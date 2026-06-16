"""Tests for inbound FastAPI server spans and HTTP metrics (OTEL-02)."""

from __future__ import annotations

from typing import Any

import httpx
import respx
from fastapi.testclient import TestClient

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.adapters.inbound.rest import app, set_client
from graphql_mcp.adapters.outbound.http_transport import HttpTransport
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _get_metric_value(metric_reader, metric_name: str) -> list[dict[str, Any]]:
    """Extract data points for a named metric from InMemoryMetricReader."""
    data = metric_reader.get_metrics_data()
    results: list[dict[str, Any]] = []
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == metric_name:
                    for dp in metric.data.data_points:
                        val = getattr(dp, "value", None)
                        if val is None:
                            val = getattr(dp, "sum", 0)
                        results.append(
                            {
                                "value": val,
                                "attributes": dict(dp.attributes) if dp.attributes else {},
                            }
                        )
    return results


def _find_metrics_by_substring(metric_reader, substring: str) -> list[str]:
    """Find all metric names containing a substring."""
    data = metric_reader.get_metrics_data()
    names: list[str] = []
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if substring in metric.name:
                    names.append(metric.name)
    return names


def _setup_test_client_with_transport(endpoint: str) -> TestClient:
    """Create a TestClient with a GraphQLClient backed by HttpTransport."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    transport = HttpTransport(endpoint=endpoint)
    config = GraphQLConfig(allow_mutations=False)
    client = GraphQLClient(schema_service=service, transport=transport, config=config)
    set_client(client)
    return TestClient(app)


class TestFastAPIServerSpans:
    """Verify that inbound FastAPI requests produce SERVER spans."""

    @respx.mock
    def test_fastapi_server_span_on_query(self, otel_setup) -> None:
        """POST /graphql/query produces a SERVER span with HTTP attributes."""
        from opentelemetry.trace import SpanKind

        respx.post("http://inbound.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        tc = _setup_test_client_with_transport("http://inbound.test/graphql")
        try:
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            assert resp.status_code == 200
        finally:
            set_client(None)

        spans = otel_setup["span_exporter"].get_finished_spans()
        assert len(spans) >= 1, f"Expected at least 1 span, got {len(spans)}"

        # Find the SERVER span (from FastAPI instrumentation)
        server_spans = [s for s in spans if s.kind == SpanKind.SERVER]
        assert len(server_spans) >= 1, (
            f"Expected at least 1 SERVER span, got {len(server_spans)}. All spans: {[(s.name, s.kind) for s in spans]}"
        )

        server_span = server_spans[0]
        attrs = dict(server_span.attributes or {})

        # Check HTTP method (semconv v1.21+ uses http.request.method, older uses http.method)
        method = attrs.get("http.request.method") or attrs.get("http.method")
        assert method == "POST", f"Expected POST, got {method}. Attrs: {attrs}"

        # Check route is present somewhere in attributes
        route_found = any("/graphql/query" in str(v) for v in attrs.values()) or "/graphql/query" in server_span.name
        assert route_found, f"Expected /graphql/query in span attrs or name. Attrs: {attrs}, Name: {server_span.name}"


class TestFastAPIHTTPMetrics:
    """Verify that inbound HTTP metrics are emitted."""

    @respx.mock
    def test_fastapi_http_server_duration_metric(self, otel_setup) -> None:
        """POST /graphql/query records an http.server.duration (or similar) metric."""
        respx.post("http://inbound.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        tc = _setup_test_client_with_transport("http://inbound.test/graphql")
        try:
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            assert resp.status_code == 200
        finally:
            set_client(None)

        # FastAPI instrumentor may use different metric names depending on semconv version:
        # - http.server.duration (semconv < 1.21)
        # - http.server.request.duration (semconv >= 1.21)
        duration_metrics = _find_metrics_by_substring(otel_setup["metric_reader"], "duration")
        http_duration_metrics = [m for m in duration_metrics if "server" in m.lower() or "http" in m.lower()]
        assert len(http_duration_metrics) >= 1, f"Expected an HTTP server duration metric, found: {duration_metrics}"

    @respx.mock
    def test_fastapi_http_server_metrics_registered(self, otel_setup) -> None:
        """POST /graphql/query registers HTTP server metrics (duration or active_requests).

        The FastAPI/ASGI instrumentor version determines which metrics are emitted.
        Older semconv: http.server.duration + http.server.active_requests.
        Newer semconv (v0.48b0+): http.server.request.duration only.
        We check that at least one HTTP-related metric is registered.
        """
        respx.post("http://inbound.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        tc = _setup_test_client_with_transport("http://inbound.test/graphql")
        try:
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            assert resp.status_code == 200
        finally:
            set_client(None)

        # Collect all metric names
        all_metrics = _find_metrics_by_substring(otel_setup["metric_reader"], "")
        # Accept either active_requests OR duration (or both) as proof of HTTP instrumentation
        http_metrics = [m for m in all_metrics if "active" in m.lower() or "duration" in m.lower()]
        assert len(http_metrics) >= 1, (
            f"Expected at least one HTTP metric (duration or active_requests). All metrics: {all_metrics}"
        )


class TestNoOTELFallback:
    """Verify app works when OTEL is not fully initialized."""

    def test_no_otel_app_still_works(self) -> None:
        """Without otel_setup fixture, /health still returns 200."""
        tc = TestClient(app)
        resp = tc.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
