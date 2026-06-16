---
phase: 11-graphql-subscriptions
plan: 02
subsystem: subscriptions
tags: [sse, server-sent-events, streaming, http-fallback]
dependency_graph:
  requires: [UpstreamWSTransport, subscription-config]
  provides: [sse-subscribe-endpoint]
  affects: [rest]
tech_stack:
  added: []
  patterns: [server-sent-events, streaming-response, http-fallback]
key_files:
  created:
    - tests/test_sse_subscribe.py
  modified:
    - src/graphql_mcp/adapters/inbound/rest.py
decisions:
  - "SSE format: data: {json}\n\n per event (standard text/event-stream)"
  - "X-Accel-Buffering: no header to disable nginx proxy buffering"
  - "response_model=None to allow mixed return types (StreamingResponse|JSONResponse)"
  - "Same header forwarding pattern as WS endpoint (reuses _extract_forwarded_headers)"
metrics:
  duration: "3m"
  completed: "2026-06-16T04:21:52Z"
---

# Phase 11 Plan 02: SSE Subscription Fallback Endpoint Summary

**One-liner:** GET /graphql/subscribe SSE endpoint streaming QueryResult as text/event-stream for environments where WebSocket is unavailable.

## What Was Built

### SSE Subscription Endpoint (rest.py)
- `GET /graphql/subscribe?query=...&variables=...` returns `text/event-stream`
- Each event: `data: {"data": ..., "errors": [], "error_class": "ok"}\n\n`
- Internally creates `UpstreamWSTransport` to upstream WS, converts to SSE
- JSON validation of `variables` parameter — 400 on invalid JSON
- 503 when no subscription endpoint configured
- Auth header forwarding via `_extract_forwarded_headers` (same whitelist as REST)
- `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no` headers
- Generic error messages to client; full exceptions logged server-side only

## Tests Added

| Test File | Tests | Description |
|-----------|-------|-------------|
| `tests/test_sse_subscribe.py` | 5 | Stream events, invalid variables, no endpoint, auth forwarding, cache headers |
| **Total** | **5** | |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FastAPI response type annotation**
- **Found during:** Task 1 (SSE endpoint)
- **Issue:** FastAPI rejects `StreamingResponse | JSONResponse` as a return type annotation; raises `FastAPIError` during route registration
- **Fix:** Added `response_model=None` to `@app.get("/graphql/subscribe")` decorator
- **Files modified:** `src/graphql_mcp/adapters/inbound/rest.py`

## Self-Check: PASSED
