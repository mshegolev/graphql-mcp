"""Tests for outbound httpx span attributes and W3C traceparent propagation (OTEL-01)."""

from __future__ import annotations

import re

import httpx
import respx

from generic_graphql_mcp.adapters.outbound.async_http_transport import AsyncHttpTransport
from generic_graphql_mcp.adapters.outbound.http_transport import HttpTransport


class TestOutboundHttpSpans:
    """Verify auto-instrumented httpx spans contain expected attributes."""

    @respx.mock
    def test_outbound_http_span_attributes(self, otel_setup) -> None:
        """Sync HttpTransport produces span with http.method and http.url."""
        respx.post("http://test.example/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        transport = HttpTransport(endpoint="http://test.example/graphql")
        try:
            transport.execute("{ hello }")
        finally:
            transport.close()

        spans = otel_setup["span_exporter"].get_finished_spans()
        assert len(spans) >= 1, f"Expected at least 1 span, got {len(spans)}"

        # Find the HTTP span
        http_span = spans[0]
        attrs = dict(http_span.attributes or {})

        # opentelemetry-instrumentation-httpx uses http.request.method (semconv v1.21+)
        # or http.method (older semconv). Accept either.
        method = attrs.get("http.request.method") or attrs.get("http.method")
        assert method == "POST", f"Expected POST, got {method}. Attrs: {attrs}"

        url = attrs.get("url.full") or attrs.get("http.url") or str(attrs)
        assert "test.example" in str(url), f"Expected test.example in URL attrs: {attrs}"

    @respx.mock
    async def test_outbound_async_http_span_attributes(self, otel_setup) -> None:
        """Async AsyncHttpTransport produces span with http.method and http.url."""
        respx.post("http://test.example/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        transport = AsyncHttpTransport(endpoint="http://test.example/graphql")
        try:
            await transport.execute("{ hello }")
        finally:
            await transport.close()

        spans = otel_setup["span_exporter"].get_finished_spans()
        assert len(spans) >= 1, f"Expected at least 1 span, got {len(spans)}"

        http_span = spans[0]
        attrs = dict(http_span.attributes or {})

        method = attrs.get("http.request.method") or attrs.get("http.method")
        assert method == "POST", f"Expected POST, got {method}. Attrs: {attrs}"

        url = attrs.get("url.full") or attrs.get("http.url") or str(attrs)
        assert "test.example" in str(url), f"Expected test.example in URL attrs: {attrs}"

    @respx.mock
    def test_traceparent_propagated(self, otel_setup) -> None:
        """W3C traceparent header is injected on outbound requests."""
        captured_headers: dict[str, str] = {}

        def _capture(request: httpx.Request) -> httpx.Response:
            captured_headers.update(dict(request.headers))
            return httpx.Response(200, json={"data": {"ok": True}})

        respx.post("http://test.example/graphql/").mock(side_effect=_capture)

        transport = HttpTransport(endpoint="http://test.example/graphql")
        try:
            transport.execute("{ ok }")
        finally:
            transport.close()

        assert "traceparent" in captured_headers, f"traceparent not found in headers: {list(captured_headers.keys())}"
        # W3C traceparent format: version-trace_id-parent_id-trace_flags
        tp = captured_headers["traceparent"]
        assert re.match(r"^\d{2}-[0-9a-f]{32}-[0-9a-f]{16}-\d{2}$", tp), f"traceparent format invalid: {tp}"
