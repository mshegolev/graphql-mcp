# Phase 4: Ship - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart discuss skipped)

<domain>
## Phase Boundary

The brick is fully tested, CI produces installable wheels for the complete platform matrix, and the package is discoverable on Glama. This phase delivers: comprehensive pytest suite, ruff compliance, CI workflow with cibuildwheel, README, and Glama publication files.

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase.

Key constraints:
- CI wheel matrix: Linux manylinux+musllinux x86_64+aarch64, macOS arm64+x86_64, Windows AMD64, py3.10–3.12 + sdist
- pip install without Rust toolchain must work (orjson fallback path)
- Glama submission: server.json and glama.json required

Phase 1-3 delivered:
- 128 tests passing (domain purity, cascade, TTL, query guard, schema analyzer, codec parity, operations, REST, CLI, MCP)
- Rust pyo3 JsonCodec + orjson fallback with byte-identical parity
- All 4 inbound adapters operational
- All 10 requirements (GQL-01..10) partially addressed

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- 128 existing tests across 10 test files
- pyproject.toml with maturin build-backend
- All source code in src/graphql_mcp/ (domain, ports, adapters)

### Integration Points
- GitHub Actions CI workflow needed
- README.md at project root
- server.json + glama.json for Glama
- ruff already configured in pyproject.toml

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None — this is the final phase.

</deferred>
