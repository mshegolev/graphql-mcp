---
phase: 10-security-hardening
plan: 01
subsystem: adapters/inbound, adapters/outbound
tags: [security, rate-limiting, depth-limiting, header-forwarding]
dependency_graph:
  requires: []
  provides: [check_query_depth, RateLimitMiddleware, header_forwarding, extra_headers_kwarg]
  affects: [rest.py, http_transport.py, async_http_transport.py, lib.py, async_lib.py]
tech_stack:
  added: []
  patterns: [sliding-window-rate-limit, ast-depth-analysis, middleware-chain]
key_files:
  created:
    - tests/test_security_middleware.py
  modified:
    - src/graphql_mcp/config.py
    - src/graphql_mcp/domain/errors.py
    - src/graphql_mcp/adapters/outbound/query_guard.py
    - src/graphql_mcp/adapters/inbound/rest.py
    - src/graphql_mcp/adapters/outbound/http_transport.py
    - src/graphql_mcp/adapters/outbound/async_http_transport.py
    - src/graphql_mcp/adapters/inbound/lib.py
    - src/graphql_mcp/adapters/inbound/async_lib.py
    - tests/conftest.py
decisions:
  - "Used graphql-core AST for depth analysis — no new dependencies needed"
  - "Rate limiter uses in-memory sliding window (acceptable for single-instance; T-10-04)"
  - "Header forwarding uses explicit whitelist of 3 headers — no wildcard forwarding (T-10-03, T-10-05)"
  - "Added extra_headers kwarg through transport chain rather than mutating client-level headers"
  - "Added autouse fixture in conftest to reset rate limiter state between tests"
metrics:
  duration: "~9 minutes"
  completed: "2026-06-16"
  tasks_completed: 3
  tasks_total: 3
  test_count: 16
  test_file_lines: 356
  total_tests_passing: 261
---

# Phase 10 Plan 01: Security Middleware Summary

**One-liner:** Query depth limiting via graphql-core AST, IP-based sliding-window rate limiter with 429+Retry-After, and explicit 3-header forwarding (Authorization, X-User-Id, X-Roles) to upstream.

## What Was Done

### Task 1: Config + Depth Analysis
- Added `max_query_depth` (default 10), `rate_limit` (default "100/minute"), `audit_log` (default False) to `GraphQLConfig`
- Added `QueryDepthError` exception to `domain/errors.py` with depth/max_depth attributes
- Implemented `check_query_depth()` in `query_guard.py` using recursive AST traversal with fragment resolution and cycle protection

### Task 2: REST Middleware + Header Forwarding
- Created `RateLimitMiddleware` (Starlette BaseHTTPMiddleware) with sliding-window IP tracking
  - Parses "count/window" rate limit format
  - Returns 429 + Retry-After header when exceeded
  - Exempts /health and /ready probes
- Added `QueryDepthError` exception handler returning 400 with depth info
- Added depth check before `/graphql/query` and `/graphql/raw` dispatch
- Added `_extract_forwarded_headers()` — explicit whitelist of `authorization`, `x-user-id`, `x-roles`
- Added `extra_headers` kwarg to `HttpTransport.execute()`, `post_raw()`, `AsyncHttpTransport.execute()`, `post_raw()`, `GraphQLClient.query()`, `raw()`, `entities()`, `AsyncGraphQLClient.query()`, `raw()`, `entities()` — all backward-compatible (default None)
- Updated all 3 POST endpoints (query, raw, entities) to extract and forward headers

### Task 3: Comprehensive Tests
Created `tests/test_security_middleware.py` with 16 tests across 3 classes:
- **TestQueryDepthLimit** (6 tests): shallow pass, deep reject, configurable limit, raw endpoint, invalid pass-through, fragment depth
- **TestRateLimiting** (5 tests): under-limit, over-limit 429, retry-after header, health exempt, per-IP independence
- **TestHeaderForwarding** (5 tests): auth forwarded, x-user-id/x-roles forwarded, missing not forwarded, raw endpoint, entities endpoint

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed respx mock URL mismatch**
- **Found during:** Task 3
- **Issue:** httpx sends to `https://upstream.test/graphql/` (trailing slash) when base_url is set, but respx mock was for exact URL without slash
- **Fix:** Changed respx mocks to use `url__startswith=` pattern matching
- **Files modified:** tests/test_security_middleware.py

**2. [Rule 1 - Bug] Fixed rate limiter state leaking between tests**
- **Found during:** Task 3 (full suite run)
- **Issue:** Rate limiter uses module-level in-memory state on the FastAPI app singleton, causing 429 errors in unrelated test files
- **Fix:** Added autouse fixture in `tests/conftest.py` to clear rate limiter windows before each test
- **Files modified:** tests/conftest.py
- **Commit:** c79d30d

**3. [Rule 1 - Bug] Fixed TC002 lint violation**
- **Found during:** Task 2 verification
- **Issue:** `ASGIApp` import not needed at runtime, only for type hints
- **Fix:** Moved to `TYPE_CHECKING` block
- **Files modified:** src/graphql_mcp/adapters/inbound/rest.py

## Decisions Made

1. **AST depth analysis over regex** — graphql-core's parser gives us accurate depth even with fragments and inline fragments
2. **In-memory rate limiter** — Acceptable for single-instance deployment (T-10-04: resets on restart). Redis upgrade path exists for HA
3. **Explicit header whitelist** — Only 3 named headers forwarded (T-10-03, T-10-05). No wildcard X-* forwarding
4. **extra_headers through chain** — Additive kwarg at each layer (transport → client → endpoint) instead of mutating client-level httpx headers. Safer for concurrent use

## Verification Results

```
tests/test_security_middleware.py: 16 passed
tests/test_rest.py: 14 passed
tests/test_domain_purity.py: 3 passed
Full suite: 261 passed, 0 failed
ruff check src/graphql_mcp/adapters/inbound/rest.py: All checks passed
```

## Self-Check: PASSED

- [x] `src/graphql_mcp/config.py` — contains `max_query_depth`
- [x] `src/graphql_mcp/domain/errors.py` — contains `QueryDepthError`
- [x] `src/graphql_mcp/adapters/outbound/query_guard.py` — contains `check_query_depth`
- [x] `src/graphql_mcp/adapters/inbound/rest.py` — contains `RateLimitMiddleware`
- [x] `tests/test_security_middleware.py` — 356 lines, 16 tests
- [x] Commit 061a729 exists
- [x] Commit a53ba06 exists
- [x] Commit d8dd80c exists
- [x] Commit c79d30d exists
