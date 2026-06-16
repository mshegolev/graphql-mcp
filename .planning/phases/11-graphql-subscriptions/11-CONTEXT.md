# Phase 11: GraphQL Subscriptions - Context

**Gathered:** 2026-06-16
**Status:** Ready for planning
**Mode:** Auto-generated (infrastructure phase — discuss skipped)

<domain>
## Phase Boundary

Consumers can subscribe to real-time GraphQL data through WebSocket, SSE, or the async lib face — the brick proxies subscription streams from upstream with proper lifecycle management, backpressure, and error handling.

Requirements: SUB-01 (WebSocket graphql-transport-ws), SUB-02 (SSE fallback), SUB-03 (AsyncGraphQLClient.subscribe AsyncIterator).

</domain>

<decisions>
## Implementation Decisions

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Key architectural guidelines:

- WebSocket proxy using `websockets` library — standard graphql-transport-ws sub-protocol
- SSE endpoint as GET /graphql/subscribe on FastAPI — text/event-stream response
- AsyncGraphQLClient.subscribe() as AsyncIterator[QueryResult] — yields results from upstream subscription
- Upstream subscription connection managed by dedicated transport (websockets client)
- Backpressure via async queue with bounded capacity
- Graceful shutdown: clean complete message on WS, connection close on SSE
- New `[subscriptions]` optional extra in pyproject.toml with websockets dependency

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- AsyncHttpTransport pattern for async transport implementation
- FastAPI app in rest.py — add WebSocket and SSE routes
- QueryResult domain model — subscription results use same type
- OTEL tracing from Phase 9 — subscription operations get traced
- Security from Phase 10 — rate limiting, auth forwarding apply

### Established Patterns
- Hexagonal architecture: domain/ has zero I/O imports
- Behavioral parity between sync/async where applicable
- Optional dependencies via extras
- Tests use respx for HTTP mocking, Starlette TestClient for endpoints

### Integration Points
- rest.py — new WebSocket route and SSE GET route
- async_lib.py — new subscribe() method
- mcp_stdio.py — potential subscribe tool
- config.py — subscription config fields

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase. Refer to ROADMAP phase description and success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — infrastructure phase, discuss skipped.

</deferred>
