# Phase 12: DX & Ecosystem - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

External consumers can `pip install graphql-mcp` from PyPI, and developers can validate the full stack locally with a one-command integration test harness.

Requirements: DX-01 (PyPI publish via GitHub Actions OIDC), DX-02 (docker compose integration harness + examples).

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Key guidelines:

- GitHub Actions workflow for PyPI publishing using OIDC Trusted Publishing (no API tokens)
- Triggered on v* tag push
- docker-compose.yml with mock GraphQL server for integration testing
- Integration tests in tests/integration/ directory
- Examples in examples/ directory (basic query, async query, subscription)
- No changes to domain layer

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- pyproject.toml with maturin build system
- Existing Dockerfile for container builds
- Existing test infrastructure with pytest

### Established Patterns
- CI wheel matrix already exists for maturin
- Optional extras for different features
- Click CLI for commands

### Integration Points
- .github/workflows/ — new publish workflow
- docker-compose.yml — new integration harness
- tests/integration/ — new integration tests
- examples/ — new example scripts

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
