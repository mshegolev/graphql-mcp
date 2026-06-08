# graphql-mcp v1.1 — Requirements

**Milestone:** v1.1 Production Hardening
**Scope:** Close v1.0 tech debt, add async transport, perf benchmarks, MCP-over-HTTP, serve infrastructure, _entities operation, and remaining spec artifacts.
**Predecessor:** v1.0 MVP (shipped 2026-06-08, 10/10 requirements satisfied)

---

## Requirements

### Tech Debt & Hardening (from v1.0 audit)

- [x] **HARD-01**: Wire `JsonCodec` port into `HttpTransport` via `get_codec()` factory — replace direct `orjson.dumps()`/`orjson.loads()` with codec abstraction so Rust native codec is used in production, not just tests.
- [x] **HARD-02**: Handle `SchemaResolutionError` in all inbound adapters — REST returns 503 with structured body, MCP returns structured error dict, CLI prints clean message and exits 1. No unhandled Python tracebacks.
- [x] **HARD-03**: Resource lifecycle — `GraphQLClient` implements context manager (`__enter__`/`__exit__`) and `close()` method. `HttpTransport.close()` is called on cleanup. `atexit` handler registered for non-context-manager usage.

### Async Transport & Performance

- [x] **PERF-01**: `AsyncHttpTransport` adapter using `httpx.AsyncClient` implementing `GraphQLTransport` protocol (async variant). Passes same behavioral tests as sync transport.
- [ ] **PERF-02**: `AsyncGraphQLClient` — separate class with same 6 operations as `GraphQLClient` but async. Uses `AsyncHttpTransport`. Context manager support (`async with`).
- [x] **PERF-03**: Perf benchmark suite using pytest-benchmark — 100KB and 1MB JSON payloads. Measures codec encode/decode (native vs fallback) and transport round-trip. `EVALUATION.md` documents thresholds. `evaluation.xml` for structured output.

### Inbound Faces & Infrastructure

- [ ] **FACE-01**: `graphql-mcp serve` CLI command — starts FastAPI via uvicorn with configurable host/port (`GRAPHQL_HTTP_HOST`/`GRAPHQL_HTTP_PORT`).
- [ ] **FACE-02**: MCP-over-HTTP (streamable HTTP transport) on FastAPI app — alongside existing REST routes. Uses `mcp` SDK's `StreamableHTTPServerTransport` or equivalent.
- [ ] **FACE-03**: `Dockerfile` — uvicorn default, multi-stage build, health + readiness probes, non-root user.
- [ ] **FACE-04**: `/ready` endpoint — returns 200 only when schema is resolvable (distinguishes from `/health` which always returns 200).

### Federation & Ship

- [ ] **ENT-01**: `_entities(representations:)` pass-through operation — sends `_entities` query to federation gateway, returns typed result. 7th operation on `GraphQLClient` and `AsyncGraphQLClient`. Exposed in all faces.
- [ ] **SHIP-01**: `CHANGELOG.md` covering v1.0 and v1.1 changes.
- [ ] **SHIP-02**: `LICENSE` file (MIT).

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| HARD-01 | Phase 5 | Complete |
| HARD-02 | Phase 5 | Complete |
| HARD-03 | Phase 5 | Complete |
| PERF-01 | Phase 6 | Complete |
| PERF-02 | Phase 6 | Pending |
| PERF-03 | Phase 6 | Complete |
| FACE-01 | Phase 7 | Pending |
| FACE-02 | Phase 7 | Pending |
| FACE-03 | Phase 7 | Pending |
| FACE-04 | Phase 7 | Pending |
| ENT-01 | Phase 8 | Pending |
| SHIP-01 | Phase 8 | Pending |
| SHIP-02 | Phase 8 | Pending |
