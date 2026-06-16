# Phase 9: OpenTelemetry Observability - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Every operation through every face is traced, metered, and log-correlated — a developer can follow a single request from REST/MCP inbound through to upstream GraphQL HTTP call in Jaeger, see query metrics in Prometheus, and correlate structured logs by trace ID.

Requirements: OTEL-01 (distributed tracing + W3C traceparent), OTEL-02 (FastAPI server spans + HTTP metrics), OTEL-03 (custom graphql_mcp.query.* metrics by error_class), OTEL-04 (log correlation with trace_id/span_id), OTEL-05 (OTLP env var config).

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Key architectural guidelines:

- OTEL goes in adapters layer only — domain/ and ports/ must remain I/O-free (enforced by test_domain_purity.py)
- Use official opentelemetry-instrumentation-* libraries where available (httpx, fastapi, logging)
- Custom metrics (graphql_mcp.query.*) go in the client facade layer (lib.py / async_lib.py) where error_class is known
- Configuration via standard OTEL_* env vars — no custom config fields needed
- OTEL dependencies as optional `[otel]` extra in pyproject.toml — OTEL is opt-in
- Graceful no-op when OTEL packages not installed (import guards)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `httpx.Client` / `httpx.AsyncClient` in transport — `opentelemetry-instrumentation-httpx` auto-instruments these
- `FastAPI` app in `rest.py` — `opentelemetry-instrumentation-fastapi` auto-instruments it
- Standard `logging.getLogger(__name__)` across 10 modules — `opentelemetry-instrumentation-logging` patches LogRecord
- `config.py` with pydantic-settings for env var config
- `conftest.py` with `MockSchemaSource`, `respx` for HTTP mocking

### Established Patterns
- Hexagonal architecture: domain/ has zero I/O imports
- Behavioral parity between sync/async clients
- Optional dependencies via extras (server, mcp, cli, dev)
- Tests use respx for HTTP mocking, FastAPI TestClient for endpoint testing

### Integration Points
- `http_transport.py:post_raw()` — outbound HTTP choke point for span creation
- `async_http_transport.py:post_raw()` — async counterpart
- `rest.py` app creation — FastAPI instrumentation hook
- `lib.py:query()/raw()/entities()` — custom metrics recording point
- `async_lib.py:query()/raw()/entities()` — async metrics recording point

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase, discuss skipped.

</deferred>
