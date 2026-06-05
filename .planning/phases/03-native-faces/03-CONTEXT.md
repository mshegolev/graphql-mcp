# Phase 3: Native & Faces - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart discuss skipped)

<domain>
## Phase Boundary

The pyo3 JsonCodec crate builds via maturin, the orjson fallback passes the same parity test, and all four inbound adapters (lib, mcp_stdio, FastAPI REST+MCP-over-HTTP, CLI) expose the full operation set.

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase.

Key constraints:
- D5: Python core + Rust hot paths (pyo3/maturin); pure-Python orjson fallback
- D8: FastAPI primary face (k8s/team sharing); stdio second (Glama + local agent)
- D9: Rust JsonCodec via pyo3; orjson fallback; parity under test; maturin CI
- Library-first: `from graphql_mcp import GraphQLClient` works without MCP/FastAPI

Phase 1-2 established:
- GraphQLClient with all 6 operations (query, raw, introspect, describe_type, list_subgraphs, refresh_schema)
- 60 tests passing
- Hexagonal architecture with domain purity

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- GraphQLClient (adapters/inbound/lib.py) — fully operational library facade
- JsonCodec port (ports/json_codec.py) — Protocol interface ready for implementation
- HttpTransport — httpx-based with 3-class error typing
- All 6 operations wired and tested

### Integration Points
- JsonCodec port needs Rust (pyo3) and orjson implementations
- Inbound adapters: MCP stdio, FastAPI, CLI all delegate to GraphQLClient
- native/src/lib.rs has a stub pymodule ready for implementation

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
