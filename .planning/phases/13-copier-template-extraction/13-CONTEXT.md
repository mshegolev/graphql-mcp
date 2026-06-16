# Phase 13: Copier Template Extraction - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

A developer can generate a new MCP brick from the graphql-mcp skeleton with a single `copier copy` command, choosing which optional features to include, and the generated project passes its own test suite out of the box.

Requirements: TPL-01 (copier template with parameterized module name, env prefix, optional features).

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Key guidelines:

- Copier template in a separate `template/` directory within the repo
- copier.yml with questions: module_name, env_prefix, optional features (rust_native, subscriptions, otel)
- Jinja2 templating to replace all graphql_mcp / graphql-mcp / GRAPHQL_ references
- Generated project includes: pyproject.toml, src/ structure, basic tests, Dockerfile, CI
- Verification: generate a test brick, run its test suite, grep for hardcoded strings

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- The entire graphql-mcp project IS the template source
- pyproject.toml structure with extras
- Hexagonal architecture pattern
- Test structure and conftest

### Integration Points
- template/ directory — new Copier template
- copier.yml — template configuration
- Jinja2 templates for all source files

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None.

</deferred>
