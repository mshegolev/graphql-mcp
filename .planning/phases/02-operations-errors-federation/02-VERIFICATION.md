---
phase: 02-operations-errors-federation
verified: 2026-06-05T21:30:25Z
status: passed
score: 5/5 roadmap SCs verified + 19/19 plan truths verified
overrides_applied: 0
must_haves:
  roadmap_truths:
    - "SC1: client.query(query, variables) returns QueryResult{data, errors, error_class} — error_class=ok on success, graphql on errors[], transport on HTTP!=200/timeout"
    - "SC2: mutation{...} to client.query() or client.raw() raises MutationGuardError; succeeds when GRAPHQL_ALLOW_MUTATIONS=true"
    - "SC3: client.introspect() returns SchemaSummary; client.describe_type('SomeType') returns TypeInfo with subgraph populated from supergraph, null otherwise"
    - "SC4: client.list_subgraphs() returns non-empty Subgraph list from supergraph SDL; empty list when GRAPHQL_SUPERGRAPH_SOURCE=off"
    - "SC5: client.refresh_schema() forces next schema access to re-fetch (mock adapter called twice)"
---

# Phase 2: Operations, Errors & Federation Verification Report

**Phase Goal:** All 6 operations are callable through the lib facade and return typed results with correct error classification and federation metadata.
**Verified:** 2026-06-05T21:30:25Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

**Roadmap Success Criteria (non-negotiable contract):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | `client.query(query, variables)` returns `QueryResult{data, errors, error_class}` — `error_class="ok"` on success, `"graphql"` on errors[], `"transport"` on HTTP!=200/timeout | ✓ VERIFIED | `lib.py:122-135` — `query()` calls `check_mutation_guard`, falls back to `ErrorClass.TRANSPORT` when no transport, delegates to `self._transport.execute()`. `http_transport.py:38-79` correctly classifies all 3 error classes. Tests `test_query_returns_query_result_with_data`, `test_query_error_class_graphql_on_errors`, `test_query_error_class_transport_on_http_error`, `test_query_error_class_transport_on_timeout` all PASS. |
| SC2 | Sending `mutation{...}` to `client.query()` or `client.raw()` raises `MutationGuardError`; succeeds when `GRAPHQL_ALLOW_MUTATIONS=true` | ✓ VERIFIED | `lib.py:128-129` — guard check before transport. `lib.py:143-146` — raw checks `body.get("query")`. `query_guard.py:13-37` — AST-based detection via `OperationType.MUTATION`. Tests `test_query_blocks_mutation`, `test_query_allows_mutation_when_enabled`, `test_raw_blocks_mutation` all PASS. |
| SC3 | `client.introspect()` returns `SchemaSummary`; `client.describe_type("SomeType")` returns `TypeInfo{name, fields, args, subgraph}` with subgraph populated from supergraph, null otherwise | ✓ VERIFIED | `lib.py:154-162` — `introspect()` delegates to `self._analyzer.build_summary()`, `describe_type()` delegates to `self._analyzer.describe_type()`. `schema_analyzer.py:60-113` — substantive implementation with field extraction, type mapping, and `_find_subgraph_for_type()`. Tests `test_introspect_returns_schema_summary`, `test_introspect_lists_types`, `test_describe_type_returns_type_info`, `test_describe_type_with_supergraph`, `test_describe_type_unknown_returns_none` all PASS. |
| SC4 | `client.list_subgraphs()` returns non-empty `Subgraph{name, url, owned_types}` list from supergraph SDL; returns empty list when `GRAPHQL_SUPERGRAPH_SOURCE=off` | ✓ VERIFIED | `lib.py:164-173` — shortcircuits to `[]` when `supergraph_source == "off"`, else delegates to `self._analyzer.list_subgraphs()`. `schema_analyzer.py:115-175` — parses `join__Graph` enum + `@join__graph` directives with dual validation. Tests `test_list_subgraphs_from_supergraph`, `test_list_subgraphs_has_url_and_owned_types`, `test_list_subgraphs_empty_for_non_supergraph`, `test_list_subgraphs_empty_when_supergraph_source_off` all PASS. |
| SC5 | `client.refresh_schema()` forces next schema access to re-fetch (mock adapter called twice across two `introspect()` calls separated by `refresh_schema()`) | ✓ VERIFIED | `lib.py:175-177` — delegates to `self._schema_service.invalidate()`. Test `test_refresh_forces_refetch` explicitly asserts `source.call_count == 2` after `introspect()` → `refresh_schema()` → `introspect()`. PASSES. |

**Score:** 5/5 roadmap SCs verified

