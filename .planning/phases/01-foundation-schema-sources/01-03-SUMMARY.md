---
phase: 01-foundation-schema-sources
plan: 03
subsystem: composition-root
tags: [config, graphql-client, facade, tests, domain-purity, cascade, ttl-cache]
dependency_graph:
  requires: [domain-models, port-protocols, schema-service, http-transport, gitlab-source, introspection-source, federation-sdl-source, file-sdl-source]
  provides: [graphql-config, graphql-client, library-face, test-suite]
  affects: []
tech_stack:
  added: [pydantic-settings]
  patterns: [composition-root, factory-method, facade-pattern, env-driven-config]
key_files:
  created:
    - src/graphql_mcp/config.py
    - src/graphql_mcp/adapters/inbound/lib.py
    - tests/__init__.py
    - tests/conftest.py
    - tests/test_domain_purity.py
    - tests/test_schema_cascade.py
    - tests/test_ttl_cache.py
  modified:
    - src/graphql_mcp/__init__.py
decisions:
  - "GraphQLClient.from_env(**overrides: Any) accepts Any for overrides to support int/bool config fields via pydantic-settings coercion"
  - "TYPE_CHECKING block used for SchemaGraph and SchemaSource imports in lib.py to satisfy ruff TC001"
metrics:
  duration: "422s (~7min)"
  completed: "2026-06-05T20:20:01Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 7
  files_modified: 1
---

# Phase 01 Plan 03: Config, GraphQLClient.from_env(), and Test Suite Summary

Pydantic-settings GraphQLConfig reading GRAPHQL_* env vars, GraphQLClient.from_env() factory wiring 4-source cascade (GitLab > introspection > federation SDL > file) into SchemaService, package-level re-export via `from graphql_mcp import GraphQLClient`, and 13-test suite verifying domain purity, cascade fallback, and TTL cache behavior.

## What Was Done

### Task 1: Create GraphQLConfig and GraphQLClient.from_env() composition root
- Created `src/graphql_mcp/config.py` — `GraphQLConfig(BaseSettings)` with `env_prefix="GRAPHQL_"`, all connection, schema source selection, GitLab, and behavior fields
- Created `src/graphql_mcp/adapters/inbound/lib.py` — `GraphQLClient` facade with `from_env()` classmethod that reads config, builds HttpTransport when endpoint is set, wires cascade sources in priority order (gitlab > introspection > federation > sdl_file), and creates SchemaService
- Updated `src/graphql_mcp/__init__.py` to re-export `GraphQLClient` with `__all__`
- Verified: `from graphql_mcp import GraphQLClient` succeeds, `GraphQLClient.from_env()` returns wired client
- **Commit:** `e345447`

### Task 2: Create test suite for domain purity, schema cascade, and TTL cache
- Created `tests/__init__.py` — empty package marker
- Created `tests/conftest.py` — `MockSchemaSource` with configurable sdl/raise/None behavior and `call_count` tracking, `SAMPLE_SDL` fixture
- Created `tests/test_domain_purity.py` — 3 tests: file-scan domain/, file-scan ports/, grep belt-and-suspenders
- Created `tests/test_schema_cascade.py` — 6 tests: first-source-wins, fallback-on-none, fallback-on-exception, full-cascade (None>exception>None>success), all-fail-raises, empty-sources-raises
- Created `tests/test_ttl_cache.py` — 4 tests: cache-hit-within-ttl, cache-expired-refetches (time.monotonic mock), invalidate-forces-refetch, invalidate-then-resolve
- Fixed ruff lint issues in lib.py (TYPE_CHECKING block, nested-if simplification) and config.py (unused `Field` import)
- Verified: `pytest tests/ -v` — 13/13 passed, `ruff check` — all clean
- **Commit:** `840580e`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed type annotation for from_env overrides**
- **Found during:** Task 1 implementation
- **Issue:** `**overrides: str` would fail type checking for int/bool config fields (timeout, ssl_verify, schema_ttl)
- **Fix:** Changed to `**overrides: Any` — pydantic-settings handles type coercion at runtime
- **Files modified:** `src/graphql_mcp/adapters/inbound/lib.py`
- **Commit:** `840580e` (included with Task 2)

**2. [Rule 1 - Bug] Fixed ruff lint violations in created files**
- **Found during:** Task 2 verification
- **Issue:** Unused `Field` import in config.py, empty TYPE_CHECKING block in lib.py, nested-if statements, unsorted imports in test files
- **Fix:** Removed unused import, moved SchemaGraph/SchemaSource to TYPE_CHECKING block, flattened nested-if to combined conditions, ran `ruff check --fix` on tests
- **Files modified:** `src/graphql_mcp/config.py`, `src/graphql_mcp/adapters/inbound/lib.py`, `tests/conftest.py`, `tests/test_schema_cascade.py`, `tests/test_ttl_cache.py`
- **Commit:** `840580e`

## Verification Results

- `from graphql_mcp import GraphQLClient` — PASS
- `GraphQLClient.from_env()` returns client with SchemaService — PASS
- `python -m pytest tests/ -v` — 13/13 passed (0.08s) — PASS
- `ruff check src/ tests/` (our files) — all checks passed — PASS
- Domain purity: zero I/O imports in domain/ and ports/ — PASS (3 tests)
- Cascade: fallback None→exception→None→success — PASS (6 tests)
- TTL cache: cached within TTL, re-fetched after expiry, re-fetched after invalidate — PASS (4 tests)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `**overrides: Any` (not `str`) for from_env() | Config has int/bool fields; pydantic-settings coerces at runtime; `Any` avoids false type errors |
| TYPE_CHECKING block for domain imports in lib.py | Satisfies ruff TC001 rule; domain types only needed for annotations |
| MockSchemaSource as class (not Protocol mock) | Simpler, explicitly satisfies SchemaSource protocol via duck typing, tracks call_count |

## Self-Check: PASSED
