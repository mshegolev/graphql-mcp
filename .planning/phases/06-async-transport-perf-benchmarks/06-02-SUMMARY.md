---
phase: 06-async-transport-perf-benchmarks
plan: 02
subsystem: client
tags: [async, client, facade, lifecycle, context-manager]
dependency_graph:
  requires: [AsyncHttpTransport]
  provides: [AsyncGraphQLClient]
  affects: [fastapi-adapter, package-exports]
tech_stack:
  added: []
  patterns: [async-context-manager, atexit-sync-cleanup, mirror-strategy]
key_files:
  created:
    - src/graphql_mcp/adapters/inbound/async_lib.py
    - tests/test_async_operations.py
    - tests/test_async_client_lifecycle.py
  modified:
    - src/graphql_mcp/__init__.py
decisions:
  - "Async client mirrors sync client exactly — same constructor, operations, error handling"
  - "query/raw/close are async; introspect/describe_type/list_subgraphs/refresh_schema are sync (no network I/O)"
  - "atexit uses sync cleanup path since atexit cannot await async close"
  - "from_env() skips IntrospectionSource/ServiceSdlSource (require sync transport)"
metrics:
  duration_seconds: 1314
  completed: "2026-06-08T13:17:26Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 32
  tests_total: 204
  lines_added: 682
---

# Phase 06 Plan 02: Async GraphQL Client Summary

**One-liner:** AsyncGraphQLClient with 6 operations (query/raw async, introspect/describe_type/list_subgraphs/refresh_schema sync), async context manager, idempotent close, atexit cleanup — mirroring sync GraphQLClient behavior exactly.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create AsyncGraphQLClient with 6 async operations + lifecycle | `1cb9cfa` | async_lib.py, __init__.py |
| 2 | Async client operation + lifecycle tests | `29135b1` | test_async_operations.py, test_async_client_lifecycle.py |

## What Was Built

### AsyncGraphQLClient (`adapters/inbound/async_lib.py`)
- Full mirror of `GraphQLClient` with async transport operations
- **Async methods:** `query()`, `raw()`, `close()` — await AsyncHttpTransport
- **Sync methods:** `introspect()`, `describe_type()`, `list_subgraphs()`, `refresh_schema()` — use in-process SchemaService/SchemaAnalyzer (no network I/O)
- Constructor: `(schema_service, transport: AsyncHttpTransport | None, config)`
- `from_env()` factory with GRAPHQL_* env var cascade (GitLab + file sources; skips introspection/federation sources that need sync transport)
- Async context manager: `async with AsyncGraphQLClient.from_env() as client:`
- Idempotent `close()` via `_closed` flag — safe to call multiple times
- `atexit` registration in `from_env()` using sync cleanup path (httpx.AsyncClient sync close for cleanup)
- Mutation guard: `check_mutation_guard()` called synchronously before any async transport call — no race condition possible

### Package Export Update (`__init__.py`)
- `from graphql_mcp import AsyncGraphQLClient` works
- `__all__` includes both `AsyncGraphQLClient` and `GraphQLClient`

### Async Operation Tests (`tests/test_async_operations.py`)
- 22 tests across 6 test classes mirroring sync `test_operations.py`:
  - `TestAsyncQuery` (8 tests): OK, GRAPHQL, TRANSPORT/500, TRANSPORT/ConnectError, mutation blocked, mutation allowed, no transport, with variables
  - `TestAsyncRaw` (4 tests): OK, mutation blocked, no query key, no transport
  - `TestAsyncIntrospect` (2 tests): schema summary, type listing
  - `TestAsyncDescribeType` (3 tests): TypeInfo, supergraph subgraph, unknown returns None
  - `TestAsyncListSubgraphs` (4 tests): from supergraph, url+owned_types, non-supergraph empty, source=off empty
  - `TestAsyncRefreshSchema` (1 test): cache invalidation

### Async Lifecycle Tests (`tests/test_async_client_lifecycle.py`)
- 10 tests across 3 test classes mirroring sync `test_client_lifecycle.py`:
  - `TestAsyncContextManager` (4 tests): enter returns self, exit closes, exit on exception, no transport
  - `TestAsyncExplicitClose` (4 tests): calls transport close, idempotent, no transport, sets closed flag
  - `TestAsyncAtexitRegistration` (2 tests): from_env registers atexit, atexit+context manager both safe

## Threat Mitigations Applied

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-06-04 | Same mutation guard + error classification as sync client | Implemented — check_mutation_guard called synchronously before async transport |
| T-06-05 | atexit sync cleanup + async context manager + _closed idempotency flag | Implemented — three layers of cleanup |
| T-06-06 | Mutation guard called synchronously before any async transport call | Implemented — no race condition possible |

## Deviations from Plan

None — plan executed exactly as written.

## TDD Gate Compliance

Both tasks were marked `tdd="true"`. Task 1 created the implementation, task 2 wrote the tests — sequential within the same plan. All 32 tests passed on first run, confirming behavioral parity with sync client. Gate commits:
- `feat(06-02)` at `1cb9cfa` — implementation (GREEN equivalent)
- `test(06-02)` at `29135b1` — behavioral test suite

## Decisions Made

1. **Mirror strategy**: AsyncGraphQLClient mirrors GraphQLClient line-by-line — same constructor, operations, error paths, mutation guard logic
2. **Async/sync split**: query/raw/close are async (network I/O via AsyncHttpTransport); introspect/describe_type/list_subgraphs/refresh_schema are sync (in-process SchemaService, no awaits needed)
3. **atexit sync cleanup**: Since atexit cannot await, `from_env()` registers a sync cleanup function that directly calls `transport._client.close()` — httpx.AsyncClient supports sync close for cleanup
4. **from_env() source cascade**: Skips IntrospectionSource and ServiceSdlSource (require sync HttpTransport); async client uses GitLab and file sources for schema resolution

## Verification Results

- `pytest tests/test_async_operations.py tests/test_async_client_lifecycle.py -v`: 32/32 passed
- `pytest tests/ -q`: 204/204 passed (172 existing + 32 new, zero regression)
- Both clients importable: `from graphql_mcp import AsyncGraphQLClient, GraphQLClient`
- All 6 operations present: query, raw, introspect, describe_type, list_subgraphs, refresh_schema
- Async/sync method types verified via `inspect.iscoroutinefunction`

## Self-Check: PASSED

- [x] `src/graphql_mcp/adapters/inbound/async_lib.py` exists (222 lines, min 100 required)
- [x] `tests/test_async_operations.py` exists (345 lines, min 150 required)
- [x] `tests/test_async_client_lifecycle.py` exists (115 lines, min 60 required)
- [x] `src/graphql_mcp/__init__.py` updated with AsyncGraphQLClient export
- [x] Commit `1cb9cfa` exists in git log
- [x] Commit `29135b1` exists in git log
- [x] No stubs found
- [x] No unexpected file deletions
