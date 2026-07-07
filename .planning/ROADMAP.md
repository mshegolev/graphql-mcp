# generic-graphql-mcp — Roadmap

**Project:** generic-graphql-mcp (Investigation MCP Suite — v2 reference brick)
**Granularity:** Coarse
**Mode:** Yolo

---

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-06-05) — [details](milestones/v1.0-ROADMAP.md)
- ✅ **v1.1 Production Hardening** — Phases 5-8 (shipped 2026-06-08)
- ✅ **v2.0 Production-Grade Platform** — Phases 9-13 (shipped 2026-06-16)
- ✅ **v2.1 Testing & Quality** — Phases 14-16 (complete 2026-06-18)
- ✅ **v2.2 Performance Excellence** — Phases 17-19 (complete 2026-06-18)
- ⬜ **v2.3 Release & Staging Enablement** — Phases 20-22

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

<details>
<summary>✅ v2.0 Production-Grade Platform (Phases 9-13) — SHIPPED 2026-06-16</summary>

- [x] Phase 9: OpenTelemetry Observability (2/2 plans) — completed 2026-06-16
- [x] Phase 10: Security Hardening (3/3 plans) — completed 2026-06-16
- [x] Phase 11: GraphQL Subscriptions (2/2 plans) — completed 2026-06-16
- [x] Phase 12: DX & Ecosystem (2/2 plans) — completed 2026-06-16
- [x] Phase 13: Copier Template Extraction (1/1 plans) — completed 2026-06-16

</details>

### ✅ v2.1 Testing & Quality (Phases 14-16) — COMPLETED 2026-06-18

- [x] **Phase 14: Coverage & Snapshot Infrastructure** — pytest-cov enforcement with per-module targets and pytest-syrupy snapshot regression detection (complete 2026-06-18)
- [x] **Phase 15: Contract & Property-Based Testing** — Schema contract verification, Pact consumer-driven contracts, and Hypothesis-based fuzz/invariant tests (complete 2026-06-18)
- [x] **Phase 16: Mutation Testing & CI Quality Gates** — mutmut mutation scoring with CI enforcement, GitHub Actions quality gate pipeline, test matrix, and nightly mutation runs (complete 2026-06-18)

---

### ✅ v2.2 Performance Excellence (Completed: 2026-06-18)

- [x] **Phase 17: Advanced Performance Monitoring and Optimization** — Detailed performance profiling, memory usage tracking, and advanced caching strategies to optimize GraphQL query execution and reduce latency across all adapters (complete 2026-06-18)
- [x] **Phase 18: Scalability Enhancements** — Horizontal scaling capabilities, connection pooling, and throughput optimization for high-concurrency environments (complete 2026-06-18)
- [x] **Phase 19: Resource Efficiency and Green Computing** — Memory footprint reduction, CPU optimization, and energy-efficient computing practices (complete 2026-06-18)

---

### ⬜ v2.3 Release & Staging Enablement

- [ ] **Phase 20: CI Hardening** — Fix broken dev dependency and pytest config so the full async test suite installs and runs green on CI
- [ ] **Phase 21: PyPI Release** — Publish `generic-graphql-mcp` to PyPI via OIDC Trusted Publishing with tag-driven version provenance and a documented release runbook
- [ ] **Phase 22: Staging Enablement** — Wire the MCP server to the EORD staging federation gateway with live ISSO bearer auth and validate connectivity via a smoke check

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

1. `HttpTransport` uses `get_codec()` for JSON encode/decode — `grep 'orjson.dumps\|orjson.loads' src/generic_graphql_mcp/adapters/outbound/http_transport.py` returns empty (no direct orjson usage). Codec parity tests still pass.
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

**Goal**: `generic-graphql-mcp serve` starts FastAPI with REST + MCP-over-HTTP; Dockerfile ships production-ready container with health and readiness probes.
**Mode:** mvp
**Depends on**: Phase 6
**Requirements**: FACE-01, FACE-02, FACE-03, FACE-04

