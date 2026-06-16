---
phase: 10-security-hardening
plan: 03
subsystem: audit-logging
tags: [security, audit, otel, logging, SEC-06]
dependency_graph:
  requires: [10-01, 10-02]
  provides: [structured-audit-logging, otel-trace-correlation]
  affects: [lib-facade, async-lib-facade, rest-adapter]
tech_stack:
  added: []
  patterns: [structured-logging, sha256-query-hash, otel-span-extraction]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/audit.py
    - tests/test_audit_logging.py
  modified:
    - src/graphql_mcp/adapters/inbound/lib.py
    - src/graphql_mcp/adapters/inbound/async_lib.py
    - src/graphql_mcp/adapters/inbound/rest.py
decisions:
  - "SHA-256 query hash (16 hex chars) prevents sensitive data leakage in logs"
  - "Logger 'graphql_mcp.audit' at INFO level integrates with OTEL LoggingInstrumentor"
  - "Caller checks config.audit_log before calling emit_audit_log — keeps function pure"
  - "Instance attributes _audit_caller_ip/_audit_caller_identity initialized in __init__ for type safety"
  - "Audit emitted for both transport-present and no-transport error paths"
metrics:
  duration: 9m 23s
  completed: 2026-06-16
  tasks: 2/2
  tests_added: 13
  tests_total: 258
---

# Phase 10 Plan 03: Structured Audit Logging with OTEL Trace Correlation Summary

Structured audit logging via `emit_audit_log()` emitting SHA-256 query hashes, caller identity, error class, latency, and OTEL trace_id for every query/raw/entities operation when `GRAPHQL_AUDIT_LOG=true`.

## What Was Done

### Task 1: Create audit logging module (376cf85)
Created `src/graphql_mcp/adapters/outbound/audit.py` with:
- `emit_audit_log()` — structured log record with 7 fields: event, caller_ip, caller_identity, operation, query_hash, error_class, latency_ms, trace_id
- `_query_hash()` — SHA-256 hash (first 16 hex chars) to prevent sensitive data leakage
- `_get_trace_id()` — extracts 32-char hex trace_id from current OTEL span, or "none"
- Logger `graphql_mcp.audit` at INFO level for targeted log filtering/routing
- `extra=record` passes structured fields for JSON log formatters

### Task 2: Wire audit logging + tests (3d1f506)
- **lib.py**: Added `emit_audit_log` import, `_audit_caller_ip`/`_audit_caller_identity` instance attributes (initialized in `__init__`), audit emission in `query()`, `raw()`, `entities()` — gated by `self._config.audit_log`
- **async_lib.py**: Same pattern as sync lib — audit emission in all three async operations
- **rest.py**: Set `_audit_caller_ip` (from `request.client.host`) and `_audit_caller_identity` (from `X-User-Id` header) before each client call in `graphql_query`, `graphql_raw`, `graphql_entities`
- **tests/test_audit_logging.py**: 13 tests across 4 classes (230 lines):
  - `TestAuditLogEmission` (6 tests): field validation, hash determinism, defaults, latency precision
  - `TestAuditViaLibFacade` (4 tests): query/raw/entities audit emission, disabled check
  - `TestAuditViaREST` (2 tests): caller_ip from request, X-User-Id as caller_identity
  - `TestAuditWithOTEL` (1 test): real 32-char trace_id when OTEL span is active

## Decisions Made

1. **SHA-256 query hash (T-10-11 mitigation)**: Never log raw queries — hash prevents sensitive variable leakage
2. **Logger name `graphql_mcp.audit`**: Enables targeted log filtering/routing in production
3. **Caller checks config before emit**: `emit_audit_log()` is pure (no config dependency), testable in isolation
4. **Instance attributes over `getattr`**: Declared `_audit_caller_ip`/`_audit_caller_identity` in `__init__` for type safety instead of dynamic `getattr` with defaults
5. **Audit on both code paths**: `start = time.monotonic()` moved before transport check so audit fires for transport errors too (enables complete audit trail)

## Verification Results

- `python -m pytest tests/test_audit_logging.py -x -v` → **13 passed**
- `python -m pytest tests/test_security_middleware.py tests/test_mtls.py tests/test_oauth2.py -x -v` → **38 passed** (Plans 01+02 intact)
- `python -m pytest tests/ --ignore=tests/benchmarks` → **291 passed, 4 pre-existing OTEL instrumentation failures** (SpanKind.SERVER detection and LoggingInstrumentor global state — same failures without our changes)
- `ruff check src/graphql_mcp/` → **0 new errors** (3 pre-existing in otel_bootstrap.py)
- Audit log contains all 7 required fields: caller_ip, caller_identity, operation, query_hash, error_class, latency_ms, trace_id

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Correctness] Audit emission for no-transport path**
- **Found during:** Task 2
- **Issue:** Plan placed audit after `record_query_metrics()` which is only in the transport-present path. Test `test_audit_logged_on_query` constructs with `transport=None` expecting an audit record.
- **Fix:** Moved `start = time.monotonic()` before transport check, restructured both branches to converge on `elapsed`/`record_query_metrics`/`emit_audit_log` — complete audit trail for all operation outcomes.
- **Files modified:** lib.py, async_lib.py
- **Commit:** 3d1f506

**2. [Rule 2 - Type Safety] Declared instance attributes in __init__**
- **Found during:** Task 2
- **Issue:** Plan used `getattr(self, '_audit_caller_ip', 'local')` pattern. LSP reported type errors when REST adapter assigned `client._audit_caller_ip`. 
- **Fix:** Initialized `_audit_caller_ip: str = "local"` and `_audit_caller_identity: str = "anonymous"` in `__init__` for both `GraphQLClient` and `AsyncGraphQLClient`. REST adapter assignments now type-safe.
- **Files modified:** lib.py, async_lib.py
- **Commit:** 3d1f506

## Threat Model Compliance

| Threat ID | Disposition | Status |
|-----------|-------------|--------|
| T-10-11 (Information Disclosure) | mitigate | ✅ SHA-256 query hash — raw queries never logged |
| T-10-12 (Repudiation) | mitigate | ✅ Structured audit trail with caller_ip + caller_identity + trace_id |
| T-10-13 (Tampering) | accept | Accepted — log integrity is infrastructure responsibility |
| T-10-14 (Information Disclosure) | accept | Accepted — X-User-Id validation at gateway layer |

## Self-Check: PASSED

All created files exist. Both commit hashes verified in git log.
