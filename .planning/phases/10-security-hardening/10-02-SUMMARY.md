---
phase: 10-security-hardening
plan: 02
subsystem: transport-security
tags: [mtls, oauth2, client-credentials, ssl, token-rotation]
dependency_graph:
  requires: [10-01]
  provides: [mTLS-ssl-context, OAuth2-token-manager, transport-auth]
  affects: [http_transport, async_http_transport, lib, async_lib, config]
tech_stack:
  added: []
  patterns: [thread-safe-token-cache, asyncio-lock, ssl-context-injection, env-driven-auth]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/oauth2.py
    - tests/test_mtls.py
    - tests/test_oauth2.py
  modified:
    - src/graphql_mcp/config.py
    - src/graphql_mcp/adapters/outbound/http_transport.py
    - src/graphql_mcp/adapters/outbound/async_http_transport.py
    - src/graphql_mcp/adapters/inbound/lib.py
    - src/graphql_mcp/adapters/inbound/async_lib.py
decisions:
  - "OAuth2 token injected in post_raw() per-request rather than as a client-level header — ensures automatic refresh on every call"
  - "ssl_context takes precedence over ssl_verify when both provided — allows mTLS without disabling verification"
  - "OAuth2TokenManager owns its httpx.Client and closes it in close() — clean resource lifecycle"
  - "ssl import moved to TYPE_CHECKING block — satisfies ruff TCH003 rule with from __future__ annotations"
metrics:
  duration: "7m 35s"
  completed: "2026-06-16"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 22
  files_created: 3
  files_modified: 5
---

# Phase 10 Plan 02: mTLS Client Certificates & OAuth2 Token Rotation Summary

**One-liner:** mTLS client cert via ssl_context from env vars, OAuth2 client_credentials with thread-safe auto-refresh token cache, injected per-request in both sync/async transports.

## What Was Built

### mTLS Support (SEC-04)
- Added `client_cert`, `client_key`, `ca_bundle` config fields to `GraphQLConfig`
- `from_env()` builds `ssl.SSLContext` when cert+key are configured, passes to transport
- `HttpTransport` and `AsyncHttpTransport` accept `ssl_context` parameter
- When `ssl_context` is provided, it takes precedence over `ssl_verify` for the httpx client

### OAuth2 Client Credentials (SEC-05)
- Created `OAuth2TokenManager` — thread-safe (threading.Lock) token cache with auto-refresh
- Created `AsyncOAuth2TokenManager` — async counterpart using asyncio.Lock
- Tokens are fetched on first call, cached, and automatically refreshed before expiry
- Transport `post_raw()` injects `Authorization: Bearer <token>` per-request
- OAuth2 token overrides static `bearer_token` when both are configured
- Clean resource lifecycle: transport.close() cascades to token manager close()

### from_env() Wiring
- Both `lib.py` and `async_lib.py` `from_env()` methods build mTLS ssl_context and OAuth2 manager when env vars are configured
- Fully env-driven: no code changes needed by consumers

## Task Results

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Config + OAuth2 manager + transport params | `0b124b8` | config.py, oauth2.py, http_transport.py, async_http_transport.py |
| 2 | from_env wiring + tests | `8332c84` | lib.py, async_lib.py, test_mtls.py, test_oauth2.py |

## Test Results

- **22 new tests** added (9 mTLS + 13 OAuth2)
- **278 tests pass** in full suite
- **5 pre-existing OTEL test failures** (unrelated to this plan — FastAPI SERVER span detection and log correlation issues)

### Test Coverage
- Config field reading from env vars (mTLS + OAuth2)
- Transport constructor accepts ssl_context and oauth2
- ssl_context precedence over ssl_verify
- from_env builds ssl_context when cert+key provided
- from_env skips mTLS when only cert (no key) provided
- OAuth2 token fetch on first call
- Token caching within expiry
- Token refresh after expiry
- Client credentials grant format verification
- Scope omission when empty
- Error propagation on token failure
- Default expires_in=3600 when omitted
- OAuth2 token injected into upstream requests
- OAuth2 overrides static bearer_token
- from_env creates OAuth2 manager when all vars set
- from_env skips OAuth2 without token_url

## Deviations from Plan

None — plan executed exactly as written.

## Threat Mitigations Applied

| Threat ID | Mitigation | Status |
|-----------|-----------|--------|
| T-10-06 (Info Disclosure: client_secret) | Read from env var only via pydantic-settings; never logged | ✅ Applied |
| T-10-07 (Spoofing: token endpoint) | token_url uses HTTPS; httpx verifies TLS by default | ✅ Applied |
| T-10-10 (DoS: token refresh failure) | Exception propagates to caller; request fails with TRANSPORT error_class | ✅ Applied |

## Self-Check: PASSED

All files exist, all commits verified.
