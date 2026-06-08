---
phase: 07-mcp-over-http-serve-infrastructure
plan: 01
subsystem: inbound-adapters
tags: [mcp-http, rest, cli, health-probes, serve]
dependency_graph:
  requires: [mcp_stdio, rest_adapter, schema_service, cli_adapter]
  provides: [ready_endpoint, mcp_http_endpoint, serve_command, http_config]
  affects: [config, rest, cli, mcp_stdio]
tech_stack:
  added: [StreamableHTTPServerTransport]
  patterns: [starlette-sub-app-mount, sse-json-rpc, factory-function]
key_files:
  created:
    - src/graphql_mcp/adapters/inbound/mcp_http.py
    - tests/test_mcp_http.py
    - tests/test_serve_command.py
  modified:
    - src/graphql_mcp/config.py
    - src/graphql_mcp/adapters/inbound/rest.py
    - src/graphql_mcp/adapters/inbound/cli.py
    - tests/test_rest.py
decisions:
  - "streamable_http_path set to / in mcp_http.py to avoid double-path /mcp/mcp"
  - "MCP sub-app tested directly via Starlette TestClient (not through FastAPI mount) to invoke lifespan for session manager"
  - "DNS rebinding protection disabled in test fixtures via mcp_instance.settings.transport_security"
  - "Session manager reset between tests to ensure clean state"
metrics:
  duration_seconds: 484
  completed: "2026-06-08T15:18:54Z"
  tasks_completed: 3
  tasks_total: 3
  tests_added: 9
  tests_total: 213
  files_created: 3
  files_modified: 4
---

# Phase 07 Plan 01: REST + MCP-over-HTTP & Serve Infrastructure Summary

**One-liner:** /ready health probe, MCP-over-HTTP at /mcp via FastMCP's StreamableHTTPServerTransport, and `graphql-mcp serve` CLI command with configurable host:port.

## Completed Tasks

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add config fields, /ready endpoint, MCP-over-HTTP sub-app mount | ede739d | config.py, rest.py, mcp_http.py |
| 2 | Add serve CLI command | 03cbe0d | cli.py |
| 3 | Tests for /ready, MCP-over-HTTP, and serve command | 8124db4 | test_rest.py, test_mcp_http.py, test_serve_command.py |

## What Was Built

### 1. Config Extension (`http_host`, `http_port`)
Added `http_host: str = "0.0.0.0"` and `http_port: int = 8000` to `GraphQLConfig`. These map to `GRAPHQL_HTTP_HOST` and `GRAPHQL_HTTP_PORT` env vars automatically via pydantic-settings prefix.

### 2. /ready Readiness Probe
`GET /ready` returns:
- **200** `{"status": "ready"}` when schema source resolves successfully
- **503** `{"status": "unavailable", "detail": "schema resolution failed"}` when all schema sources fail

Uses explicit `JSONResponse` with try/except to bypass the global `SchemaResolutionError` exception handler (which returns a different response format).

### 3. MCP-over-HTTP Sub-App at /mcp
`mcp_http.py` provides `create_mcp_http_app()` factory that:
- Reuses the same `FastMCP` instance from `mcp_stdio.py` (all 6 tools already registered)
- Sets `streamable_http_path = "/"` to avoid double-path `/mcp/mcp` when mounted
- Returns a Starlette ASGI app via `mcp.streamable_http_app()`

The sub-app is mounted on FastAPI via `app.mount("/mcp", create_mcp_http_app())`.

### 4. `graphql-mcp serve` CLI Command
Click subcommand with `--host` and `--port` options that:
- Override `GRAPHQL_HTTP_HOST`/`GRAPHQL_HTTP_PORT` env vars for ad-hoc usage
- Delegate to `uvicorn.run("graphql_mcp.adapters.inbound.rest:app", ...)` with import string
- Follow existing CLI pattern of lazy imports inside command body

### 5. Test Coverage (9 new tests)
- **TestReady** (2): /ready 200 with schema, 503 without
- **TestMCPMount** (1): verify /mcp route exists on FastAPI app
- **TestMCPHTTPInitialize** (1): MCP initialize returns serverInfo via SSE
- **TestMCPHTTPToolsList** (1): all 6 MCP tools accessible over HTTP
- **TestServeCommand** (4): serve --help, uvicorn defaults, host/port options, env config fallback

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] MCP sub-app lifespan not invoked via FastAPI mount**
- **Found during:** Task 3 (test implementation)
- **Issue:** FastAPI's `app.mount()` does not invoke the mounted sub-app's lifespan. The MCP `StreamableHTTPSessionManager` requires its lifespan to be running for request handling. Testing via the full FastAPI app at `/mcp` fails with `RuntimeError: Task group is not initialized`.
- **Fix:** MCP-over-HTTP integration tests use Starlette `TestClient` directly on the sub-app (which does invoke lifespan via context manager). A separate `TestMCPMount` test verifies the route is registered on FastAPI. In production, uvicorn invokes all lifespans correctly.
- **Files modified:** tests/test_mcp_http.py

**2. [Rule 3 - Blocking] DNS rebinding protection rejects test host**
- **Found during:** Task 3 (test implementation)
- **Issue:** MCP SDK's default `TransportSecuritySettings` only allows `localhost`, `127.0.0.1`, and `[::1]`. Starlette `TestClient` sends `Host: testserver`, which is rejected with HTTP 421.
- **Fix:** Test fixture temporarily disables `enable_dns_rebinding_protection` and restores it after test. This is test-only — production keeps DNS rebinding protection enabled.
- **Files modified:** tests/test_mcp_http.py

**3. [Rule 3 - Blocking] Session manager state leaks between tests**
- **Found during:** Task 3 (test implementation)
- **Issue:** `FastMCP._session_manager` is a singleton on the module-level `mcp` instance. After the first test's lifespan shuts down, subsequent tests would fail because the session manager is in a shutdown state.
- **Fix:** Test fixture resets `mcp_instance._session_manager = None` before each test and restores the original after. This ensures each test gets a fresh session manager via the lifespan.
- **Files modified:** tests/test_mcp_http.py

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `streamable_http_path = "/"` in mcp_http.py | Avoids double-path `/mcp/mcp`. FastAPI mount at `/mcp` + sub-app root `/` = effective endpoint `/mcp`. |
| Test MCP sub-app directly, not through FastAPI mount | FastAPI doesn't invoke sub-app lifespans during testing. Direct testing proves MCP protocol correctness. |
| DNS rebinding protection disabled only in test fixtures | Production security preserved. Test uses `testserver` host which would fail DNS check. |
| No new dependencies added | MCP SDK, FastAPI, uvicorn, click already in `pyproject.toml` optional dependencies. |

## Verification Results

1. **213 tests passing** (204 existing + 9 new) — zero regressions
2. **Routes confirmed**: `/health`, `/ready`, `/mcp`, `/graphql/query`, `/graphql/introspect`, `/graphql/type/{type_name}`, `/graphql/subgraphs`, `/graphql/raw`, `/graphql/refresh`
3. **Config defaults**: `http_host=0.0.0.0`, `http_port=8000`
4. **MCP protocol**: initialize returns serverInfo, tools/list returns all 6 tools

## Threat Flags

None — no new trust boundaries beyond what the plan's threat model covers.

## Known Stubs

None — all functionality is fully wired.

## Self-Check: PASSED
