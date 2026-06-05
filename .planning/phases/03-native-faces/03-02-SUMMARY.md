---
phase: 03-native-faces
plan: 02
subsystem: inbound-adapters
tags: [fastapi, mcp, cli, click, rest, stdio, adapters]
dependency_graph:
  requires: [graphql_client, domain_models, domain_errors]
  provides: [rest_adapter, mcp_stdio_adapter, cli_adapter]
  affects: [pyproject.toml, adapters.inbound]
tech_stack:
  added: [fastapi, uvicorn, mcp-fastmcp, click]
  patterns: [lazy-singleton, pure-delegation, thin-adapter, testclient]
key_files:
  created:
    - src/graphql_mcp/adapters/inbound/rest.py
    - src/graphql_mcp/adapters/inbound/mcp_stdio.py
    - src/graphql_mcp/adapters/inbound/cli.py
    - tests/test_rest.py
    - tests/test_cli.py
    - tests/test_mcp_stdio.py
  modified:
    - pyproject.toml
decisions:
  - "All adapters use lazy singleton _get_client() pattern for GraphQLClient.from_env() initialization"
  - "CLI uses deferred imports (inside command handlers) for fast startup"
  - "FastAPI rest.py exposes set_client() for test injection without monkeypatching"
  - "MCP stdio adapter exposes all 6 operations as individual tools via FastMCP decorator"
metrics:
  duration: "5m"
  completed: "2026-06-05"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 23
  files_changed: 7
---

# Phase 3 Plan 2: FastAPI REST + MCP stdio + CLI Inbound Adapters Summary

Three thin inbound adapters (FastAPI REST, MCP stdio, Click CLI) as pure delegation layers over GraphQLClient, with optional dependency groups in pyproject.toml and 23-test adapter-specific test suites.

## What Was Built

### FastAPI REST Adapter (`src/graphql_mcp/adapters/inbound/rest.py`)
- `GET /health` → `{"status": "ok"}`
- `POST /graphql/query` → accepts `{query, variables}`, returns `{data, errors, error_class}`
- `GET /graphql/introspect` → returns `SchemaSummary` as JSON
- `GET /graphql/type/{type_name}` → returns `TypeInfo` or 404
- `GET /graphql/subgraphs` → returns list of `Subgraph` dicts
- `POST /graphql/refresh` → clears schema cache, returns `{"status": "refreshed"}`
- `MutationGuardError` mapped to HTTP 403 (T-03-04 mitigation)
- Lazy singleton `_get_client()` + `set_client()` for test injection

### MCP stdio Adapter (`src/graphql_mcp/adapters/inbound/mcp_stdio.py`)
- 6 MCP tools registered via `@mcp.tool()`: query, raw, introspect, describe_type, list_subgraphs, refresh_schema
- Each tool delegates to GraphQLClient, returns `.model_dump()` dicts
- `if __name__ == "__main__": mcp.run(transport="stdio")` for standalone execution
- Lazy singleton pattern matches REST adapter

### Click CLI Adapter (`src/graphql_mcp/adapters/inbound/cli.py`)
- 5 commands: query, introspect, describe-type, list-subgraphs, refresh
- Deferred imports inside command handlers for fast `--help` response
- `describe-type` for missing type exits 1 with stderr message
- All output as pretty-printed JSON to stdout
- Entry point: `graphql-mcp` via `pyproject.toml [project.scripts]`

### pyproject.toml Updates
- `[project.optional-dependencies]` groups: server (fastapi+uvicorn), mcp, cli (click), all (meta-group)
- `[project.scripts]` entry point: `graphql-mcp = graphql_mcp.adapters.inbound.cli:main`
- Dev group extended with `httpx[cli]>=0.28`

### Test Suites
- **test_rest.py** (9 tests): /health, query transport error, mutation 403, introspect, describe-type (found + 404), subgraphs (supergraph + regular), refresh
- **test_cli.py** (6 tests): introspect, describe-type (found + missing), list-subgraphs, refresh, query with no transport
- **test_mcp_stdio.py** (8 tests): server exists, all 6 tools registered, delegation tests for introspect, describe_type, list_subgraphs, refresh_schema, query, raw

## Verification Results

| Check | Result |
|-------|--------|
| `from graphql_mcp.adapters.inbound.rest import app` | ✅ Imports OK |
| `from graphql_mcp.adapters.inbound.mcp_stdio import mcp` | ✅ Imports OK |
| `from graphql_mcp.adapters.inbound.cli import main` | ✅ Imports OK |
| `from graphql_mcp import GraphQLClient` | ✅ Library face unchanged |
| test_rest.py (9 tests) | ✅ All pass |
| test_cli.py (6 tests) | ✅ All pass |
| test_mcp_stdio.py (8 tests) | ✅ All pass |
| Full test suite (128 tests) | ✅ All pass, zero regressions |
| `ruff check` on all new files | ✅ All passed |

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Lazy singleton `_get_client()` in all adapters | Defers `from_env()` until first request; avoids startup cost for health checks and test setup |
| CLI deferred imports in command handlers | Fast `--help` response; doesn't load GraphQLClient until command executes |
| `set_client()` public API in rest.py | Explicit test injection without monkeypatching globals; cleaner than fixture-level patches |
| MCP tools as individual functions (not class) | FastMCP `@mcp.tool()` decorator works on module-level functions; matches FastMCP idiom |

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | a0779b1 | feat(03-02): add FastAPI REST, MCP stdio, and CLI inbound adapters |
| 2 | 34d2caf | test(03-02): add test suites for FastAPI, CLI, and MCP stdio adapters |

## Self-Check: PASSED

All 7 files verified present. Both commits (a0779b1, 34d2caf) verified in git log. 128 tests passing. Test files exceed minimum line counts (102/40, 82/30, 90/30).
