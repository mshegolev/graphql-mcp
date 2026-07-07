"""Structured audit logging for generic-graphql-mcp operations.

When ``GRAPHQL_AUDIT_LOG=true``, every query/raw/entities operation emits
a structured log record via Python's ``logging`` module at INFO level.

The audit record includes:
- ``caller_ip`` — client IP (from REST request, or "local" for lib facade)
- ``caller_identity`` — X-User-Id header value or "anonymous"
- ``operation`` — query / raw / entities
- ``query_hash`` — SHA-256 of the query string (first 16 hex chars)
- ``error_class`` — ok / graphql / transport
- ``latency_ms`` — operation duration in milliseconds (rounded to 2 decimal places)
- ``trace_id`` — OTEL trace ID if available, else "none"

Integrates with Phase 9 OTEL: when a traced request is active, ``trace_id``
is extracted from the current span context. When OTEL ``LoggingInstrumentor``
is active, the log record also gets ``otelTraceID`` and ``otelSpanID`` fields
automatically.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger("generic_graphql_mcp.audit")


def _get_trace_id() -> str:
    """Extract trace_id from current OTEL span, or return 'none'."""
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            return format(ctx.trace_id, "032x")
    except ImportError:
        pass
    except Exception:
        pass
    return "none"


def _query_hash(query_str: str) -> str:
    """Return first 16 hex chars of SHA-256 hash of the query string."""
    return hashlib.sha256(query_str.encode("utf-8")).hexdigest()[:16]


def emit_audit_log(
    *,
    operation: str,
    query_str: str,
    error_class: str,
    latency_s: float,
    caller_ip: str = "local",
    caller_identity: str = "anonymous",
) -> None:
    """Emit a structured audit log record.

    This function is a no-op when audit logging is disabled — the caller
    is responsible for checking ``config.audit_log`` before calling.
    This keeps the function pure (no config dependency) and testable.
    """
    trace_id = _get_trace_id()
    record: dict[str, Any] = {
        "event": "graphql_audit",
        "caller_ip": caller_ip,
        "caller_identity": caller_identity,
        "operation": operation,
        "query_hash": _query_hash(query_str),
        "error_class": error_class,
        "latency_ms": round(latency_s * 1000, 2),
        "trace_id": trace_id,
    }
    logger.info("audit: %s", record, extra=record)
