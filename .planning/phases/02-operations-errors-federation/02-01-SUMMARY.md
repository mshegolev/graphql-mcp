---
phase: 02-operations-errors-federation
plan: 01
subsystem: adapters/outbound
tags: [query-guard, schema-analyzer, federation, mutation-detection, SDL-parsing]
dependency_graph:
  requires: [domain/models, domain/errors, graphql-core]
  provides: [query_guard.contains_mutation, query_guard.check_mutation_guard, SchemaAnalyzer]
  affects: [GraphQLClient (plan 02 wiring)]
tech_stack:
  added: []
  patterns: [SDL-hash caching, AST-based mutation detection, join__Graph federation parsing]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/query_guard.py
    - src/graphql_mcp/adapters/outbound/schema_analyzer.py
    - tests/test_query_guard.py
    - tests/test_schema_analyzer.py
  modified:
    - tests/conftest.py
decisions:
  - "AST parse (not regex) for mutation detection — graphql-core OperationType.MUTATION"
  - "Unparseable queries return False — server-side validation decides"
  - "SDL-hash caching via SHA-256 to avoid redundant build_schema() calls"
  - "build_schema fallback to assume_valid_sdl=True for supergraph SDL"
  - "Dual validation for supergraph: join__Graph enum AND @join__graph directive both required"
metrics:
  duration: 5m
  completed: "2026-06-05T21:13:00Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 25
  tests_total: 38
  files_created: 4
  files_modified: 1
---

# Phase 02 Plan 01: Query Guard & Schema Analyzer Summary

**One-liner:** AST-based mutation detection via graphql-core parse + SDL→domain model analyzer with federation subgraph extraction and SHA-256 caching

## What Was Built

### query_guard.py — Mutation Detection via AST Parse
- `contains_mutation(query_str)` → parses with `graphql.parse()`, checks `OperationType.MUTATION` on each definition
- `check_mutation_guard(query_str)` → raises `MutationGuardError` if mutation detected
- Subscriptions pass through (not blocked); unparseable/empty strings return `False`
- Threat T-02-01 mitigated: uses AST parse (not regex) for reliable mutation detection

### schema_analyzer.py — SDL Parsing into Domain Models
- `SchemaAnalyzer.build_summary(sdl)` → `SchemaSummary` with query fields and types (builtins excluded)
- `SchemaAnalyzer.describe_type(sdl, type_name)` → `TypeInfo` with fields, args, and subgraph ownership
- `SchemaAnalyzer.list_subgraphs(sdl)` → `list[Subgraph]` from supergraph SDL via `join__Graph` enum + `@join__type` directives
- SHA-256 hash caching prevents redundant `build_schema()` calls (Threat T-02-04 mitigated)
- `build_schema` fallback to `assume_valid_sdl=True` handles supergraph SDL with duplicate directives
- Threat T-02-03 mitigated: validates BOTH `join__Graph` enum AND `@join__graph` directive presence

### Test Infrastructure
- `SAMPLE_SUPERGRAPH_SDL` constant added to `tests/conftest.py` with join__Graph enum, @join__graph directives, and @join__type type ownership

## Domain Purity
- All graphql-core imports confined to `adapters/outbound/` — `domain/` and `ports/` remain pure
- Verified via `grep -r "from graphql " src/graphql_mcp/domain/ src/graphql_mcp/ports/` → empty

## Test Results

| Suite | Tests | Status |
|-------|-------|--------|
| test_query_guard.py | 10 | All pass |
| test_schema_analyzer.py | 15 | All pass |
| Existing (domain_purity, cascade, TTL) | 13 | All pass |
| **Total** | **38** | **All pass** |

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | e3c3b8d | feat(02-01): add mutation detection via graphql-core AST parse |
| 2 | 071d06c | feat(02-01): add SchemaAnalyzer with SDL parsing and federation support |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Ruff SIM110 lint violation in query_guard.py**
- **Found during:** task 1
- **Issue:** `for` loop with early return flagged by ruff as replaceable with `any()`
- **Fix:** Replaced `for/if/return` with `return any(...)` generator expression
- **Files modified:** src/graphql_mcp/adapters/outbound/query_guard.py
- **Commit:** e3c3b8d

**2. [Rule 1 - Bug] Ruff I001 + E501 lint violations in schema_analyzer.py and conftest.py**
- **Found during:** task 2
- **Issue:** Import block unsorted (I001); SDL string line > 120 chars (E501)
- **Fix:** Auto-sorted imports via `ruff --fix`; rewrote SAMPLE_SUPERGRAPH_SDL as string concatenation (removed @link directives that were not needed for federation detection)
- **Files modified:** src/graphql_mcp/adapters/outbound/schema_analyzer.py, tests/conftest.py
- **Commit:** 071d06c

## Requirements Addressed

| Requirement | Coverage |
|-------------|----------|
| GQL-03 | Partial — mutation detection + guard ready; wiring into client deferred to plan 02 |
| GQL-04 | Partial — SDL→SchemaSummary ready; client.introspect() wiring deferred to plan 02 |
| GQL-05 | Partial — describe_type() with subgraph ready; client.describe_type() wiring deferred to plan 02 |
| GQL-08 | Partial — list_subgraphs() with name/url/owned_types ready; client.list_subgraphs() wiring deferred to plan 02 |

## Self-Check: PASSED
