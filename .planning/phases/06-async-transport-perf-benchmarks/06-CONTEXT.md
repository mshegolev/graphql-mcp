# Phase 6: Async Transport & Perf Benchmarks - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

AsyncGraphQLClient passes the same behavioral tests as sync client. Perf benchmarks with thresholds run in CI. EVALUATION.md and evaluation.xml present.

</domain>

<decisions>
## Implementation Decisions

### From user discussion
- Separate `AsyncGraphQLClient` class (NOT dual methods on one client)
- `AsyncHttpTransport` using `httpx.AsyncClient`
- Same 6 operations as sync, all async
- Context manager support (`async with`)

### OpenCode's Discretion
- How to share logic between sync and async (abstract base, mixin, or duplicate)
- Benchmark threshold values (document what's measured)

</decisions>

<code_context>
## Existing Code

Phase 5 just completed — 154 tests pass. Key code:
- `src/graphql_mcp/adapters/outbound/http_transport.py` — sync HttpTransport with codec wiring
- `src/graphql_mcp/adapters/inbound/lib.py` — sync GraphQLClient with context manager
- `src/graphql_mcp/ports/transport.py` — GraphQLTransport protocol
- `src/graphql_mcp/adapters/outbound/codec_factory.py` — get_codec() factory

</code_context>
