# Phase 1: Foundation & Schema Sources - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart discuss skipped)

<domain>
## Phase Boundary

The hexagonal skeleton compiles and the schema cascade resolves a live or offline schema through all four source adapters. This phase delivers: project scaffold (pyproject.toml, Cargo.toml stub, package layout), domain models (SchemaGraph, QueryResult, TypeInfo, ErrorClass), port protocols (SchemaSource, Transport, JsonCodec), outbound adapters (GitLab, introspection, _service{sdl}, file), SchemaService with TTL cache, configuration (GraphQLConfig via pydantic-settings), and the GraphQLClient.from_env() library facade.

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key constraints inherited from project decisions:
- D2: Library-first; MCP/REST/CLI are thin inbound adapters
- D5: Python core + Rust hot paths (pyo3/maturin); pure-Python orjson fallback
- D7: Hexagonal architecture — domain has zero I/O or framework imports
- D9: Rust JsonCodec via pyo3; orjson fallback; parity under test; maturin CI

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- No existing code — greenfield project

### Established Patterns
- No established patterns yet — this phase sets the foundational patterns

### Integration Points
- No existing integration points — this is the first phase

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation-schema-sources*
*Context gathered: 2026-06-06 via Smart Discuss (infrastructure auto-skip)*
