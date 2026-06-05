---
phase: 02-operations-errors-federation
plan: 02
subsystem: adapters/inbound, config
tags: [graphql-client, operations, mutation-guard, schema-analyzer, federation, error-class, integration-tests]
dependency_graph:
  requires: [query_guard, schema_analyzer, http_transport, schema_service, domain/models]
  provides: [GraphQLClient.query, GraphQLClient.raw, GraphQLClient.introspect, GraphQLClient.describe_type, GraphQLClient.list_subgraphs, GraphQLClient.refresh_schema]
  affects: [Phase 3 inbound adapters (MCP/FastAPI/CLI will delegate to these methods)]
tech_stack:
  added: [respx (test dependency)]
  patterns: [facade pattern wiring, mutation guard before transport, supergraph_source config shortcircuit]
key_files:
  created:
    - tests/test_operations.py
  modified:
    - src/graphql_mcp/adapters/inbound/lib.py
    - src/graphql_mcp/config.py
    - tests/conftest.py
decisions:
  - "ErrorClass and QueryResult imported at runtime in lib.py (not TYPE_CHECKING) — needed for return values"
  - "Mutation guard check runs BEFORE transport None check — block mutations even without endpoint"
  - "respx mock URL must use trailing slash to match httpx base_url resolution"
metrics:
  duration: 7m
  completed: "2026-06-05T21:24:37Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 22
  tests_total: 60
  files_created: 1
  files_modified: 3
---

# Phase 02 Plan 02: Wire Operations + Integration Tests Summary

**One-liner:** All 6 GraphQLClient operations (query/raw/introspect/describe_type/list_subgraphs/refresh_schema) wired through mutation guard and schema analyzer with 22 integration tests covering 3-class error typing and federation

## What Was Built

### GraphQLClient Operations (lib.py)

1. **`query(query, variables)`** — Executes GraphQL via transport, mutation guard blocks mutations by default, returns `QueryResult` with `error_class` (ok/graphql/transport)
2. **`raw(body)`** — Passes arbitrary POST body through transport; mutation guard applies only if `body["query"]` exists as a string; bodies without `query` key pass through
3. **`introspect()`** — Returns `SchemaSummary` (query_fields + types) via `SchemaAnalyzer.build_summary()` on resolved SDL — replaces old `SchemaGraph` return type
4. **`describe_type(name)`** — Returns `TypeInfo` with fields, args, and federation subgraph ownership via `SchemaAnalyzer.describe_type()`
5. **`list_subgraphs()`** — Returns `list[Subgraph]` from supergraph SDL; shortcircuits to `[]` when `supergraph_source="off"`
6. **`refresh_schema()`** — Delegates to `SchemaService.invalidate()` (unchanged from Phase 1)

### Config Extension

- Added `supergraph_source: str = "auto"` field to `GraphQLConfig` (auto|off)
- Controls whether `list_subgraphs()` attempts SDL parsing or returns empty list

### Integration Test Suite (test_operations.py)

22 tests organized into 6 test classes:

| Class | Tests | Requirements |
|-------|-------|-------------|
| TestQuery | 8 | GQL-01, GQL-02, GQL-03 |
| TestRaw | 4 | GQL-09, GQL-03 |
| TestIntrospect | 2 | GQL-04 |
| TestDescribeType | 3 | GQL-05 |
| TestListSubgraphs | 4 | GQL-08 |
| TestRefreshSchema | 1 | GQL-07 |

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| test_operations.py | 22 | All pass |
| test_query_guard.py | 10 | All pass |
| test_schema_analyzer.py | 15 | All pass |
| test_schema_cascade.py | 6 | All pass |
| test_ttl_cache.py | 4 | All pass |
| test_domain_purity.py | 3 | All pass |
| **Total** | **60** | **All pass** |

## Phase 2 Success Criteria Validation

| Criterion | Test(s) | Status |
|-----------|---------|--------|
| SC1: query() returns QueryResult with error_class ok/graphql/transport | test_query_returns_query_result_with_data, test_query_error_class_graphql_on_errors, test_query_error_class_transport_on_http_error, test_query_error_class_transport_on_timeout | ✅ |
| SC2: Mutation guard blocks/allows on query and raw | test_query_blocks_mutation, test_query_allows_mutation_when_enabled, test_raw_blocks_mutation | ✅ |
| SC3: introspect() returns SchemaSummary, describe_type returns TypeInfo with subgraph | test_introspect_returns_schema_summary, test_describe_type_returns_type_info, test_describe_type_with_supergraph | ✅ |
| SC4: list_subgraphs returns Subgraph list, empty when off | test_list_subgraphs_from_supergraph, test_list_subgraphs_has_url_and_owned_types, test_list_subgraphs_empty_when_supergraph_source_off | ✅ |
| SC5: refresh_schema forces re-fetch | test_refresh_forces_refetch | ✅ |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 0d16eb2 | feat(02-02): wire all 6 operations into GraphQLClient + add supergraph_source config |
| 2 | 32d49c0 | test(02-02): add integration tests for all 6 GraphQLClient operations |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] respx mock URL mismatch with httpx base_url trailing slash**
- **Found during:** task 2
- **Issue:** `httpx.Client(base_url="https://mock.test/graphql")` resolves `.post("")` to `https://mock.test/graphql/` (trailing slash), but respx was mocked for `https://mock.test/graphql` (no slash) — causing `AllMockedAssertionError`
- **Fix:** Used `MOCK_ENDPOINT_RESOLVED` constant with trailing slash for respx route matching
- **Files modified:** tests/test_operations.py
- **Commit:** 32d49c0

## Requirements Addressed

| Requirement | Coverage |
|-------------|----------|
| GQL-01 | Complete — query() returns QueryResult with data/errors separated |
| GQL-02 | Complete — error_class=ok/graphql/transport verified |
| GQL-03 | Complete — mutation guard blocks by default, allows when enabled, works on both query() and raw() |
| GQL-04 | Complete — introspect() returns SchemaSummary with query_fields and types |
| GQL-05 | Complete — describe_type() returns TypeInfo with subgraph from supergraph SDL |
| GQL-07 | Complete — refresh_schema() forces re-fetch verified |
| GQL-08 | Complete — list_subgraphs() returns Subgraph list, empty for non-supergraph and off |
| GQL-09 | Complete — raw() returns QueryResult, mutation guard on body["query"] |

## Self-Check: PASSED
