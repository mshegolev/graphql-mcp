# Phase 5: Tech Debt & Error Hardening - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart discuss skipped)

<domain>
## Phase Boundary

All v1.0 tech debt resolved: codec wired into transport, errors handled cleanly in all adapters, resource lifecycle managed with context manager support.

Three work areas:
1. Wire `get_codec()` into `HttpTransport` — replace direct orjson with codec abstraction
2. Handle `SchemaResolutionError` in REST (503), MCP (structured error), CLI (clean message + exit 1)
3. Add context manager + `close()` to `GraphQLClient`, call `HttpTransport.close()` on cleanup

</domain>

<decisions>
## Implementation Decisions

### From user discussion
- This is brownfield — extend existing code, don't replace it
- All 128 existing tests must continue to pass
- Domain purity must be maintained

### OpenCode's Discretion
Implementation details at OpenCode's discretion — pure infrastructure phase.

Key v1.0 code to modify:
- `src/graphql_mcp/adapters/outbound/http_transport.py` — replace `orjson.dumps()`/`orjson.loads()` with codec
- `src/graphql_mcp/adapters/inbound/rest.py` — add SchemaResolutionError handler (503)
- `src/graphql_mcp/adapters/inbound/mcp_stdio.py` — add SchemaResolutionError handler
- `src/graphql_mcp/adapters/inbound/cli.py` — add SchemaResolutionError handler
- `src/graphql_mcp/adapters/inbound/lib.py` — add `__enter__`/`__exit__`/`close()`

</decisions>

<code_context>
## Existing Code Insights

### v1.0 Tech Debt (from audit)
1. `HttpTransport` uses `orjson.dumps()`/`orjson.loads()` directly (lines ~50, ~67) — should use `JsonCodec` port via `get_codec()` factory
2. `SchemaResolutionError` raised by `SchemaService.resolve()` but never caught by any inbound adapter
3. `HttpTransport.close()` exists but never called — `GraphQLClient` has no `close()` or context manager

### Integration Points
- `codec_factory.get_codec()` returns best available codec (Rust native or orjson fallback)
- `SchemaResolutionError` is in `domain/errors.py`
- `HttpTransport.__init__` creates `httpx.Client`, `close()` calls `self._client.close()`

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond tech debt resolution.

</specifics>

<deferred>
## Deferred Ideas

None — all work items are in scope.

</deferred>
