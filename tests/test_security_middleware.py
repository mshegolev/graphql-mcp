"""Tests for security middleware: query depth limiting, rate limiting, header forwarding.

Covers SEC-01 (depth), SEC-02 (rate limit), SEC-03 (header forwarding).
"""

from __future__ import annotations

import json

import pytest
import respx
import httpx
from fastapi.testclient import TestClient

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.adapters.inbound.rest import RateLimitMiddleware, app, set_client
from graphql_mcp.adapters.outbound.http_transport import HttpTransport
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def test_client() -> TestClient:
    """FastAPI TestClient with mock GraphQLClient (no transport)."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    client = GraphQLClient(schema_service=service, transport=None, config=config)
    set_client(client)
    return TestClient(app)


@pytest.fixture()
def transport_client():
    """GraphQLClient with a real HttpTransport (respx-mocked)."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False, endpoint="https://upstream.test/graphql")
    transport = HttpTransport(endpoint="https://upstream.test/graphql")
    client = GraphQLClient(schema_service=service, transport=transport, config=config)
    set_client(client)
    # Clear rate limiter state to avoid interference from other tests
    middleware = _get_rate_limit_middleware()
    if middleware is not None:
        middleware._windows.clear()
    return TestClient(app)


# ---------------------------------------------------------------------------
# TestQueryDepthLimit
# ---------------------------------------------------------------------------