**Plan 01 Truths (Wave 1 — query_guard + schema_analyzer):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| W1-1 | `contains_mutation()` detects mutation operations via AST parse and returns True | ✓ VERIFIED | `query_guard.py:13-28` — `gql_parse()` + `OperationType.MUTATION` check. Tests `test_detects_anonymous_mutation`, `test_detects_named_mutation` PASS. |
| W1-2 | `contains_mutation()` returns False for queries, subscriptions, and unparseable strings | ✓ VERIFIED | `query_guard.py:21-26` — empty/whitespace check + `except Exception: return False`. Tests `test_query_is_not_mutation`, `test_subscription_is_not_mutation`, `test_unparseable_query_returns_false`, `test_empty_string_returns_false` all PASS. |
| W1-3 | `check_mutation_guard()` raises MutationGuardError when mutation detected | ✓ VERIFIED | `query_guard.py:31-37` — `if contains_mutation(query_str): raise MutationGuardError()`. Test `test_raises_on_mutation` PASSES with match. |
| W1-4 | `SchemaAnalyzer.build_summary()` converts SDL into SchemaSummary with query_fields and types | ✓ VERIFIED | `schema_analyzer.py:60-79` — extracts `query_fields` from `schema.query_type.fields`, maps types excluding builtins. Tests `test_extracts_query_fields`, `test_extracts_types_excluding_builtins`, `test_type_kinds_are_set` PASS. |
| W1-5 | `SchemaAnalyzer.describe_type()` returns TypeInfo with fields, args, and subgraph | ✓ VERIFIED | `schema_analyzer.py:81-113` — builds `FieldInfo` with args, resolves subgraph. Tests `test_returns_type_info_with_fields`, `test_field_args_extracted`, `test_subgraph_populated_from_supergraph` PASS. |
| W1-6 | `SchemaAnalyzer.list_subgraphs()` extracts Subgraph list from supergraph SDL | ✓ VERIFIED | `schema_analyzer.py:115-175` — 4-step extraction with dual validation. Tests `test_extracts_subgraphs_from_supergraph_sdl`, `test_subgraph_has_url`, `test_subgraph_has_owned_types` PASS. |
| W1-7 | `SchemaAnalyzer.list_subgraphs()` returns empty list for non-supergraph SDL | ✓ VERIFIED | `schema_analyzer.py:130-131` — returns `[]` when no `join__Graph` enum. `schema_analyzer.py:152-154` — returns `[]` when enum exists but no directives. Tests `test_returns_empty_list_for_non_supergraph`, `test_returns_empty_for_enum_without_directives` PASS. |

