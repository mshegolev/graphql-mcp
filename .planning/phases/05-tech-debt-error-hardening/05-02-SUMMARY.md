---
phase: 05-tech-debt-error-hardening
plan: 02
subsystem: inbound-adapters
tags: [error-handling, schema-resolution, tech-debt, HARD-02]
dependency_graph:
  requires: [domain/errors.py (SchemaResolutionError class)]
  provides: [SchemaResolutionError handling in REST/MCP/CLI adapters]
  affects: [rest.py, mcp_stdio.py, cli.py]
tech_stack:
  added: []
  patterns: [FastAPI exception_handler for global error interception, per-tool try/except for MCP, lazy-import + try/except for CLI]
key_files:
  created:
    - tests/test_schema_error_handling.py
  modified:
    - src/graphql_mcp/adapters/inbound/rest.py
    - src/graphql_mcp/adapters/inbound/mcp_stdio.py
    - src/graphql_mcp/adapters/inbound/cli.py
decisions:
  - "FastAPI exception_handler (global) over per-endpoint try/except — cleaner, catches all future endpoints too"
  - "MCP returns dict with error_class key matching existing mutation_blocked pattern"
  - "CLI uses lazy import of SchemaResolutionError inside each command (consistent with existing MutationGuardError pattern)"
metrics:
  duration: "5m 26s"
  completed: "2026-06-08"
  tasks: 2/2
  tests_added: 11
  tests_total: 144
  files_modified: 3
  files_created: 1
---

# Phase 05 Plan 02: SchemaResolutionError Adapter Handling Summary

**One-liner:** Catch SchemaResolutionError in all three inbound adapters — REST returns 503 with structured JSON, MCP returns error dict with `error_class: "schema_unavailable"`, CLI prints clean error and exits 1 — closing tech debt item #2 from v1.0 audit.

## What Was Done

### Task 1: Add SchemaResolutionError handlers to all three adapters (5d256ad)

**REST adapter (`rest.py`):**
- Added `SchemaResolutionError` to imports from `graphql_mcp.domain.errors`
- Added `FastAPI.exception_handler(SchemaResolutionError)` returning `JSONResponse(status_code=503, content={"error": "schema unavailable", "detail": str(exc)})` — global handler, no per-endpoint wrapping needed
- Added `Request` and `JSONResponse` imports from FastAPI

**MCP adapter (`mcp_stdio.py`):**
- Added `SchemaResolutionError` to imports
- Wrapped `introspect()`, `describe_type()`, `list_subgraphs()` with `try/except SchemaResolutionError` returning `{"error": str(exc), "error_class": "schema_unavailable"}`
- Updated `list_subgraphs` return type annotation to `list[dict] | dict`

**CLI adapter (`cli.py`):**
- Added lazy `from graphql_mcp.domain.errors import SchemaResolutionError` in `introspect`, `describe_type`, `list_subgraphs` commands
- Wrapped schema operations with `try/except SchemaResolutionError` → `click.echo(f"Error: {exc}", err=True); sys.exit(1)`

### Task 2: Add tests for SchemaResolutionError handling (35689bf)

Created `tests/test_schema_error_handling.py` with 11 tests across 3 test classes:

| Class | Tests | What's Verified |
|-------|-------|-----------------|
| `TestRESTSchemaError` | 4 | 503 + structured JSON on introspect/describe_type/list_subgraphs; /health still 200 |
| `TestMCPSchemaError` | 3 | Error dict with `error_class == "schema_unavailable"` from all 3 schema tools |
| `TestCLISchemaError` | 4 | Exit code 1, "Error:" message present, no "Traceback" in output |

All tests use a `_failing_client()` helper that configures `MockSchemaSource(should_raise=True)` to guarantee `SchemaResolutionError` on any schema operation.

## Decisions Made

1. **FastAPI `exception_handler` (global) over per-endpoint try/except** — A single exception handler catches `SchemaResolutionError` from any endpoint including future ones. Cleaner than wrapping each endpoint individually.
2. **MCP uses dict return (not exception)** — Follows existing `mutation_blocked` pattern where MCP tools return error dicts rather than raising. `error_class: "schema_unavailable"` gives callers a machine-readable discriminator.
3. **CLI lazy imports inside each command** — Follows the existing `MutationGuardError` pattern. Each command that needs `SchemaResolutionError` imports it locally (CLI commands use lazy imports to keep startup fast).

## Deviations from Plan

None — plan executed exactly as written.

## Threat Mitigations

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-05-03 | REST 500 traceback → 503 with sanitized JSON body | Mitigated |
| T-05-04 | CLI traceback → clean "Error: ..." to stderr | Mitigated |
| T-05-05 | MCP traceback → structured error dict | Mitigated |

## Verification Results

| Check | Expected | Actual |
|-------|----------|--------|
| `SchemaResolutionError` refs in rest.py | >= 2 | 3 |
| `SchemaResolutionError` refs in mcp_stdio.py | >= 4 | 4 |
| `SchemaResolutionError` refs in cli.py | >= 6 | 6 |
| `schema_unavailable` in mcp_stdio.py | 3 | 3 |
| `503` in rest.py | >= 1 | 1 |
| New tests pass | 11/11 | 11/11 |
| Full suite | 133+ | 144 passed |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| `5d256ad` | feat | Handle SchemaResolutionError in all inbound adapters |
| `35689bf` | test | Add SchemaResolutionError handling tests for all adapters |

## Self-Check: PASSED

All files exist. All commits verified. 144 tests passing. No accidental deletions.
