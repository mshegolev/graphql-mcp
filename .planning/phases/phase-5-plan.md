# Phase 5: Tech Debt & Error Hardening - Plan

## Goal
All v1.0 tech debt is resolved — codec wired into transport, errors handled cleanly in all adapters, resource lifecycle managed with context manager support.

## Requirements
- HARD-01, HARD-02, HARD-03

## Success Criteria
1. `HttpTransport` uses `get_codec()` for JSON encode/decode — `grep 'orjson.dumps\|orjson.loads' src/graphql_mcp/adapters/outbound/http_transport.py` returns empty (no direct orjson usage). Codec parity tests still pass.
2. When all schema cascade sources fail, REST returns 503 with `{"error": "schema unavailable", ...}`, MCP returns `{"error": "...", "error_class": "schema_unavailable"}`, CLI prints `Error: schema unavailable` and exits 1 — verified by tests.
3. `with GraphQLClient.from_env() as client:` works as context manager. After exiting, `client._transport._client.is_closed` is True. `atexit` handler registered for non-context-manager usage.
4. All existing 128 tests still pass with zero regressions.

## Implementation Plan

### Task 1: Wire codec into HttpTransport
- Replace direct orjson usage with get_codec() factory pattern
- Ensure codec parity tests still pass
- Verify no performance regression

### Task 2: Improve error handling for schema cascade failures
- Implement consistent error responses across all adapters
- Ensure proper HTTP status codes (503 for unavailable schema)
- Standardize error_class values across faces

### Task 3: Add context manager support to GraphQLClient
- Implement __enter__ and __exit__ methods
- Ensure proper resource cleanup
- Add atexit handler for non-context-manager usage

### Task 4: Regression testing
- Run full test suite
- Verify no regressions in existing functionality
- Validate all success criteria are met

## Dependencies
- Phase 4 (v1.0 complete)

## Mode
mvp

## Estimated Effort
2 days