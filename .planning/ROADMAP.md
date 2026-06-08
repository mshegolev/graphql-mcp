# graphql-mcp — Roadmap

**Project:** graphql-mcp (Investigation MCP Suite — v2 reference brick)
**Granularity:** Coarse
**Mode:** MVP
**Requirements:** HARD-01..03, PERF-01..03, FACE-01..04, ENT-01, SHIP-01..02 (13 total)
**Coverage:** 13/13

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-06-08) — [details](milestones/v1.0-ROADMAP.md)
- 🚧 **v1.1 Production Hardening** — Phases 5-8

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-06-08</summary>

- [x] Phase 1: Foundation & Schema Sources (3/3 plans) — completed 2026-06-05
- [x] Phase 2: Operations, Errors & Federation (2/2 plans) — completed 2026-06-05
- [x] Phase 3: Native & Faces (2/2 plans) — completed 2026-06-05
- [x] Phase 4: Ship (2/2 plans) — completed 2026-06-05

</details>

### 🚧 v1.1 Production Hardening (Phases 5-8)

- [x] Phase 5: Tech Debt & Error Hardening (3 plans) — completed 2026-06-08
  Plans:
  - [x] 05-01-PLAN.md — Wire JsonCodec into HttpTransport via get_codec()
  - [x] 05-02-PLAN.md — Handle SchemaResolutionError in all inbound adapters
  - [x] 05-03-PLAN.md — Add context manager + close() + atexit to GraphQLClient
- [ ] Phase 6: Async Transport & Perf Benchmarks (3 plans)
  Plans:
  - [ ] 06-01-PLAN.md — AsyncHttpTransport + AsyncGraphQLTransport protocol
  - [ ] 06-02-PLAN.md — AsyncGraphQLClient with 6 async operations
  - [ ] 06-03-PLAN.md — Codec perf benchmarks + EVALUATION.md
- [ ] Phase 7: MCP-over-HTTP & Serve Infrastructure
- [ ] Phase 8: _entities & Ship v1.1

---

## Phase Details

### Phase 5: Tech Debt & Error Hardening

**Goal**: All v1.0 tech debt is resolved — codec wired into transport, errors handled cleanly in all adapters, resource lifecycle managed with context manager support.
**Mode:** mvp
**Depends on**: Phase 4 (v1.0 complete)
**Requirements**: HARD-01, HARD-02, HARD-03

**Success Criteria** (what must be TRUE):

1. `HttpTransport` uses `get_codec()` for JSON encode/decode — `grep 'orjson.dumps\|orjson.loads' src/graphql_mcp/adapters/outbound/http_transport.py` returns empty (no direct orjson usage). Codec parity tests still pass.
2. When all schema cascade sources fail, REST returns 503 with `{"error": "schema unavailable", ...}`, MCP returns `{"error": "...", "error_class": "schema_unavailable"}`, CLI prints `Error: schema unavailable` and exits 1 — verified by tests.
3. `with GraphQLClient.from_env() as client:` works as context manager. After exiting, `client._transport._client.is_closed` is True. `atexit` handler registered for non-context-manager usage.
4. All existing 128 tests still pass with zero regressions.

**UI hint**: no

---

### Phase 6: Async Transport & Perf Benchmarks

**Goal**: `AsyncGraphQLClient` passes the same behavioral tests as sync client, and perf benchmarks with thresholds run in CI.
**Mode:** mvp
**Depends on**: Phase 5
**Requirements**: PERF-01, PERF-02, PERF-03

**Success Criteria** (what must be TRUE):

1. `AsyncHttpTransport` using `httpx.AsyncClient` passes the same error classification tests (ok/graphql/transport) as sync `HttpTransport`.
2. `async with AsyncGraphQLClient.from_env() as client:` works; `await client.query(...)` returns `QueryResult` with correct types. All 6 operations available as async methods.
3. pytest-benchmark suite measures codec encode/decode on 100KB and 1MB payloads. Rust native codec is measurably faster than orjson fallback on 1MB (>10% improvement, or documented as I/O-bound if not).
4. `EVALUATION.md` documents benchmark results and thresholds. `evaluation.xml` present for structured output.

**UI hint**: no

---

### Phase 7: MCP-over-HTTP & Serve Infrastructure

**Goal**: `graphql-mcp serve` starts FastAPI with REST + MCP-over-HTTP; Dockerfile ships production-ready container with health and readiness probes.
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: FACE-01, FACE-02, FACE-03, FACE-04

**Success Criteria** (what must be TRUE):

1. `graphql-mcp serve` starts uvicorn with FastAPI app on configurable `GRAPHQL_HTTP_HOST:GRAPHQL_HTTP_PORT` (default `0.0.0.0:8000`). Verified by test that starts/stops server subprocess.
2. MCP-over-HTTP endpoint on FastAPI app accepts streamable HTTP MCP sessions — test client can list tools and call `query` via HTTP MCP transport.
3. `docker build .` succeeds; container runs with `CMD ["graphql-mcp", "serve"]`. `/health` returns 200, `/ready` returns 503 when no schema source configured (graceful degradation).
4. `/ready` returns 200 only when `SchemaService.resolve()` succeeds; returns 503 otherwise. Separate from `/health` which always returns 200.

**UI hint**: no

---

### Phase 8: _entities & Ship v1.1

**Goal**: `_entities(representations:)` pass-through resolves federation entities, remaining spec artifacts published, milestone shipped.
**Mode:** mvp
**Depends on**: Phase 7
**Requirements**: ENT-01, SHIP-01, SHIP-02

**Success Criteria** (what must be TRUE):

1. `client.entities(representations=[{"__typename": "Product", "id": "123"}])` sends `_entities` query to the endpoint and returns typed `QueryResult`. Mutation guard does not block (it's a query).
2. `entities()` is exposed in all faces: `GraphQLClient.entities()`, `AsyncGraphQLClient.entities()`, REST `POST /graphql/entities`, MCP tool `entities`, CLI `graphql-mcp entities`.
3. `CHANGELOG.md` covers v1.0 and v1.1 changes. `LICENSE` file present (MIT).
4. Updated `server.json` lists `entities` tool. `glama.json` updated.

**UI hint**: no

---

## Progress Table

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Schema Sources | v1.0 | 3/3 | Complete | 2026-06-05 |
| 2. Operations, Errors & Federation | v1.0 | 2/2 | Complete | 2026-06-05 |
| 3. Native & Faces | v1.0 | 2/2 | Complete | 2026-06-05 |
| 4. Ship | v1.0 | 2/2 | Complete | 2026-06-05 |
| 5. Tech Debt & Error Hardening | v1.1 | 3/3 | Complete    | 2026-06-08 |
| 6. Async Transport & Perf Benchmarks | v1.1 | 0/3 | Planned | — |
| 7. MCP-over-HTTP & Serve Infrastructure | v1.1 | — | Not Started | — |
| 8. _entities & Ship v1.1 | v1.1 | — | Not Started | — |
