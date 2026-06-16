# graphql-mcp — Roadmap

**Project:** graphql-mcp (Investigation MCP Suite — v2 reference brick)
**Granularity:** Coarse
**Mode:** Yolo

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-06-05) — [details](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Production Hardening** — Phases 5-8 (shipped 2026-06-08)
- 🔵 **v2.0 Production-Grade Platform** — Phases 9-13 (active)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-06-05</summary>

- [x] Phase 1: Foundation & Schema Sources (3/3 plans) — completed 2026-06-05
- [x] Phase 2: Operations, Errors & Federation (2/2 plans) — completed 2026-06-05
- [x] Phase 3: Native & Faces (2/2 plans) — completed 2026-06-05
- [x] Phase 4: Ship (2/2 plans) — completed 2026-06-05

</details>

<details>
<summary>✅ v1.1 Production Hardening (Phases 5-8) — SHIPPED 2026-06-08</summary>

- [x] Phase 5: Tech Debt & Error Hardening (3/3 plans) — completed 2026-06-08
- [x] Phase 6: Async Transport & Perf Benchmarks (3/3 plans) — completed 2026-06-08
- [x] Phase 7: MCP-over-HTTP & Serve Infrastructure (2/2 plans) — completed 2026-06-08
- [x] Phase 8: _entities & Ship v1.1 (2/2 plans) — completed 2026-06-08

</details>

### 🔵 v2.0 Production-Grade Platform (Phases 9-13) — ACTIVE

- [x] **Phase 9: OpenTelemetry Observability** — Distributed tracing, custom metrics, and log correlation across all operations (2/2 plans) — completed 2026-06-16
- [x] **Phase 10: Security Hardening** — Query depth limits, rate limiting, mTLS, token rotation, header forwarding, audit logging (3/3 plans) — completed 2026-06-16
- [x] **Phase 11: GraphQL Subscriptions** — WebSocket + SSE subscription proxy with streaming lib-face support (2/2 plans) — completed 2026-06-16
- [x] **Phase 12: DX & Ecosystem** — PyPI publish pipeline and integration test harness with examples (2/2 plans) — completed 2026-06-16
- [x] **Phase 13: Copier Template Extraction** — Reusable parameterized brick template for the suite (1/1 plans) — completed 2026-06-16

---

## Phase Details

<details>
<summary>✅ v1.0 Phase Details (collapsed)</summary>

_See [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md) for v1.0 phase details._

</details>

<details>
<summary>✅ v1.1 Phase Details (collapsed)</summary>

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

</details>

---

### Phase 9: OpenTelemetry Observability

**Goal**: Every operation through every face is traced, metered, and log-correlated — a developer can follow a single request from REST/MCP inbound through to upstream GraphQL HTTP call in Jaeger, see query metrics in Prometheus, and correlate structured logs by trace ID.
**Depends on**: Phase 8 (v1.1 complete — stable transport and adapter layer to instrument)
**Requirements**: OTEL-01, OTEL-02, OTEL-03, OTEL-04, OTEL-05

**Success Criteria** (what must be TRUE):

1. Outbound HTTP calls to the upstream GraphQL endpoint produce spans with `http.method` and `http.url` attributes, and W3C `traceparent` header is propagated — verified by test asserting span attributes from in-memory exporter.
2. Inbound REST/FastAPI requests produce server spans with `http.server.duration` and `http.server.active_requests` metrics emitted — verified by test asserting spans from FastAPI auto-instrumentation middleware.
3. `graphql_mcp.query.duration` histogram, `graphql_mcp.query.count` counter, and `graphql_mcp.query.errors` counter (broken down by `error_class`) are recorded for every `query()`/`raw()` call — verified by test reading in-memory metric reader.
4. Every structured log record emitted during a traced request contains `otelTraceID` and `otelSpanID` fields — verified by test capturing log output during a traced operation.
5. Setting `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_SERVICE_NAME` env vars configures OTLP HTTP export with no code changes — verified by test initializing TracerProvider from env-based config.

**Plans:** 2 plans

Plans:
- [ ] 09-01-PLAN.md — OTEL bootstrap, outbound tracing, custom metrics (OTEL-01, OTEL-03, OTEL-05)
- [ ] 09-02-PLAN.md — Inbound FastAPI instrumentation, log correlation, integration wiring (OTEL-02, OTEL-04)

**UI hint**: no

---

### Phase 10: Security Hardening

**Goal**: The brick rejects adversarial input, rate-limits abusive callers, forwards auth context to upstream, supports enterprise mTLS deployments, automatically refreshes tokens, and produces an audit trail — all without changing the domain layer.
**Depends on**: Phase 9 (OTEL available — security events are traced and metered from day one)
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04, SEC-05, SEC-06

**Success Criteria** (what must be TRUE):

1. A query exceeding `GRAPHQL_MAX_QUERY_DEPTH` (default 10) is rejected with HTTP 400 before reaching upstream — verified by test sending a deeply nested query and asserting 400 response with depth error message.
2. A caller IP exceeding `GRAPHQL_RATE_LIMIT` (default `100/minute`) receives HTTP 429 with `Retry-After` header — verified by test sending burst requests from a single IP.
3. `Authorization`, `X-User-Id`, and `X-Roles` headers from inbound REST requests are forwarded to the upstream GraphQL endpoint — verified by test asserting headers arrive at mock upstream.
4. When `GRAPHQL_CLIENT_CERT`, `GRAPHQL_CLIENT_KEY`, `GRAPHQL_CA_BUNDLE` are set, outbound connections use mTLS — verified by test connecting to a mock TLS server that requires client certificate.
5. When OAuth2 env vars are configured, the client automatically obtains and refreshes tokens before they expire — verified by test with mock OAuth2 server returning short-lived tokens.
6. When `GRAPHQL_AUDIT_LOG=true`, every operation produces a structured audit log record containing caller identity, query hash, error_class, latency_ms, and trace_id — verified by test asserting log output fields.

**Plans:** 3 plans

Plans:
- [ ] 10-01-PLAN.md — Query depth limiting + rate limiting + header forwarding (SEC-01, SEC-02, SEC-03)
- [ ] 10-02-PLAN.md — mTLS client certificate + OAuth2 token rotation (SEC-04, SEC-05)
- [ ] 10-03-PLAN.md — Structured audit logging (SEC-06)

**UI hint**: no

---

### Phase 11: GraphQL Subscriptions

**Goal**: Consumers can subscribe to real-time GraphQL data through WebSocket, SSE, or the async lib face — the brick proxies subscription streams from upstream with proper lifecycle management, backpressure, and error handling.
**Depends on**: Phase 10 (security hardening complete — WS connections are rate-limited, auth headers forwarded, subscription operations traced and audited)
**Requirements**: SUB-01, SUB-02, SUB-03

**Success Criteria** (what must be TRUE):

1. A WebSocket client connecting to `ws://host/graphql/subscribe` using `graphql-transport-ws` sub-protocol receives `QueryResult` events as `next` messages and clean `complete` on stream end — verified by test with mock WS upstream.
2. An HTTP client can `GET /graphql/subscribe?query=...&variables=...` and receive an SSE event stream with `data:` lines containing JSON `QueryResult` payloads — verified by test reading SSE events from the endpoint.
3. `async for result in client.subscribe(query, variables)` on `AsyncGraphQLClient` yields `QueryResult` objects as an `AsyncIterator` — verified by test iterating results from a mock subscription source.

**Plans:** 2 plans

Plans:
- [ ] 11-01-PLAN.md — WebSocket subscription transport + AsyncGraphQLClient.subscribe() (SUB-01, SUB-03)
- [ ] 11-02-PLAN.md — SSE fallback endpoint on FastAPI (SUB-02)

**UI hint**: no

---

### Phase 12: DX & Ecosystem

**Goal**: External consumers can `pip install graphql-mcp` from PyPI, and developers can validate the full stack locally with a one-command integration test harness.
**Depends on**: Phase 11 (API is stable — all features shipped; publish pipeline and examples cover the final API surface)
**Requirements**: DX-01, DX-02

**Success Criteria** (what must be TRUE):

1. Pushing a `v*` tag to GitHub triggers a GitHub Actions workflow that publishes the package to PyPI using OIDC Trusted Publishing — verified by CI workflow dry-run (`--skip-existing` or test PyPI).
2. `docker compose up` starts a mock GraphQL server harness, and `pytest tests/integration/` passes against it — verified by running the harness and integration suite.
3. `examples/` directory contains runnable SDK usage examples (at minimum: basic query, async query, subscription) with inline documentation — verified by reviewing directory contents.

**Plans:** 2 plans

Plans:
- [x] 12-01-PLAN.md — GitHub Actions publish workflow + SDK examples (DX-01)
- [x] 12-02-PLAN.md — Docker compose integration harness + integration tests (DX-02)

**UI hint**: no

---

### Phase 13: Copier Template Extraction

**Goal**: A developer can generate a new MCP brick from the graphql-mcp skeleton with a single `copier copy` command, choosing which optional features to include, and the generated project passes its own test suite out of the box.
**Depends on**: Phase 12 (final v2.0 architecture is complete — template captures the definitive structure)
**Requirements**: TPL-01

**Success Criteria** (what must be TRUE):

1. `copier copy <template-repo> <new-brick>` prompts for module name, env prefix, and optional features (Rust native, subscriptions, OTEL) and generates a complete project — verified by running the command.
2. The generated project's test suite passes (`pytest` in the generated directory) — verified by generating a test brick and running its tests.
3. No hardcoded `graphql_mcp` or `graphql-mcp` strings remain in the generated project (all parameterized via Jinja2) — verified by grep in generated output.

**Plans**: 1 plan

Plans:
- [x] 13-01-PLAN.md — Copier template extraction with parameterized brick generation (TPL-01)

**UI hint**: no

---

## Progress Table

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation & Schema Sources | v1.0 | 3/3 | Complete | 2026-06-05 |
| 2. Operations, Errors & Federation | v1.0 | 2/2 | Complete | 2026-06-05 |
| 3. Native & Faces | v1.0 | 2/2 | Complete | 2026-06-05 |
| 4. Ship | v1.0 | 2/2 | Complete | 2026-06-05 |
| 5. Tech Debt & Error Hardening | v1.1 | 3/3 | Complete | 2026-06-08 |
| 6. Async Transport & Perf Benchmarks | v1.1 | 3/3 | Complete | 2026-06-08 |
| 7. MCP-over-HTTP & Serve Infrastructure | v1.1 | 2/2 | Complete | 2026-06-08 |
| 8. _entities & Ship v1.1 | v1.1 | 2/2 | Complete | 2026-06-08 |
| 9. OpenTelemetry Observability | v2.0 | 2/2 | Complete | 2026-06-16 |
| 10. Security Hardening | v2.0 | 3/3 | Complete | 2026-06-16 |
| 11. GraphQL Subscriptions | v2.0 | 2/2 | Complete | 2026-06-16 |
| 12. DX & Ecosystem | v2.0 | 2/2 | Complete | 2026-06-16 |
| 13. Copier Template Extraction | v2.0 | 1/1 | Complete | 2026-06-16 |