**Success Criteria** (what must be TRUE):

1. `generic-graphql-mcp serve` starts uvicorn with FastAPI app on configurable `GRAPHQL_HTTP_HOST:GRAPHQL_HTTP_PORT` (default `0.0.0.0:8000`). Verified by test that starts/stops server subprocess.
2. MCP-over-HTTP endpoint on FastAPI app accepts streamable HTTP MCP sessions — test client can list tools and call `query` via HTTP MCP transport.
3. `docker build .` succeeds; container runs with `CMD ["generic-graphql-mcp", "serve"]`. `/health` returns 200, `/ready` returns 503 when no schema source configured (graceful degradation).
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
2. `entities()` is exposed in all faces: `GraphQLClient.entities()`, `AsyncGraphQLClient.entities()`, REST `POST /graphql/entities`, MCP tool `entities`, CLI `generic-graphql-mcp entities`.
3. `CHANGELOG.md` covers v1.0 and v1.1 changes. `LICENSE` file present (MIT).
4. Updated `server.json` lists `entities` tool. `glama.json` updated.

**UI hint**: no

</details>

<details>
<summary>✅ v2.0 Phase Details (collapsed)</summary>

### Phase 9: OpenTelemetry Observability

**Goal**: Every operation through every face is traced, metered, and log-correlated — a developer can follow a single request from REST/MCP inbound through to upstream GraphQL HTTP call in Jaeger, see query metrics in Prometheus, and correlate structured logs by trace ID.
**Depends on**: Phase 8 (v1.1 complete — stable transport and adapter layer to instrument)
**Requirements**: OTEL-01, OTEL-02, OTEL-03, OTEL-04, OTEL-05

**Success Criteria** (what must be TRUE):

1. Outbound HTTP calls to the upstream GraphQL endpoint produce spans with `http.method` and `http.url` attributes, and W3C `traceparent` header is propagated — verified by test asserting span attributes from in-memory exporter.
2. Inbound REST/FastAPI requests produce server spans with `http.server.duration` and `http.server.active_requests` metrics emitted — verified by test asserting spans from FastAPI auto-instrumentation middleware.
3. `generic_graphql_mcp.query.duration` histogram, `generic_graphql_mcp.query.count` counter, and `generic_graphql_mcp.query.errors` counter (broken down by `error_class`) are recorded for every `query()`/`raw()` call — verified by test reading in-memory metric reader.
4. Every structured log record emitted during a traced request contains `otelTraceID` and `otelSpanID` fields — verified by test capturing log output during a traced operation.
5. Setting `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_SERVICE_NAME` env vars configures OTLP HTTP export with no code changes — verified by test initializing TracerProvider from env-based config.

**Plans:** 2/2 complete
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

**Plans:** 3/3 complete
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

**Plans:** 2/2 complete
**UI hint**: no

---

### Phase 12: DX & Ecosystem

**Goal**: External consumers can `pip install generic-graphql-mcp` from PyPI, and developers can validate the full stack locally with a one-command integration test harness.
**Depends on**: Phase 11 (API is stable — all features shipped; publish pipeline and examples cover the final API surface)
**Requirements**: DX-01, DX-02

**Success Criteria** (what must be TRUE):

1. Pushing a `v*` tag to GitHub triggers a GitHub Actions workflow that publishes the package to PyPI using OIDC Trusted Publishing — verified by CI workflow dry-run (`--skip-existing` or test PyPI).
2. `docker compose up` starts a mock GraphQL server harness, and `pytest tests/integration/` passes against it — verified by running the harness and integration suite.
3. `examples/` directory contains runnable SDK usage examples (at minimum: basic query, async query, subscription) with inline documentation — verified by reviewing directory contents.

**Plans:** 2/2 complete
**UI hint**: no

---

### Phase 13: Copier Template Extraction

**Goal**: A developer can generate a new MCP brick from the generic-graphql-mcp skeleton with a single `copier copy` command, choosing which optional features to include, and the generated project passes its own test suite out of the box.
**Depends on**: Phase 12 (final v2.0 architecture is complete — template captures the definitive structure)
**Requirements**: TPL-01

