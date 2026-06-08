# Phase 7: MCP-over-HTTP & Serve Infrastructure - Context

**Gathered:** 2026-06-08
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase)

<domain>
## Phase Boundary

`graphql-mcp serve` starts FastAPI with REST + MCP-over-HTTP. Dockerfile ships production-ready container with health and readiness probes.

</domain>

<decisions>
## Implementation Decisions

### From spec §3.7
- FastAPI is primary face (D8) — REST routes + MCP-over-HTTP + /health + /ready
- `graphql-mcp serve` starts uvicorn
- Dockerfile runs uvicorn by default

### OpenCode's Discretion
- MCP-over-HTTP transport implementation (mcp SDK StreamableHTTPServerTransport or equivalent)
- Dockerfile base image, multi-stage build strategy
- /ready probe implementation (schema availability check)

</decisions>

<code_context>
## Existing Code

Phase 5-6 complete — 204 tests pass. Key files:
- `src/graphql_mcp/adapters/inbound/rest.py` — existing FastAPI app (7 routes: health, query, raw, introspect, type, subgraphs, refresh)
- `src/graphql_mcp/adapters/inbound/mcp_stdio.py` — existing MCP stdio adapter
- `src/graphql_mcp/adapters/inbound/cli.py` — existing CLI with 6 commands
- `src/graphql_mcp/config.py` — existing GraphQLConfig
- No `server.py` exists yet — needs creation as composition root

</code_context>
