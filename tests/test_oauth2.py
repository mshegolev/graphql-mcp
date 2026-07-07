"""Tests for OAuth2 client_credentials token rotation (SEC-05)."""

from __future__ import annotations

import time

import httpx
import pytest
import respx

from generic_graphql_mcp.adapters.outbound.oauth2 import OAuth2TokenManager
from generic_graphql_mcp.config import GraphQLConfig


class TestOAuth2Config:
    """Config reads OAuth2-related env vars."""

    def test_config_reads_oauth2_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("GRAPHQL_OAUTH2_TOKEN_URL", "https://auth.test/token")
        monkeypatch.setenv("GRAPHQL_OAUTH2_CLIENT_ID", "my-client")
        monkeypatch.setenv("GRAPHQL_OAUTH2_CLIENT_SECRET", "my-secret")
        monkeypatch.setenv("GRAPHQL_OAUTH2_SCOPES", "read write")
        config = GraphQLConfig()
        assert config.oauth2_token_url == "https://auth.test/token"
        assert config.oauth2_client_id == "my-client"
        assert config.oauth2_client_secret == "my-secret"
        assert config.oauth2_scopes == "read write"

    def test_oauth2_fields_default_empty(self) -> None:
        config = GraphQLConfig()
        assert config.oauth2_token_url == ""
        assert config.oauth2_client_id == ""
        assert config.oauth2_client_secret == ""
        assert config.oauth2_scopes == ""


class TestOAuth2TokenManager:
    """OAuth2TokenManager: token fetch, caching, refresh, error handling."""

    def test_fetches_token_on_first_call(self) -> None:
        """First get_token() call fetches from token endpoint."""
        with respx.mock:
            respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "tok-123",
                        "expires_in": 3600,
                        "token_type": "Bearer",
                    },
                )
            )
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="my-id",
                client_secret="my-secret",
            )
            token = mgr.get_token()
            assert token == "tok-123"
            mgr.close()

    def test_caches_token_within_expiry(self) -> None:
        """Second call returns cached token without hitting endpoint again."""
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"tok-{call_count}",
                    "expires_in": 3600,
                },
            )

        with respx.mock:
            respx.post("https://auth.test/token").mock(side_effect=side_effect)
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="id",
                client_secret="secret",
            )
            t1 = mgr.get_token()
            t2 = mgr.get_token()
            assert t1 == t2 == "tok-1"
            assert call_count == 1
            mgr.close()

    def test_refreshes_expired_token(self) -> None:
        """Token is re-fetched when expired."""
        call_count = 0

        def side_effect(request: httpx.Request) -> httpx.Response:
            nonlocal call_count
            call_count += 1
            return httpx.Response(
                200,
                json={
                    "access_token": f"tok-{call_count}",
                    "expires_in": 1,
                },
            )

        with respx.mock:
            respx.post("https://auth.test/token").mock(side_effect=side_effect)
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="id",
                client_secret="secret",
                refresh_margin_seconds=0,
            )
            t1 = mgr.get_token()
            assert t1 == "tok-1"
            # Force expiry by manipulating internal state
            mgr._token.expires_at = time.monotonic() - 1  # type: ignore[union-attr]
            t2 = mgr.get_token()
            assert t2 == "tok-2"
            assert call_count == 2
            mgr.close()

    def test_sends_client_credentials_grant(self) -> None:
        """Token request uses grant_type=client_credentials with correct params."""
        with respx.mock:
            route = respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "tok",
                        "expires_in": 3600,
                    },
                )
            )
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="cid",
                client_secret="csecret",
                scopes="read write",
            )
            mgr.get_token()
            req = route.calls[0].request
            body = req.content.decode()
            assert "grant_type=client_credentials" in body
            assert "client_id=cid" in body
            assert "client_secret=csecret" in body
            assert "scope=read+write" in body or "scope=read%20write" in body
            mgr.close()

    def test_sends_no_scope_when_empty(self) -> None:
        """When scopes is empty, no scope param is sent."""
        with respx.mock:
            route = respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "tok",
                        "expires_in": 3600,
                    },
                )
            )
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="cid",
                client_secret="csecret",
                scopes="",
            )
            mgr.get_token()
            req = route.calls[0].request
            body = req.content.decode()
            assert "scope" not in body
            mgr.close()

    def test_token_failure_raises(self) -> None:
        """When token endpoint returns error, exception propagates."""
        with respx.mock:
            respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(401, json={"error": "invalid_client"})
            )
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="bad",
                client_secret="bad",
            )
            with pytest.raises(httpx.HTTPStatusError):
                mgr.get_token()
            mgr.close()

    def test_defaults_expires_in_to_3600(self) -> None:
        """When token response omits expires_in, defaults to 3600."""
        with respx.mock:
            respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "tok-no-expiry",
                    },
                )
            )
            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="id",
                client_secret="secret",
            )
            token = mgr.get_token()
            assert token == "tok-no-expiry"
            assert mgr._token is not None
            # expires_at should be roughly now + 3600
            assert mgr._token.expires_at > time.monotonic() + 3500
            mgr.close()


