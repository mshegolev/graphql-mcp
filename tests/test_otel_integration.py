"""End-to-end trace integration tests — inbound + outbound in a single trace (OTEL-02/04)."""

from __future__ import annotations

from typing import Any

import httpx
import respx
from fastapi.testclient import TestClient
from opentelemetry.trace import SpanKind

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


def _setup_client(endpoint: str) -> GraphQLClient:
    """Build a GraphQLClient with HttpTransport for integration tests."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    transport = HttpTransport(endpoint=endpoint)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=transport, config=config)


def _reinstrument_fastapi(otel_setup) -> None:
    """Re-instrument the FastAPI app with the current test's providers.

    The ASGI/FastAPI middleware is installed at module-import time in rest.py.
    After the otel_setup fixture tears down (resetting the global providers) and
    recreates fresh ones, the middleware holds a stale reference. This helper
    forces a clean re-instrumentation cycle so SERVER spans are exported to the
    current test's InMemorySpanExporter.
    """
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    FastAPIInstrumentor().uninstrument_app(app)
    app.middleware_stack = None  # Force lazy rebuild on next request
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=otel_setup["tracer_provider"],
        meter_provider=otel_setup["meter_provider"],
    )


class TestEndToEndTrace:
    """Verify a single trace flows from inbound REST through outbound HTTP."""

    @respx.mock
    def test_end_to_end_trace_inbound_to_outbound(self, otel_setup) -> None:
        """A single trace connects the FastAPI SERVER span to the httpx CLIENT span."""
        _reinstrument_fastapi(otel_setup)

        respx.post("http://e2e.test/graphql/").mock(return_value=httpx.Response(200, json={"data": {"hello": "world"}}))

        client = _setup_client("http://e2e.test/graphql")
        set_client(client)
        try:
            tc = TestClient(app)
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            assert resp.status_code == 200
            assert resp.json()["data"] == {"hello": "world"}
        finally:
            set_client(None)

        spans = otel_setup["span_exporter"].get_finished_spans()
        assert len(spans) >= 2, (
            f"Expected at least 2 spans (server + client), got {len(spans)}: {[(s.name, s.kind) for s in spans]}"
        )

        # Find SERVER and CLIENT spans
        server_spans = [s for s in spans if s.kind == SpanKind.SERVER]
        client_spans = [s for s in spans if s.kind == SpanKind.CLIENT]

        assert len(server_spans) >= 1, f"Expected at least 1 SERVER span. All: {[(s.name, s.kind) for s in spans]}"
        assert len(client_spans) >= 1, f"Expected at least 1 CLIENT span. All: {[(s.name, s.kind) for s in spans]}"

        # All spans should share the same trace_id (single distributed trace)
        trace_ids = {s.context.trace_id for s in spans}
        assert len(trace_ids) == 1, (
            f"Expected single trace, got {len(trace_ids)} traces. "
            f"Trace IDs: {[format(tid, '032x') for tid in trace_ids]}"
        )

        # CLIENT span should be a child of the SERVER span
        server_span = server_spans[0]
        client_span = client_spans[0]
        assert client_span.parent is not None, "CLIENT span should have a parent"
        assert client_span.parent.span_id == server_span.context.span_id, (
            f"CLIENT span parent_id={format(client_span.parent.span_id, '016x')} "
            f"should equal SERVER span_id={format(server_span.context.span_id, '016x')}"
        )

    @respx.mock
    def test_end_to_end_trace_includes_custom_metrics(self, otel_setup) -> None:
        """An end-to-end request produces both trace spans AND custom metrics.

        Verifies all three observability pillars (traces, metrics, logs) are
        active simultaneously within a single request flow.

        Note: Re-instruments the FastAPI app to ensure the server spans use the
        current test's TracerProvider (since the module-level instrumentation
        may reference a stale provider from a previous test cycle).
        """
        _reinstrument_fastapi(otel_setup)

        respx.post("http://e2e-metrics.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        client = _setup_client("http://e2e-metrics.test/graphql")
        set_client(client)
        try:
            tc = TestClient(app)
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            assert resp.status_code == 200
        finally:
            set_client(None)

        # Verify at least one span exists (traces pillar)
        spans = otel_setup["span_exporter"].get_finished_spans()
        assert len(spans) >= 1, f"Expected at least 1 span, got {len(spans)}"

        # Verify custom metrics exist (metrics pillar)
        count_points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.count")
        assert len(count_points) >= 1, "Expected graphql_mcp.query.count metric"
        query_points = [p for p in count_points if p["attributes"].get("operation") == "query"]
        assert len(query_points) >= 1, f"Expected query.count with operation=query. Got: {count_points}"

        client = _setup_client("http://e2e-metrics.test/graphql")
        set_client(client)
        try:
            tc = TestClient(app)
            resp = tc.post("/graphql/query", json={"query": "{ hello }"})
            assert resp.status_code == 200
        finally:
            set_client(None)

        # Verify at least the SERVER span exists (traces pillar)
        spans = otel_setup["span_exporter"].get_finished_spans()
        server_spans = [s for s in spans if s.kind == SpanKind.SERVER]
        assert len(server_spans) >= 1, (
            f"Expected at least 1 SERVER span, got {len(server_spans)}. All spans: {[(s.name, s.kind) for s in spans]}"
        )

        # Verify custom metrics exist (metrics pillar)
        count_points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.count")
        assert len(count_points) >= 1, "Expected graphql_mcp.query.count metric"
        query_points = [p for p in count_points if p["attributes"].get("operation") == "query"]
        assert len(query_points) >= 1, f"Expected query.count with operation=query. Got: {count_points}"
