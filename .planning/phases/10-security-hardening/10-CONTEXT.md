# Phase 10: Security Hardening - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

The brick rejects adversarial input, rate-limits abusive callers, forwards auth context to upstream, supports enterprise mTLS deployments, automatically refreshes tokens, and produces an audit trail — all without changing the domain layer.

Requirements: SEC-01 (query depth limit), SEC-02 (rate limiting), SEC-03 (header forwarding), SEC-04 (mTLS), SEC-05 (OAuth2 token rotation), SEC-06 (audit logging).

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Key architectural guidelines:

- All security middleware goes in adapters layer — domain/ports remain I/O-free
- Query depth analysis uses graphql-core AST (already a dependency)
- Rate limiting via in-memory sliding window (no external Redis dependency) — configurable via GRAPHQL_RATE_LIMIT env var
- Header forwarding in REST adapter — X-Forwarded-* pattern, Authorization passthrough
- mTLS via httpx ssl_context configuration from env vars (GRAPHQL_CLIENT_CERT, GRAPHQL_CLIENT_KEY, GRAPHQL_CA_BUNDLE)
- OAuth2 client_credentials with auto-refresh — token cache with expiry tracking
- Audit logging as structured log records (not separate log file) — integrates with OTEL log correlation from Phase 9
- OTEL tracing available for security events (Phase 9 dependency satisfied)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `query_guard.py` already does mutation detection via graphql-core AST — depth analysis can use same approach
- `config.py` with pydantic-settings for env var config — extend for security env vars
- OTEL from Phase 9 — audit logs get trace_id/span_id correlation automatically
- `rest.py` FastAPI app — middleware hooks for rate limiting and header forwarding

### Established Patterns
- Hexagonal architecture: domain/ has zero I/O imports
- Environment-based configuration via pydantic-settings
- Optional features via extras (server, mcp, cli, otel)
- Tests use respx for HTTP mocking

### Integration Points
- `rest.py` — rate limiting middleware, header forwarding middleware, depth limit check
- `http_transport.py` — mTLS ssl_context, OAuth2 token injection
- `async_http_transport.py` — same mTLS/OAuth2
- `config.py` — new security config fields
- `lib.py` / `async_lib.py` — audit logging after operations

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase, discuss skipped.

</deferred>
