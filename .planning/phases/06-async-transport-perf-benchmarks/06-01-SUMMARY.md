---
phase: 06-async-transport-perf-benchmarks
plan: 01
subsystem: transport
tags: [async, httpx, protocol, transport]
dependency_graph:
  requires: []
  provides: [AsyncGraphQLTransport, AsyncHttpTransport]
  affects: [async-client, benchmarks]
tech_stack:
  added: [pytest-asyncio]
  patterns: [async-protocol, async-adapter, respx-async-mocking]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/async_http_transport.py
    - tests/test_async_http_transport.py
  modified:
    - src/graphql_mcp/ports/transport.py
    - pyproject.toml
decisions:
  - "AsyncGraphQLTransport protocol uses async def methods (not Awaitable return types) for clean Protocol definition"
  - "AsyncHttpTransport mirrors sync HttpTransport exactly — same constructor, error handling, codec injection"
  - "asyncio_mode=auto configured globally for pytest so async tests are auto-detected"
metrics:
  duration_seconds: 335
  completed: "2026-06-08T12:32:52Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 10
  tests_total: 164
  lines_added: 280
---

# Phase 06 Plan 01: Async HTTP Transport Summary

**One-liner:** Async GraphQL transport adapter using httpx.AsyncClient with 3-class error classification, codec injection, and protocol conformance — mirroring sync HttpTransport behavior exactly.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add AsyncGraphQLTransport protocol and create AsyncHttpTransport | `8074c0f` | ports/transport.py, async_http_transport.py |
| 2 | Async transport behavioral tests mirroring sync | `89a2f3c` | test_async_http_transport.py, pyproject.toml |

## What Was Built

### AsyncGraphQLTransport Protocol (`ports/transport.py`)
- Added `AsyncGraphQLTransport` protocol alongside existing `GraphQLTransport`
- `@runtime_checkable` for isinstance checks
- `async def execute()` and `async def post_raw()` returning `QueryResult`

### AsyncHttpTransport Adapter (`adapters/outbound/async_http_transport.py`)
- Uses `httpx.AsyncClient` (async counterpart to sync `httpx.Client`)
- Same constructor signature: `(endpoint, bearer_token, timeout, ssl_verify, headers, codec)`
- Same 3-class error classification:
  - `ErrorClass.OK` — 200 + clean data
  - `ErrorClass.GRAPHQL` — 200 + errors array present
  - `ErrorClass.TRANSPORT` — HTTP errors, connection errors, codec decode errors, non-200 status
- Codec injection via constructor with `get_codec()` factory default
- `async def close()` calls `await self._client.aclose()`

### Test Suite (`tests/test_async_http_transport.py`)
- 10 async tests using `pytest-asyncio` (auto mode) and `respx.mock`
- `TestAsyncHttpTransportErrorClassification` (4 tests): OK, GRAPHQL, HTTP 500, ConnectError
- `TestAsyncHttpTransportUsesCodec` (4 tests): SpyCodec injection, post_raw codec, factory default, decode ValueError
- `TestAsyncHttpTransportLifecycle` (1 test): close/aclose verification
- `TestAsyncProtocolConformance` (1 test): isinstance check against AsyncGraphQLTransport

## Threat Mitigations Applied

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-06-01 | Codec-agnostic ValueError/TypeError catch on decode | Implemented — identical to sync |
| T-06-02 | httpx.Timeout with connect capped at min(timeout, 10s) | Implemented — identical to sync |
| T-06-03 | Error text truncated to 500 chars | Accepted — identical to sync |

## Deviations from Plan

None — plan executed exactly as written.

## TDD Gate Compliance

Task 2 was marked `tdd="true"`. The implementation (task 1) was created before tests (task 2) per plan design — tasks are sequential within the same plan. Tests were written and all 10 passed on first run, confirming the implementation correctly mirrors sync behavior. Gate commits:
- `feat(06-01)` at `8074c0f` — implementation (GREEN equivalent since no prior RED in same task)
- `test(06-01)` at `89a2f3c` — behavioral test suite

## Decisions Made

1. **Async Protocol design**: Used `async def` in Protocol body rather than `Awaitable` return types — cleaner, standard Python pattern
2. **asyncio_mode=auto**: Configured globally in pyproject.toml so all async test functions are auto-detected without per-test markers
3. **Mirror strategy**: Line-by-line mirror of sync transport ensures behavioral parity; no refactoring or abstraction to reduce duplication (keep independent for clarity)

## Verification Results

- `pytest tests/test_async_http_transport.py -v`: 10/10 passed
- `pytest tests/ -q`: 164/164 passed (154 existing + 10 new, zero regression)
- Both protocols importable: `AsyncGraphQLTransport` + `GraphQLTransport`
- `httpx.AsyncClient` used in async transport: confirmed

## Self-Check: PASSED

- [x] `src/graphql_mcp/adapters/outbound/async_http_transport.py` exists (88 lines)
- [x] `tests/test_async_http_transport.py` exists (175 lines)
- [x] `src/graphql_mcp/ports/transport.py` updated (40 lines, includes AsyncGraphQLTransport)
- [x] Commit `8074c0f` exists in git log
- [x] Commit `89a2f3c` exists in git log
- [x] No stubs found
- [x] No unexpected file deletions
