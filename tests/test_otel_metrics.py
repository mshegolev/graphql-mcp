"""Tests for custom graphql_mcp.query.* metrics (OTEL-03)."""

from __future__ import annotations

from typing import Any

import httpx
import respx

from graphql_mcp.adapters.inbound.async_lib import AsyncGraphQLClient
from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.adapters.outbound.async_http_transport import AsyncHttpTransport
from graphql_mcp.adapters.outbound.http_transport import HttpTransport
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import MockSchemaSource, SAMPLE_SDL


def _get_metric_value(metric_reader, metric_name: str) -> list[dict[str, Any]]:
    """Extract data points for a named metric from InMemoryMetricReader.

    Returns a list of dicts, each with ``value`` and ``attributes``.
    """
    data = metric_reader.get_metrics_data()
    results: list[dict[str, Any]] = []
    for resource_metric in data.resource_metrics:
        for scope_metric in resource_metric.scope_metrics:
            for metric in scope_metric.metrics:
                if metric.name == metric_name:
                    for dp in metric.data.data_points:
                        val = getattr(dp, "value", None)
                        if val is None:
                            # Histogram uses sum
                            val = getattr(dp, "sum", 0)
                        results.append(
                            {
                                "value": val,
                                "attributes": dict(dp.attributes) if dp.attributes else {},
                            }
                        )
    return results


def _make_sync_client(endpoint: str) -> GraphQLClient:
    """Build a GraphQLClient with a real HttpTransport for metric tests."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    transport = HttpTransport(endpoint=endpoint)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=transport, config=config)


def _make_async_client(endpoint: str) -> AsyncGraphQLClient:
    """Build an AsyncGraphQLClient with a real AsyncHttpTransport for metric tests."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    transport = AsyncHttpTransport(endpoint=endpoint)
    config = GraphQLConfig(allow_mutations=False)
    return AsyncGraphQLClient(schema_service=service, transport=transport, config=config)


class TestQueryCountMetric:
    """Verify graphql_mcp.query.count increments correctly."""

    @respx.mock
    def test_query_count_increments(self, otel_setup) -> None:
        """query() increments graphql_mcp.query.count with operation=query, error_class=ok."""
        respx.post("http://metrics.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        client = _make_sync_client("http://metrics.test/graphql")
        try:
            client.query("{ hello }")
        finally:
            client.close()

        points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.count")
        assert len(points) >= 1, f"Expected at least 1 count data point, got {points}"
        p = points[0]
        assert p["value"] == 1
        assert p["attributes"]["operation"] == "query"
        assert p["attributes"]["error_class"] == "ok"


class TestQueryDurationMetric:
    """Verify graphql_mcp.query.duration histogram records latency."""

    @respx.mock
    def test_query_duration_recorded(self, otel_setup) -> None:
        """query() records a duration > 0 in graphql_mcp.query.duration."""
        respx.post("http://metrics.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        client = _make_sync_client("http://metrics.test/graphql")
        try:
            client.query("{ hello }")
        finally:
            client.close()

        points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.duration")
        assert len(points) >= 1, f"Expected at least 1 duration data point, got {points}"
        assert points[0]["value"] > 0, "Duration should be > 0"


class TestQueryErrorsMetric:
    """Verify graphql_mcp.query.errors counter by error_class."""

    @respx.mock
    def test_query_errors_counter_by_error_class(self, otel_setup) -> None:
        """query() on HTTP 500 increments graphql_mcp.query.errors with error_class=transport."""
        respx.post("http://metrics.test/graphql/").mock(return_value=httpx.Response(500, text="Internal Server Error"))

        client = _make_sync_client("http://metrics.test/graphql")
        try:
            client.query("{ fail }")
        finally:
            client.close()

        points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.errors")
        assert len(points) >= 1, f"Expected at least 1 error data point, got {points}"
        p = points[0]
        assert p["value"] == 1
        assert p["attributes"]["error_class"] == "transport"


class TestRawOperationMetrics:
    """Verify raw() operation records metrics."""

    @respx.mock
    def test_raw_operation_records_metrics(self, otel_setup) -> None:
        """raw() records graphql_mcp.query.count with operation=raw."""
        respx.post("http://metrics.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        client = _make_sync_client("http://metrics.test/graphql")
        try:
            client.raw({"query": "{ hello }"})
        finally:
            client.close()

        points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.count")
        assert len(points) >= 1
        # Find the point with operation=raw
        raw_points = [p for p in points if p["attributes"].get("operation") == "raw"]
        assert len(raw_points) >= 1, f"No raw operation point found in {points}"
        assert raw_points[0]["value"] == 1


class TestEntitiesOperationMetrics:
    """Verify entities() operation records metrics."""

    @respx.mock
    def test_entities_operation_records_metrics(self, otel_setup) -> None:
        """entities() records graphql_mcp.query.count with operation=entities."""
        respx.post("http://metrics.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"_entities": [{"__typename": "User"}]}})
        )

        client = _make_sync_client("http://metrics.test/graphql")
        try:
            client.entities([{"__typename": "User", "id": "1"}])
        finally:
            client.close()

        points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.count")
        assert len(points) >= 1
        entities_points = [p for p in points if p["attributes"].get("operation") == "entities"]
        assert len(entities_points) >= 1, f"No entities operation point found in {points}"
        assert entities_points[0]["value"] == 1


class TestAsyncQueryMetrics:
    """Verify async client records metrics identically."""

    @respx.mock
    async def test_async_query_records_metrics(self, otel_setup) -> None:
        """async query() records graphql_mcp.query.count with operation=query."""
        respx.post("http://metrics.test/graphql/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}})
        )

        client = _make_async_client("http://metrics.test/graphql")
        try:
            await client.query("{ hello }")
        finally:
            await client.close()

        points = _get_metric_value(otel_setup["metric_reader"], "graphql_mcp.query.count")
        assert len(points) >= 1, f"Expected at least 1 count data point, got {points}"
        query_points = [p for p in points if p["attributes"].get("operation") == "query"]
        assert len(query_points) >= 1
        assert query_points[0]["value"] == 1
        assert query_points[0]["attributes"]["error_class"] == "ok"