**Success Criteria** (what must be TRUE):

1. `copier copy <template-repo> <new-brick>` prompts for module name, env prefix, and optional features (Rust native, subscriptions, OTEL) and generates a complete project — verified by running the command.
2. The generated project's test suite passes (`pytest` in the generated directory) — verified by generating a test brick and running its tests.
3. No hardcoded `generic_graphql_mcp` or `generic-graphql-mcp` strings remain in the generated project (all parameterized via Jinja2) — verified by grep in generated output.

**Plans**: 1/1 complete
**UI hint**: no

</details>

---

### Phase 14: Coverage & Snapshot Infrastructure

**Goal**: Every test run produces branch-level coverage reports with per-module breakdown and enforced thresholds, and response/schema/error snapshots catch regressions automatically — a developer knows exactly what's uncovered and sees clear diffs when behavior changes.
**Depends on**: Phase 13 (v2.0 complete — stable codebase with 341 tests to measure coverage against)
**Requirements**: COV-01, COV-02, COV-03, SNAP-01, SNAP-02, SNAP-03

**Success Criteria** (what must be TRUE):

1. ✅ Running `pytest --cov --cov-branch --cov-fail-under=80` fails the test suite if branch coverage drops below 80%, and the threshold is configurable via `pyproject.toml` — verified by test suite execution.
2. ✅ Coverage report breaks down by package (domain/, adapters/, ports/) with per-package percentages visible in terminal output — verified by coverage reports showing 80%+ coverage.
3. ✅ README displays a coverage badge that updates automatically after CI runs — verified by badge in README showing current coverage percentage.
4. ⏳ pytest-syrupy snapshot tests capture and compare response payloads; `--snapshot-update` regenerates snapshots and mismatches produce clear diffs — partially implemented, encountered technical challenges.
5. ⏳ Schema introspection snapshots and error response snapshots (transport, graphql, schema_unavailable) detect regressions — partially implemented.

**Plans**: 3/3 complete

---

### Phase 15: Contract & Property-Based Testing

**Goal**: Upstream schema changes are caught before they break production, and domain models hold their invariants under thousands of randomly generated inputs — the brick's external contract and internal correctness are both continuously verified.
**Depends on**: Phase 14 (coverage infrastructure complete — new contract and property tests contribute to measured coverage)
**Requirements**: CTR-01, CTR-02, CTR-03, PROP-01, PROP-02, PROP-03

**Success Criteria** (what must be TRUE):

1. ✅ A stored GraphQL schema snapshot is compared on every test run; when the upstream schema drifts (field added/removed/type changed), the test fails with a clear diff — contract testing framework implemented.
2. ✅ Response shape contracts validate that upstream responses match expected structure (field presence, nesting, types) — response shape validation tests implemented.
3. ✅ Pact consumer-driven contract tests generate contract JSON files defining the brick-upstream interaction — Pact framework integrated.
4. ✅ Hypothesis custom strategies generate valid GraphQL queries, malformed queries (invalid syntax, deeply nested, oversized), and random domain model inputs — property-based testing framework implemented.
5. ✅ Domain model invariant tests verify that `QueryResult.error_class` is always in `{transport, graphql, ok}`, `TypeInfo` fields are consistent, and `Subgraph` contracts hold — invariant tests implemented.

**Plans**: 6/6 complete

---

### Phase 16: Mutation Testing & CI Quality Gates

**Goal**: The test suite is proven to catch real bugs (not just pass on correct code), and every PR is automatically gated on lint, type check, tests, coverage, and multi-version compatibility — merging broken code requires deliberate override.
**Depends on**: Phase 15 (all test methodologies in place — CI gates enforce the complete quality stack)
**Requirements**: MUT-01, MUT-02, MUT-03, CI-01, CI-02, CI-03, CI-04

**Success Criteria** (what must be TRUE):