**Plan 02 Truths (Wave 2 — GraphQLClient wiring):**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| W2-1 | `client.query(query, variables)` returns QueryResult with data, errors, and error_class | ✓ VERIFIED | `lib.py:122-135`. Test `test_query_returns_query_result_with_data` — asserts `result.data`, `result.errors == []`, `result.error_class == ErrorClass.OK`. |
| W2-2 | `client.query()` returns error_class=ok/graphql/transport | ✓ VERIFIED | Tests cover all 3: `test_query_returns_query_result_with_data` (OK), `test_query_error_class_graphql_on_errors` (GRAPHQL), `test_query_error_class_transport_on_http_error` + `test_query_error_class_transport_on_timeout` (TRANSPORT). |
| W2-3 | `client.query()` raises MutationGuardError on mutation when allow_mutations=False | ✓ VERIFIED | `lib.py:128-129`. Test `test_query_blocks_mutation` PASSES. |
| W2-4 | `client.query()` allows mutation when allow_mutations=True | ✓ VERIFIED | `lib.py:128` — guard skipped when `self._allow_mutations` is True. Test `test_query_allows_mutation_when_enabled` PASSES. |
| W2-5 | `client.raw(body)` returns QueryResult with mutation guard on body['query'] | ✓ VERIFIED | `lib.py:137-152`. Tests `test_raw_returns_query_result`, `test_raw_blocks_mutation` PASS. |
| W2-6 | `client.raw(body)` allows body without 'query' key (no guard) | ✓ VERIFIED | `lib.py:144-146` — only checks `body.get("query")` if it's a string. Test `test_raw_allows_body_without_query_key` PASSES. |
| W2-7 | `client.introspect()` returns SchemaSummary with query_fields and types | ✓ VERIFIED | `lib.py:154-157`. Test `test_introspect_returns_schema_summary` asserts `isinstance(result, SchemaSummary)` + fields present. |
| W2-8 | `client.describe_type('User')` returns TypeInfo with fields and subgraph | ✓ VERIFIED | `lib.py:159-162`. Test `test_describe_type_returns_type_info` + `test_describe_type_with_supergraph` PASS. |
| W2-9 | `client.describe_type('NonExistent')` returns None | ✓ VERIFIED | `lib.py:159-162` delegates to analyzer which returns None. Test `test_describe_type_unknown_returns_none` PASSES. |
| W2-10 | `client.list_subgraphs()` returns list of Subgraph from supergraph SDL | ✓ VERIFIED | `lib.py:164-173`. Test `test_list_subgraphs_from_supergraph` PASSES. |
| W2-11 | `client.list_subgraphs()` returns empty list when supergraph_source=off | ✓ VERIFIED | `lib.py:170-171`. Test `test_list_subgraphs_empty_when_supergraph_source_off` PASSES. |
| W2-12 | `client.refresh_schema()` forces next schema access to re-fetch | ✓ VERIFIED | `lib.py:175-177`. Test `test_refresh_forces_refetch` asserts `call_count == 2`. PASSES. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/graphql_mcp/adapters/outbound/query_guard.py` | Mutation detection via graphql-core AST parse | ✓ VERIFIED | 37 lines. Exports `contains_mutation`, `check_mutation_guard`. Imports `graphql.parse`, `OperationType.MUTATION`. Raises `MutationGuardError` from domain. |
| `src/graphql_mcp/adapters/outbound/schema_analyzer.py` | SDL parsing into domain model objects | ✓ VERIFIED | 225 lines. `SchemaAnalyzer` class with `build_summary()`, `describe_type()`, `list_subgraphs()`. SHA-256 caching. `_find_subgraph_for_type()` helper. Full federation support. |
| `src/graphql_mcp/adapters/inbound/lib.py` | GraphQLClient with all 6 operations | ✓ VERIFIED | 177 lines. 6 methods: `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`. Wired to query_guard, schema_analyzer, http_transport. |
| `src/graphql_mcp/config.py` | GraphQLConfig with supergraph_source field | ✓ VERIFIED | 41 lines. `supergraph_source: str = "auto"` on line 41. |
| `tests/test_query_guard.py` | Mutation guard unit tests | ✓ VERIFIED | 45 lines. 10 tests across 2 test classes. All pass. |
| `tests/test_schema_analyzer.py` | Schema analyzer unit tests | ✓ VERIFIED | 112 lines. 15 tests across 4 test classes. All pass. |
| `tests/test_operations.py` | Integration tests for all 6 operations | ✓ VERIFIED | 383 lines. 22 tests across 6 test classes. All pass. |
| `tests/conftest.py` | Test fixtures including SAMPLE_SUPERGRAPH_SDL | ✓ VERIFIED | 107 lines. `SAMPLE_SUPERGRAPH_SDL` with join__Graph enum, @join__graph directives, @join__type type ownership. `MockSchemaSource` with `call_count`. `simple_client` fixture. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `lib.py` | `query_guard.py` | `from graphql_mcp.adapters.outbound.query_guard import check_mutation_guard` | ✓ WIRED | Line 10: imported. Lines 129, 146: used in `query()` and `raw()`. |
| `lib.py` | `schema_analyzer.py` | `from graphql_mcp.adapters.outbound.schema_analyzer import SchemaAnalyzer` | ✓ WIRED | Line 11: imported. Line 50: instantiated in `__init__`. Lines 157, 162, 173: used in `introspect()`, `describe_type()`, `list_subgraphs()`. |
| `lib.py` | `http_transport.py` | `self._transport.execute()` and `self._transport.post_raw()` | ✓ WIRED | Line 135: `self._transport.execute(query, variables)`. Line 152: `self._transport.post_raw(body)`. |
| `query_guard.py` | `domain.errors.MutationGuardError` | `from graphql_mcp.domain.errors import MutationGuardError` | ✓ WIRED | Line 8: imported. Line 37: `raise MutationGuardError()`. |
| `schema_analyzer.py` | `domain.models` | `from graphql_mcp.domain.models import FieldInfo, SchemaSummary, Subgraph, TypeInfo, TypeSummary` | ✓ WIRED | Lines 24-30: imported. Used throughout as return types in all 3 public methods. |
| `lib.py` | `domain.models` | `from graphql_mcp.domain.models import ErrorClass, QueryResult` | ✓ WIRED | Line 14: imported at runtime. Lines 131-134, 148-151: `QueryResult(error_class=ErrorClass.TRANSPORT)` used in fallback paths. |

### Data-Flow Trace (Level 4)

Not applicable for this phase. The phase produces a library facade (not a rendering component). Data flows through the lib methods to callers — verified by integration tests that assert on returned data values.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 60 tests pass | `PYTHONPATH=src python3 -m pytest tests/ -v` | `60 passed in 0.16s` | ✓ PASS |
| GraphQLClient imports cleanly | `python3 -c "from graphql_mcp.adapters.inbound.lib import GraphQLClient"` | `import OK` | ✓ PASS |
| All 6 operations present with correct signatures | `inspect.signature()` on all 6 methods | `query(self, query: str, variables: dict[str, Any] | None = None) -> QueryResult` etc. | ✓ PASS |
| query_guard exports both functions | `from graphql_mcp.adapters.outbound.query_guard import contains_mutation, check_mutation_guard` | Both are `<class 'function'>` | ✓ PASS |
| SchemaAnalyzer exports 3 public methods | `dir(SchemaAnalyzer())` | `['build_summary', 'describe_type', 'list_subgraphs']` | ✓ PASS |
| Domain purity preserved | `grep -r "from graphql " src/graphql_mcp/domain/ src/graphql_mcp/ports/` | Empty (exit 1) | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-----------|-------------|--------|----------|
| GQL-01 | 02-02 | `query(query, variables)` returns `data` and `errors` separately as typed `QueryResult` | ✓ SATISFIED | `lib.py:122-135`. Tests `test_query_returns_query_result_with_data`, `test_query_with_variables` verify data/errors separation. |
| GQL-02 | 02-02 | Every result carries `error_class` — one of `transport`/`graphql`/`ok` | ✓ SATISFIED | `http_transport.py:59-79` classifies all 3. Tests cover OK, GRAPHQL, TRANSPORT (HTTP error + timeout). |
| GQL-03 | 02-01, 02-02 | Mutation-guard in `query` and `raw`; blocked unless `GRAPHQL_ALLOW_MUTATIONS=true` | ✓ SATISFIED | `query_guard.py` provides AST detection. `lib.py:128-129,143-146` wires guard. Tests `test_query_blocks_mutation`, `test_query_allows_mutation_when_enabled`, `test_raw_blocks_mutation`. |
| GQL-04 | 02-01, 02-02 | `introspect()` returns summary of Query fields and types | ✓ SATISFIED | `schema_analyzer.py:60-79` builds summary. `lib.py:154-157` delegates. Tests `test_introspect_returns_schema_summary`, `test_introspect_lists_types`. |
| GQL-05 | 02-01, 02-02 | `describe_type(name)` returns field/arg details plus owning subgraph | ✓ SATISFIED | `schema_analyzer.py:81-113` with `_find_subgraph_for_type()`. `lib.py:159-162` delegates. Tests `test_describe_type_returns_type_info`, `test_describe_type_with_supergraph`, `test_describe_type_unknown_returns_none`. |
| GQL-07 | 02-02 | `refresh_schema()` clears schema cache and forces re-fetch | ✓ SATISFIED | `lib.py:175-177`. Test `test_refresh_forces_refetch` verifies call_count increments. |
| GQL-08 | 02-01, 02-02 | `list_subgraphs()` returns `Subgraph{name, url, owned_types}` with graceful null degradation | ✓ SATISFIED | `schema_analyzer.py:115-175` with dual validation. `lib.py:164-173` with off shortcircuit. Tests cover supergraph, non-supergraph, off, enum-without-directives. |
| GQL-09 | 02-02 | `raw(body)` accepts arbitrary POST body and returns `QueryResult` (mutation-guard applies) | ✓ SATISFIED | `lib.py:137-152`. Tests `test_raw_returns_query_result`, `test_raw_blocks_mutation`, `test_raw_allows_body_without_query_key`, `test_raw_no_transport_returns_transport_error`. |

No orphaned requirements detected. REQUIREMENTS.md maps GQL-01..GQL-05, GQL-07..GQL-09 to Phase 2, all covered by plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No anti-patterns found | — | — |

**Details:**
- No TODO/FIXME/PLACEHOLDER markers in any Phase 2 source files.
- No debug `print()` statements in production code.
- `return []` in `lib.py:171` and `schema_analyzer.py:131,154` are intentional graceful degradation (supergraph_source=off, non-supergraph SDL, enum-without-directives) — not stubs. Validated by tests.
- Domain purity preserved: zero graphql-core imports in `domain/` or `ports/`.

### Human Verification Required

None. All phase behaviors are library-level operations verified by automated tests with mock transport. No UI, no visual behavior, no external service integration needed for this phase.

### Gaps Summary

No gaps found. All 5 roadmap Success Criteria are verified. All 19 plan-level truths are verified. All 8 artifacts pass 3-level checks (exist, substantive, wired). All 6 key links are wired. All 8 requirement IDs are satisfied. 60 tests pass. No anti-patterns detected. Domain purity preserved.

---

_Verified: 2026-06-05T21:30:25Z_
_Verifier: OpenCode (gsd-verifier)_
