# Phase 2: Operations, Errors & Federation - Context

**Gathered:** 2026-06-06
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — smart discuss skipped)

<domain>
## Phase Boundary

All 6 operations are callable through the lib facade and return typed results with correct error classification and federation metadata. This phase delivers: query(), raw(), introspect(), describe_type(), list_subgraphs(), refresh_schema() on GraphQLClient; 3-class error typing (transport/graphql/ok); mutation-guard enforcement; federation ownership mapping (field → subgraph → serviceName); supergraph SDL parsing.

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key constraints inherited from project decisions:
- D2: Library-first; MCP/REST/CLI are thin inbound adapters
- D7: Hexagonal architecture — domain has zero I/O or framework imports
- Mutation-guard is always on unless GRAPHQL_ALLOW_MUTATIONS=true; applies to both query and raw
- _entities tool is explicitly deferred to v2

Phase 1 established patterns:
- Frozen dataclasses for domain models
- typing.Protocol for port interfaces
- SchemaService with cascade and TTL cache
- GraphQLClient as the composition root in adapters/inbound/lib.py

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- GraphQLClient (adapters/inbound/lib.py) — composition root to extend with new methods
- HttpTransport (adapters/outbound/http_transport.py) — already handles query execution with 3-class error typing
- SchemaService (domain/schema_service.py) — schema resolution with cascade and TTL
- Domain models (domain/models.py) — SchemaGraph, QueryResult, TypeInfo, ErrorClass already defined

### Established Patterns
- Domain purity: no I/O imports in domain/ or ports/
- Frozen dataclasses for immutable models
- Protocol-based port interfaces
- httpx for HTTP transport

### Integration Points
- GraphQLClient needs query(), raw(), introspect(), describe_type(), list_subgraphs(), refresh_schema()
- QueryResult already has error_class field for 3-class typing
- TypeInfo already has subgraph field for federation ownership

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

- _entities(representations:) tool — deferred to v2 per spec §3.2

</deferred>

---

*Phase: 02-operations-errors-federation*
*Context gathered: 2026-06-06 via Smart Discuss (infrastructure auto-skip)*
