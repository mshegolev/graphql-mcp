# Phase 8: _entities & Ship v1.1 - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

`_entities(representations:)` pass-through resolves federation entities. CHANGELOG.md and LICENSE created. server.json/glama.json/README updated. Milestone shipped.

</domain>

<decisions>
## Implementation Decisions

### From user discussion
- _entities is pass-through: send representations to the endpoint, return typed QueryResult
- Not full entity resolution (no routing to specific subgraphs, no recursive resolution)
- 7th operation on both GraphQLClient and AsyncGraphQLClient
- Exposed in all faces: REST, MCP, CLI

### OpenCode's Discretion
- How to construct the _entities query string from representations
- Whether mutation guard should apply (it should NOT — _entities is a query)

</decisions>

<code_context>
## Existing Code

Phase 7 complete — 213 tests pass. Key files:
- `src/graphql_mcp/adapters/inbound/lib.py` — GraphQLClient (6 ops + close)
- `src/graphql_mcp/adapters/inbound/async_lib.py` — AsyncGraphQLClient (6 async ops)
- `src/graphql_mcp/adapters/inbound/rest.py` — FastAPI (8 routes + /mcp)
- `src/graphql_mcp/adapters/inbound/mcp_stdio.py` — MCP stdio (6 tools)
- `src/graphql_mcp/adapters/inbound/cli.py` — CLI (7 commands incl serve)
- `server.json`, `glama.json`, `README.md` — existing shipping artifacts

</code_context>
