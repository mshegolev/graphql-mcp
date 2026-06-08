---
phase: 08-entities-ship-v1.1
plan: 01
subsystem: federation
tags: [entities, federation, pass-through, _entities]
dependency_graph:
  requires: []
  provides: [entities-operation, rest-entities-endpoint, mcp-entities-tool, cli-entities-command]
  affects: [lib, async_lib, rest, mcp_stdio, cli]
tech_stack:
  added: []
  patterns: [federation-pass-through, _entities-query]
key_files:
  created: []
  modified:
    - src/graphql_mcp/adapters/inbound/lib.py
    - src/graphql_mcp/adapters/inbound/async_lib.py
    - src/graphql_mcp/adapters/inbound/rest.py
    - src/graphql_mcp/adapters/inbound/mcp_stdio.py
    - src/graphql_mcp/adapters/inbound/cli.py
    - tests/test_operations.py
    - tests/test_async_operations.py
    - tests/test_rest.py
    - tests/test_mcp_stdio.py
    - tests/test_mcp_http.py
    - tests/test_cli.py
decisions:
  - "_entities query uses __typename-only selection set — gateway resolves the rest"
  - "entities() bypasses mutation guard entirely — it is a query, not a mutation"
  - "All faces delegate to GraphQLClient.entities() — thin adapter pattern maintained"
metrics:
  duration: 6m18s
  completed: "2026-06-08T15:49:25Z"
  tasks: 2/2
  tests_added: 16
  tests_total: 229
---

# Phase 08 Plan 01: Federation entities() Operation Summary

Federation _entities(representations:) pass-through on both sync and async clients, exposed via REST POST /graphql/entities, MCP entities tool, and CLI graphql-mcp entities command.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add entities() to GraphQLClient and AsyncGraphQLClient with TDD | d38c978 (RED), 00eb879 (GREEN) | lib.py, async_lib.py, test_operations.py, test_async_operations.py |
| 2 | Expose entities in REST, MCP, CLI faces | ac9d02d | rest.py, mcp_stdio.py, cli.py, test_rest.py, test_mcp_stdio.py, test_mcp_http.py, test_cli.py |

## Implementation Details

### _ENTITIES_QUERY Constant

Both `lib.py` and `async_lib.py` define a module-level constant:

```graphql
query ($representations: [_Any!]!) {
  _entities(representations: $representations) {
    __typename
  }
}
```

The `__typename` field ensures a non-empty selection set. The federation gateway resolves entity fields based on the `__typename` and key fields in each representation.

### Client Methods

- `GraphQLClient.entities(representations: list[dict[str, Any]]) -> QueryResult` — sync, delegates to `self._transport.execute()`
- `AsyncGraphQLClient.entities(representations: list[dict[str, Any]]) -> QueryResult` — async, delegates to `await self._transport.execute()`
- Neither method invokes the mutation guard (entities is a query operation)
- No-transport returns `QueryResult(error_class=TRANSPORT)`

### Face Exposure

- **REST**: `POST /graphql/entities` with `EntitiesRequest(representations: list[dict[str, Any]])` Pydantic model
- **MCP**: `entities` tool registered on FastMCP server (7 tools total)
- **CLI**: `graphql-mcp entities '<json_array>'` command

## Test Coverage

| Test File | Tests Added | Description |
|-----------|-------------|-------------|
| test_operations.py | 6 | TestEntities: happy path, variables, no-transport, mutation guard, transport error, graphql error |
| test_async_operations.py | 6 | TestAsyncEntities: async mirrors of all 6 sync tests |
| test_rest.py | 2 | TestEntities: no-transport returns transport error, missing representations returns 422 |
| test_mcp_stdio.py | 1 | entities tool delegation no-transport test |
| test_mcp_http.py | 0 | Updated expected_tools set to include "entities" (7 tools) |
| test_cli.py | 1 | TestCLIEntities: no-transport returns transport error |

**Total**: 229 tests passing (213 original + 16 new), 0 regressions.

## TDD Gate Compliance

- RED gate: `d38c978` — `test(08-01): add failing tests for entities() on sync and async clients`
- GREEN gate: `00eb879` — `feat(08-01): implement entities() on GraphQLClient and AsyncGraphQLClient`
- REFACTOR gate: Skipped — implementation was clean, no refactoring needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated MCP HTTP expected tools set**
- **Found during:** task 2
- **Issue:** `tests/test_mcp_http.py::test_mcp_tools_list_returns_all_tools` expected 6 tools, failed because `entities` was now the 7th
- **Fix:** Added `"entities"` to `expected` set in `test_mcp_http.py`
- **Files modified:** `tests/test_mcp_http.py`
- **Commit:** ac9d02d (included with task 2)

## Decisions Made

1. **__typename-only selection set**: The `_ENTITIES_QUERY` uses `{ __typename }` as its selection set. The federation gateway resolves entity fields; the client just passes representations through.
2. **No mutation guard on entities()**: Since `_entities` is a query operation (not a mutation), it bypasses the mutation guard entirely. This is by design per the plan.
3. **Thin adapter pattern maintained**: REST, MCP, and CLI all delegate to `GraphQLClient.entities()` with no business logic in the face layer.

## Known Stubs

None — all functionality is fully wired.

## Self-Check: PASSED

- [x] `src/graphql_mcp/adapters/inbound/lib.py` contains `def entities` and `_ENTITIES_QUERY`
- [x] `src/graphql_mcp/adapters/inbound/async_lib.py` contains `async def entities` and `_ENTITIES_QUERY`
- [x] `src/graphql_mcp/adapters/inbound/rest.py` contains `/graphql/entities`
- [x] `src/graphql_mcp/adapters/inbound/mcp_stdio.py` contains `def entities`
- [x] `src/graphql_mcp/adapters/inbound/cli.py` contains `def entities`
- [x] Commit d38c978 exists (RED)
- [x] Commit 00eb879 exists (GREEN)
- [x] Commit ac9d02d exists (task 2)
- [x] 229 tests pass, 0 failures