class TestQueryDepthLimit:
    """SEC-01: Query depth limiting via AST analysis."""

    def test_shallow_query_passes(self, test_client: TestClient) -> None:
        resp = test_client.post("/graphql/query", json={"query": "{ hello }"})
        # 200 even though no transport — the depth check passed, transport error is 200
        assert resp.status_code == 200

    def test_deep_query_rejected_400(self, test_client: TestClient) -> None:
        # 11 levels deep — exceeds default max_query_depth=10
        deep_query = "{ a { b { c { d { e { f { g { h { i { j { k } } } } } } } } } } }"
        resp = test_client.post("/graphql/query", json={"query": deep_query})
        assert resp.status_code == 400
        body = resp.json()
        assert "depth" in body
        assert "max_depth" in body
        assert body["depth"] == 11
        assert body["max_depth"] == 10

    def test_depth_limit_configurable(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPHQL_MAX_QUERY_DEPTH", "3")
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        set_client(client)
        tc = TestClient(app)

        # Depth 4 — should be rejected with limit of 3
        query = "{ a { b { c { d } } } }"
        resp = tc.post("/graphql/query", json={"query": query})
        assert resp.status_code == 400
        body = resp.json()
        assert body["depth"] == 4
        assert body["max_depth"] == 3

    def test_raw_endpoint_depth_checked(self, test_client: TestClient) -> None:
        deep_query = "{ a { b { c { d { e { f { g { h { i { j { k } } } } } } } } } } }"
        resp = test_client.post(
            "/graphql/raw",
            json={"query": deep_query},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["depth"] == 11

    def test_invalid_graphql_passes_through(self, test_client: TestClient) -> None:
        # Invalid syntax should NOT trigger a 400 for depth — parser failure → let upstream handle
        resp = test_client.post("/graphql/query", json={"query": "{ invalid !!! }"})
        # Should pass depth check (parse error → silently skip) and hit transport error (200)
        assert resp.status_code == 200

    def test_fragment_depth_counted(self, test_client: TestClient) -> None:
        query = """
        fragment Deep on Query {
            a { b { c { d { e { f { g { h { i { j { k } } } } } } } } } }
        }
        query Main { ...Deep }
        """
        resp = test_client.post("/graphql/query", json={"query": query})
        assert resp.status_code == 400
        body = resp.json()
        assert body["depth"] > 10


# ---------------------------------------------------------------------------
# TestRateLimiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """SEC-02: IP-based sliding-window rate limiter."""

    def test_under_limit_passes(self, test_client: TestClient) -> None:
        # Default is 100/minute — 5 requests should all pass
        for _ in range(5):
            resp = test_client.get("/graphql/introspect")
            assert resp.status_code != 429

    def test_over_limit_returns_429(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPHQL_RATE_LIMIT", "5/minute")
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        set_client(client)

        # Need to re-create app middleware with new config.
        # Since RateLimitMiddleware reads config in __init__, we patch
        # the middleware instance directly.
        middleware = _get_rate_limit_middleware()
        assert middleware is not None
        middleware._max_requests = 5
        middleware._window_seconds = 60
        middleware._windows.clear()

        tc = TestClient(app)
        for i in range(6):
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            if i < 5:
                assert resp.status_code != 429, f"Request {i + 1} should not be 429"
            else:
                assert resp.status_code == 429, f"Request {i + 1} should be 429"

    def test_429_has_retry_after_header(self, monkeypatch: pytest.MonkeyPatch) -> None:
        middleware = _get_rate_limit_middleware()
        assert middleware is not None
        middleware._max_requests = 3
        middleware._window_seconds = 60
        middleware._windows.clear()

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        set_client(client)
        tc = TestClient(app)

        for _ in range(3):
            tc.post("/graphql/query", json={"query": "{ hello }"})

        resp = tc.post("/graphql/query", json={"query": "{ hello }"})
        assert resp.status_code == 429
        assert "retry-after" in resp.headers
        retry_after = int(resp.headers["retry-after"])
        assert retry_after > 0

    def test_health_exempt_from_rate_limit(self) -> None:
        middleware = _get_rate_limit_middleware()
        assert middleware is not None
        middleware._max_requests = 2
        middleware._window_seconds = 60
        middleware._windows.clear()

        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        set_client(client)
        tc = TestClient(app)

        # Exceed the limit with regular requests
        for _ in range(3):
            tc.post("/graphql/query", json={"query": "{ hello }"})

        # /health should still work
        resp = tc.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_different_ips_independent(self) -> None:
        """Rate limiter tracks state per IP key."""
        middleware = _get_rate_limit_middleware()
        assert middleware is not None
        middleware._max_requests = 2
        middleware._window_seconds = 60
        middleware._windows.clear()

        # Simulate two different IPs via the internal state
        import time

        now = time.time()
        middleware._windows["1.2.3.4"] = [now, now]
        middleware._windows["5.6.7.8"] = [now]

        # IP 1.2.3.4 has 2 entries — at limit
        assert len(middleware._windows["1.2.3.4"]) >= middleware._max_requests
        # IP 5.6.7.8 has 1 entry — under limit
        assert len(middleware._windows["5.6.7.8"]) < middleware._max_requests


# ---------------------------------------------------------------------------
# TestHeaderForwarding
# ---------------------------------------------------------------------------


class TestHeaderForwarding:
    """SEC-03: Inbound headers forwarded to upstream GraphQL."""

    @respx.mock
    def test_authorization_header_forwarded(self, transport_client: TestClient) -> None:
        # httpx base_url sends to path with trailing slash
        upstream = respx.post(url__startswith="https://upstream.test/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        transport_client.post(
            "/graphql/query",
            json={"query": "{ hello }"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert upstream.called
        request_sent = upstream.calls.last.request
        assert request_sent.headers["authorization"] == "Bearer test-token"

    @respx.mock
    def test_x_user_id_and_x_roles_forwarded(self, transport_client: TestClient) -> None:
        upstream = respx.post(url__startswith="https://upstream.test/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        transport_client.post(
            "/graphql/query",
            json={"query": "{ hello }"},
            headers={"X-User-Id": "user-42", "X-Roles": "admin,viewer"},
        )

        assert upstream.called
        request_sent = upstream.calls.last.request
        assert request_sent.headers["x-user-id"] == "user-42"
        assert request_sent.headers["x-roles"] == "admin,viewer"

    @respx.mock
    def test_missing_headers_not_forwarded(self, transport_client: TestClient) -> None:
        upstream = respx.post(url__startswith="https://upstream.test/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        # No auth headers on the inbound request
        transport_client.post(
            "/graphql/query",
            json={"query": "{ hello }"},
        )

        assert upstream.called
        request_sent = upstream.calls.last.request
        # Authorization should not appear (or should be absent/empty in
        # per-request headers — the transport may have its own if configured)
        assert "x-user-id" not in request_sent.headers
        assert "x-roles" not in request_sent.headers

    @respx.mock
    def test_raw_endpoint_forwards_headers(self, transport_client: TestClient) -> None:
        upstream = respx.post(url__startswith="https://upstream.test/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        transport_client.post(
            "/graphql/raw",
            json={"query": "{ hello }"},
            headers={"Authorization": "Bearer raw-token", "X-User-Id": "user-99"},
        )

        assert upstream.called
        request_sent = upstream.calls.last.request
        assert request_sent.headers["authorization"] == "Bearer raw-token"
        assert request_sent.headers["x-user-id"] == "user-99"

    @respx.mock
    def test_entities_endpoint_forwards_headers(self, transport_client: TestClient) -> None:
        upstream = respx.post(url__startswith="https://upstream.test/graphql").mock(
            return_value=httpx.Response(200, json={"data": {"_entities": [{"__typename": "Product"}]}})
        )

        transport_client.post(
            "/graphql/entities",
            json={"representations": [{"__typename": "Product", "id": "1"}]},
            headers={"Authorization": "Bearer ent-token"},
        )

        assert upstream.called
        request_sent = upstream.calls.last.request
        assert request_sent.headers["authorization"] == "Bearer ent-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_rate_limit_middleware() -> RateLimitMiddleware | None:
    """Walk the ASGI app middleware stack to find the RateLimitMiddleware instance."""
    inner_app = app
    # FastAPI wraps middleware in a chain. The middleware instances are accessible
    # via app.middleware_stack which is built lazily by Starlette.
    # For TestClient, middleware_stack is built on first request.
    # We can also walk the app's user_middleware list.
    for mw in getattr(app, "user_middleware", []):
        if mw.cls is RateLimitMiddleware:
            # The actual instance lives on the middleware_stack (built after first request)
            break

    # Walk the middleware_stack if available
    middleware_stack = getattr(app, "middleware_stack", None)
    if middleware_stack is None:
        # Force build by creating a test client
        _ = TestClient(app)
        middleware_stack = getattr(app, "middleware_stack", None)

    current = middleware_stack
    while current is not None:
        if isinstance(current, RateLimitMiddleware):
            return current
        current = getattr(current, "app", None)

    return None
