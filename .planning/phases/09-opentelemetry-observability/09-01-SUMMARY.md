---
phase: 09-opentelemetry-observability
plan: 01
subsystem: observability
tags: [otel, tracing, metrics, httpx, instrumentation]
dependency_graph:
  requires: []
  provides: [otel-bootstrap, outbound-tracing, query-metrics]
  affects: [lib-facades, async-lib-facades, pyproject-extras]
tech_stack:
  added: [opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-http, opentelemetry-instrumentation-httpx, opentelemetry-instrumentation-fastapi, opentelemetry-instrumentation-logging]
  patterns: [opt-in-extra, graceful-no-op, module-level-instruments, bounded-cardinality-labels]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/otel_bootstrap.py
    - src/graphql_mcp/adapters/outbound/otel_metrics.py
    - tests/test_otel_outbound.py
    - tests/test_otel_metrics.py
    - tests/test_otel_bootstrap.py
  modified:
    - pyproject.toml
    - src/graphql_mcp/adapters/inbound/lib.py
    - src/graphql_mcp/adapters/inbound/async_lib.py
    - tests/conftest.py
decisions:
  - "OTEL is opt-in via [otel] extra — zero-cost when not installed"
  - "Module-level metric instruments (no-op when OTEL absent) avoid per-call import checks"
  - "Global httpx auto-instrumentation via HTTPXClientInstrumentor — no transport constructor changes needed"
  - "Provider reset helpers in conftest.py allow each test to get a clean OTEL state"
metrics:
  duration: "~10 minutes"
  completed: "2026-06-16T03:07:13Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 15
  tests_total: 236
---

# Phase 09 Plan 01: OTEL bootstrap, outbound tracing, custom query metrics Summary

**One-liner:** OpenTelemetry opt-in foundation with env-driven TracerProvider/MeterProvider bootstrap, auto-instrumented httpx outbound spans with W3C traceparent propagation, and custom `graphql_mcp.query.{duration,count,errors}` metrics recorded in both sync and async lib facades.

## What Was Built

### 1. OTEL Bootstrap Module (`otel_bootstrap.py`)

- `init_otel()` — idempotent initialization that reads `OTEL_SERVICE_NAME` and `OTEL_EXPORTER_OTLP_ENDPOINT` from environment, configures `TracerProvider` + `MeterProvider` with OTLP/HTTP exporters, and auto-instruments httpx clients globally and logging.
- `get_tracer(name)` / `get_meter(name)` — factory functions that return real OTEL objects when SDK is installed or local no-op implementations when absent.
- `is_otel_available()` — boolean flag for conditional logic.
- Graceful no-op: When `opentelemetry` packages are not installed, all functions return immediately or provide no-op fallbacks. Zero import errors, zero runtime cost.

### 2. pyproject.toml `[otel]` Extra

Added 6 opentelemetry packages as an opt-in extra:
- `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`
- `opentelemetry-instrumentation-httpx`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-logging`

Updated `all` extra to include `otel`. Added `graphql-mcp[otel]` to `dev` extra for test availability.

### 3. Outbound HTTP Span Auto-Instrumentation

`HTTPXClientInstrumentor().instrument()` (called by `init_otel()`) patches `httpx.Client` and `httpx.AsyncClient` globally. Every outbound GraphQL call automatically gets:
- A span with `http.request.method` and `url.full` attributes
- W3C `traceparent` header injected for distributed trace propagation

No changes needed in `HttpTransport` or `AsyncHttpTransport` constructors — the instrumentation works at the httpx class level.

### 4. Custom Query Metrics (`otel_metrics.py`)

Module-level metric instruments:
- `graphql_mcp.query.duration` — histogram (seconds), records wall-clock latency per operation
- `graphql_mcp.query.count` — counter, increments for every query/raw/entities call
- `graphql_mcp.query.errors` — counter, increments only when `error_class != ok`

All instruments use bounded-cardinality labels: `operation` (3 values: query/raw/entities) and `error_class` (3 values: ok/graphql/transport) — per threat model T-09-03 mitigation.

### 5. Lib Facade Instrumentation

Both `GraphQLClient` and `AsyncGraphQLClient` now wrap their `query()`, `raw()`, and `entities()` methods with `time.monotonic()` timing and `record_query_metrics()` calls. Metrics are recorded after every transport call, regardless of success or failure.

### 6. Test Infrastructure

- `otel_setup` fixture in `conftest.py`: Sets up in-memory span exporter + metric reader, instruments httpx, yields test context, tears down and resets global OTEL state after each test.
- Provider reset helpers (`_reset_trace_provider`, `_reset_meter_provider`) ensure test isolation by resetting the OTEL API's `Once` guards and global provider references.

## Test Results

```
tests/test_otel_outbound.py — 3 passed (span attrs sync, span attrs async, traceparent)
tests/test_otel_metrics.py  — 6 passed (count, duration, errors, raw, entities, async)
tests/test_otel_bootstrap.py — 6 passed (endpoint config, no-packages no-op, idempotent, available, tracer, meter)
Full suite: 236 passed in 1.41s
Domain purity: PASSED (no opentelemetry imports in domain/ or ports/)
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] InMemorySpanExporter import path**
- **Found during:** Task 1 (conftest fixture creation)
- **Issue:** Plan specified `from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter` but the actual module path in v1.27 is `opentelemetry.sdk.trace.export.in_memory_span_exporter`
- **Fix:** Used correct import path `from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter`
- **Files modified:** tests/conftest.py

**2. [Rule 1 - Bug] respx URL matching with trailing slash**
- **Found during:** Task 1 (test execution)
- **Issue:** `httpx.Client(base_url="http://test.example/graphql")` sends requests to `http://test.example/graphql/` (with trailing slash), but respx mocks were registered without trailing slash, causing `AllMockedAssertionError`
- **Fix:** Added trailing slash to all respx mock URLs (matching existing project pattern in test_async_http_transport.py)
- **Files modified:** tests/test_otel_outbound.py, tests/test_otel_metrics.py

**3. [Rule 1 - Bug] OTEL global provider state leaking between tests**
- **Found during:** Task 1 (test execution)
- **Issue:** OTEL API's `set_tracer_provider()` and `set_meter_provider()` can only be called once per process — subsequent calls log a warning and are ignored, causing test isolation failures
- **Fix:** Added `_reset_trace_provider()` and `_reset_meter_provider()` helpers that reset the internal `Once` guards and global provider references before/after each test
- **Files modified:** tests/conftest.py

## Decisions Made

1. **OTEL is opt-in** — Added as `[otel]` extra, not a hard dependency. Zero cost when not installed.
2. **Global httpx instrumentation** — Used `HTTPXClientInstrumentor().instrument()` for global class-level patching rather than per-instance wrapping. Simpler, covers all transports automatically.
3. **Module-level metric instruments** — Created counters/histograms at module import time. They're no-ops when OTEL is absent, avoiding per-call overhead.
4. **Bounded cardinality** — Only `operation` (3 values) and `error_class` (3 values) as label dimensions — 9 max combinations per metric. No user-controlled values.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1+2 | `e176413` | feat(09-01): OTEL bootstrap, outbound tracing, custom query metrics |

## Self-Check: PASSED
