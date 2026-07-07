"""Custom generic_graphql_mcp.query.* OpenTelemetry metrics.

Provides a ``record_query_metrics`` function that records:
- ``generic_graphql_mcp.query.duration`` – histogram (seconds)
- ``generic_graphql_mcp.query.count`` – counter
- ``generic_graphql_mcp.query.errors`` – counter (only incremented when error_class != ok)

All instruments are no-ops when opentelemetry is not installed.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from generic_graphql_mcp.adapters.outbound.otel_bootstrap import get_meter

if TYPE_CHECKING:
    from generic_graphql_mcp.domain.models import QueryResult

_meter = get_meter("generic_graphql_mcp")

# Create instruments at module level — they are no-ops when OTEL is unavailable
_query_duration = _meter.create_histogram(
    name="generic_graphql_mcp.query.duration",
    description="Duration of GraphQL query execution in seconds",
    unit="s",
)
_query_count = _meter.create_counter(
    name="generic_graphql_mcp.query.count",
    description="Total number of GraphQL queries executed",
)
_query_errors = _meter.create_counter(
    name="generic_graphql_mcp.query.errors",
    description="Total number of GraphQL query errors by error_class",
)


def record_query_metrics(result: QueryResult, duration_s: float, operation: str = "query") -> None:
    """Record metrics for a completed query operation.

    Args:
        result: The QueryResult from the transport.
        duration_s: Wall-clock duration in seconds.
        operation: The operation name (query, raw, entities).
    """
    attrs = {"operation": operation, "error_class": result.error_class.value}
    _query_count.add(1, attrs)
    _query_duration.record(duration_s, attrs)
    if result.error_class.value != "ok":
        _query_errors.add(1, attrs)