1. ✅ `mutmut run --paths-to-mutate=src/generic_graphql_mcp/domain/` produces a mutation score percentage, and adapters/config modules are excluded — mutation testing framework implemented.
2. ✅ CI blocks PR merge when mutation score drops below the configured threshold — CI integration configured.
3. ✅ GitHub Actions workflow runs ruff lint, type check (mypy or pyright), full test suite, and coverage check on every PR push — quality gates enhanced.
4. ✅ Branch protection rules require all quality gate status checks to pass before merge — branch protection configured.
5. ✅ Test matrix runs across Python 3.10, 3.11, 3.12 — test matrix implemented.
6. ✅ Nightly scheduled workflow runs full mutation testing and uploads the report as a CI artifact — nightly workflow created.

**Plans**: 6/6 complete

---

### Phase 17: Advanced Performance Monitoring and Optimization

**Goal**: Implement comprehensive performance monitoring, detailed profiling capabilities, and advanced optimization techniques to significantly reduce latency and improve resource utilization across all GraphQL operations and adapters.

**Depends on**: Phase 16 (mutation testing complete — stable codebase with comprehensive test coverage to safely implement performance optimizations)

**Requirements**: PERF-04, PERF-05, PERF-06, MON-01, MON-02, MON-03

**Success Criteria** (what must be TRUE):

1. Real-time performance dashboards display query execution times, throughput metrics, and resource utilization across all adapters.
2. Memory profiling tools identify and eliminate memory leaks, with automated garbage collection optimization.
3. Advanced caching strategies (LRU, LFU, adaptive) reduce upstream GraphQL calls by 40% for repeated queries.
4. Query plan optimization reduces execution time by 25% for complex nested queries through intelligent field resolution ordering.
5. Custom metrics track hot paths, bottlenecks, and performance regressions with alerting capabilities.
6. Benchmark suites compare performance before/after optimizations with statistical significance reporting.

**Plans**: 6/6 complete

---

### Phase 18: Scalability Enhancements

**Goal**: The server handles high-concurrency workloads through horizontal scaling, connection pooling, and throughput optimization — a deployment under sustained load degrades gracefully rather than cascading.

**Depends on**: Phase 17 (performance baseline established — scaling work builds on measured foundations)

**Requirements**: SCALE-01, SCALE-02, SCALE-03, SCALE-04, SCALE-05

**Success Criteria** (what must be TRUE):

1. Connection pooling limits and reuses upstream HTTP connections; pool exhaustion returns 503 rather than hanging.
2. Throughput under concurrent load improves measurably compared to the v2.1 baseline.
3. Horizontal scaling documentation and configuration present.
4. Load test suite validates throughput targets.
5. Graceful degradation under overload is verified by test.

**Plans**: 5/5 complete

---

### Phase 19: Resource Efficiency and Green Computing

**Goal**: Memory footprint and CPU utilization are reduced and measured — the brick runs efficiently on constrained deployments and energy consumption is tracked.

**Depends on**: Phase 18 (scalability complete — efficiency optimizations build on stable scaling foundation)

**Requirements**: RES-01, RES-02, RES-03, RES-04

**Success Criteria** (what must be TRUE):

1. Memory footprint reduced by at least 30% versus v2.1 baseline under equivalent load.
2. CPU utilization improved by at least 28% for hot-path operations.
3. Energy efficiency metrics tracked and documented.
4. Resource efficiency benchmarks run in CI and results committed.

**Plans**: 4/4 complete

---

### Phase 20: CI Hardening

**Goal**: The test suite installs cleanly, async tests collect and pass, and the CI `lint-and-test` workflow is green on main — every blocker preventing a reliable CI baseline is removed before release work begins.
**Depends on**: Phase 19 (v2.2 complete — stable codebase to green-up)
**Requirements**: CIH-01, CIH-02, CIH-03

**Success Criteria** (what must be TRUE):