class TestOAuth2TransportIntegration:
    """OAuth2 token injection into transport requests."""

    def test_oauth2_token_injected_into_request(self) -> None:
        """When oauth2 is configured, transport injects Bearer token into requests."""
        with respx.mock:
            # Mock the token endpoint
            respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "auto-tok",
                        "expires_in": 3600,
                    },
                )
            )
            # Mock the upstream GraphQL endpoint (use url__regex for trailing slash tolerance)
            upstream = respx.post(url__regex=r"https://upstream\.test/graphql/?").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "data": {"hello": "world"},
                    },
                )
            )
            from generic_graphql_mcp.adapters.outbound.http_transport import HttpTransport

            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="id",
                client_secret="secret",
            )
            transport = HttpTransport(
                endpoint="https://upstream.test/graphql",
                oauth2=mgr,
            )
            result = transport.execute("{ hello }")
            # Verify the upstream request got the OAuth2 token
            req = upstream.calls[0].request
            assert req.headers["authorization"] == "Bearer auto-tok"
            assert result.data == {"hello": "world"}
            transport.close()

    def test_oauth2_overrides_static_bearer_token(self) -> None:
        """OAuth2 token takes precedence over static bearer_token."""
        with respx.mock:
            respx.post("https://auth.test/token").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "access_token": "dynamic-tok",
                        "expires_in": 3600,
                    },
                )
            )
            upstream = respx.post(url__regex=r"https://upstream\.test/graphql/?").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "data": {"hello": "world"},
                    },
                )
            )
            from generic_graphql_mcp.adapters.outbound.http_transport import HttpTransport

            mgr = OAuth2TokenManager(
                token_url="https://auth.test/token",
                client_id="id",
                client_secret="secret",
            )
            transport = HttpTransport(
                endpoint="https://upstream.test/graphql",
                bearer_token="static-tok",
                oauth2=mgr,
            )
            transport.execute("{ hello }")
            req = upstream.calls[0].request
            # The per-request OAuth2 header should override the static one
            assert req.headers["authorization"] == "Bearer dynamic-tok"
            transport.close()


class TestOAuth2FromEnvWiring:
    """Verify from_env() wires OAuth2 when env vars are set."""

    def test_from_env_creates_oauth2_manager_when_configured(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """OAuth2 manager is created when all required env vars are set."""
        monkeypatch.setenv("GRAPHQL_ENDPOINT", "https://example.com")
        monkeypatch.setenv("GRAPHQL_OAUTH2_TOKEN_URL", "https://auth.test/token")
        monkeypatch.setenv("GRAPHQL_OAUTH2_CLIENT_ID", "my-id")
        monkeypatch.setenv("GRAPHQL_OAUTH2_CLIENT_SECRET", "my-secret")

        from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient

        client = GraphQLClient.from_env()
        assert client._transport is not None
        assert client._transport._oauth2 is not None
        client.close()

    def test_from_env_no_oauth2_without_token_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Without token_url, no OAuth2 manager is created."""
        monkeypatch.setenv("GRAPHQL_ENDPOINT", "https://example.com")
        monkeypatch.setenv("GRAPHQL_OAUTH2_CLIENT_ID", "my-id")
        monkeypatch.setenv("GRAPHQL_OAUTH2_CLIENT_SECRET", "my-secret")

        from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient

        client = GraphQLClient.from_env()
        assert client._transport is not None
        assert client._transport._oauth2 is None
        client.close()
