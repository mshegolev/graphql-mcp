---
phase: 11-graphql-subscriptions
plan: 01
subsystem: subscriptions
tags: [websocket, graphql-transport-ws, async-iterator, real-time]
dependency_graph:
  requires: []
  provides: [UpstreamWSTransport, subscribe-method, ws-endpoint, subscription-config]
  affects: [async_lib, rest, config, pyproject]
tech_stack:
  added: [websockets]
  patterns: [graphql-transport-ws, async-iterator, bounded-queue-backpressure]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/ws_transport.py
    - tests/test_ws_transport.py
    - tests/test_subscribe.py
  modified:
    - pyproject.toml
    - src/graphql_mcp/config.py
    - src/graphql_mcp/adapters/inbound/async_lib.py
    - src/graphql_mcp/adapters/inbound/rest.py
decisions:
  - "websockets>=12,<14 as optional [subscriptions] extra"
  - "graphql-transport-ws sub-protocol (not legacy subscriptions-transport-ws)"
  - "Bounded asyncio.Queue for backpressure (default 128, configurable)"
  - "WS endpoint proxy pattern: client→FastAPI WS→UpstreamWSTransport→upstream"
  - "Thread-based mock WS servers for TestClient WS tests (event loop isolation)"
metrics:
  duration: "10m"
  completed: "2026-06-16T04:21:00Z"
---

# Phase 11 Plan 01: WebSocket Subscription Transport Summary

**One-liner:** UpstreamWSTransport with graphql-transport-ws protocol, AsyncGraphQLClient.subscribe() async iterator, and FastAPI WS proxy endpoint at /graphql/subscribe.

## What Was Built

### 1. Optional `[subscriptions]` Extra (pyproject.toml)
- Added `websockets>=12,<14` as optional dependency group `subscriptions`
- Updated `all` extra to include `subscriptions`
- Added `websockets` to `dev` dependencies for test execution

### 2. Subscription Config (config.py)
- `GRAPHQL_SUBSCRIPTION_ENDPOINT` — ws:// or wss:// URL for upstream subscription WS
- `GRAPHQL_SUBSCRIPTION_QUEUE_SIZE` — bounded async queue size (default 128)

### 3. UpstreamWSTransport (ws_transport.py)
- Full `graphql-transport-ws` sub-protocol: `connection_init` → `connection_ack` → `subscribe` → `next`/`error`/`complete`
- Async context manager (`__aenter__`/`__aexit__`) for connection lifecycle
- `AsyncIterator[QueryResult]` via `__aiter__` — yields from bounded queue
- Background `_reader_task` processes messages and puts `QueryResult` on queue
- Import guard: raises `ImportError` with install instructions when websockets is absent
- Error handling: upstream disconnect yields transport error result, then stops

### 4. AsyncGraphQLClient.subscribe() (async_lib.py)
- Async generator method yielding `QueryResult` objects
- `_resolve_ws_endpoint()` — converts `http→ws`, `https→wss` when `subscription_endpoint` not set
- Forwards bearer token via headers
- Emits audit log per event when `audit_log=True`

### 5. WebSocket Endpoint (rest.py)
- `@app.websocket("/graphql/subscribe")` — full protocol-level proxy
- Validates `connection_init` and `subscribe` messages; rejects malformed sequences
- Forwards whitelisted headers from `connection_init` payload (same `_FORWARDED_HEADERS`)
- Clean error handling: client disconnect, import error, generic exceptions

## Tests Added

| Test File | Tests | Description |
|-----------|-------|-------------|
| `tests/test_ws_transport.py` | 4 | Protocol lifecycle, error messages, clean close, import guard |
| `tests/test_subscribe.py` | 5 | subscribe() yields results, no endpoint error, WS endpoint protocol, reject without init |
| **Total** | **9** | |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Thread-based mock WS server for TestClient tests**
- **Found during:** Task 2 (WS endpoint tests)
- **Issue:** Starlette TestClient runs ASGI app in a separate thread, requiring the mock WS server to run in its own event loop thread (not as an async fixture in the test's loop)
- **Fix:** Used `threading.Thread` with `asyncio.new_event_loop()` for mock WS server in endpoint tests
- **Files modified:** `tests/test_subscribe.py`

## Self-Check: PASSED