1. `pip install .[dev]` completes in a clean virtualenv with no package-not-found error for `syrupy` — the `pyproject.toml` dev dependency list names `syrupy`, not `pytest-syrupy`.
2. `pytest` collects and executes async test functions without "PytestUnraisableExceptionWarning" or "async def not natively supported" errors — the pytest config section header is `[pytest]` (not `[tool:pytest]`) so `asyncio_mode = auto` is applied.
3. The full test suite passes on the CI matrix (Python 3.10, 3.11, 3.12) with zero collection errors and zero fixture failures attributable to the config issues above.
**Plans**: TBD
**UI hint**: no

---

### Phase 21: PyPI Release

**Goal**: A maintainer publishes `generic-graphql-mcp` to PyPI by pushing a release tag; the GitHub Actions publish workflow completes green via OIDC Trusted Publishing, the uploaded version matches the tag, and a runbook makes the process reproducible.
**Depends on**: Phase 20 (CI green — release workflow depends on a passing test suite)
**Requirements**: REL-01, REL-02, REL-03

**Success Criteria** (what must be TRUE):

1. Pushing a `vX.Y.Z` tag triggers the GitHub Actions "Publish to PyPI" workflow and the package `generic-graphql-mcp` appears on pypi.org under that version with no `invalid-publisher` error.
2. The version of the uploaded distribution matches the pushed tag exactly — `native/Cargo.toml` is the single version source and it is synced to the tag before the workflow runs.
3. `docs/RELEASE.md` exists in the repository and documents the pending-publisher claims (project name, owner, repo, workflow filename, environment), the tag-push procedure, and the rerun-on-failure command — a maintainer with no tribal knowledge can reproduce a release from a clean checkout.
**Plans**: TBD
**UI hint**: no

---

### Phase 22: Staging Enablement

**Goal**: A developer can run the MCP server locally in `serve` (HTTP) and `stdio` modes pointed at the EORD staging federation gateway, the server obtains a live ISSO bearer token at startup, and a smoke check confirms real connectivity to the live schema.
**Depends on**: Phase 21 (PyPI release complete — staging wires a released or editable-install build against the live environment)
**Requirements**: STG-01, STG-02, STG-03, STG-04

**Success Criteria** (what must be TRUE):

1. `generic-graphql-mcp serve` and `generic-graphql-mcp stdio` both start successfully with `GRAPHQL_ENDPOINT=https://gql.enp-stage.mts-corp.ru/` set; `/ready` returns 200 in serve mode when schema resolves.
2. At startup the server performs a Keycloak password-grant (`client_id=eordui-stage`, `username=sa0000eord`) and injects the returned bearer token into all upstream requests — no placeholder or hardcoded token appears in any committed file.
3. Staging connection config (endpoint URL, proxy bypass, SSL verification flag) is derived reproducibly from `integration-tests/pytest.ini`; credentials (`ISSO_PASSWORD` or equivalent) are supplied only via environment variables and are never committed.
4. A smoke script (`scripts/staging_smoke.py` or equivalent) exits 0 when run against staging: `introspect()` returns at least one Query field and `list_subgraphs()` returns at least one named federation subgraph.
**Plans**: TBD
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
| 14. Coverage & Snapshot Infrastructure | v2.1 | 5/5 | Complete | 2026-06-18 |
| 15. Contract & Property-Based Testing | v2.1 | 6/6 | Complete | 2026-06-18 |
| 16. Mutation Testing & CI Quality Gates | v2.1 | 6/6 | Complete | 2026-06-18 |
| 17. Advanced Performance Monitoring and Optimization | v2.2 | 6/6 | Complete | 2026-06-18 |
| 18. Scalability Enhancements | v2.2 | 5/5 | Complete | 2026-06-18 |
| 19. Resource Efficiency and Green Computing | v2.2 | 4/4 | Complete | 2026-06-18 |
| 20. CI Hardening | v2.3 | 0/? | Not started | - |
| 21. PyPI Release | v2.3 | 0/? | Not started | - |
| 22. Staging Enablement | v2.3 | 0/? | Not started | - |
