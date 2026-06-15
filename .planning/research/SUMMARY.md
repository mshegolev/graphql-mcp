# Project Research Summary

**Project:** graphql-mcp v2.0 "Production-Grade Platform"
**Domain:** MCP brick — read-only GraphQL client with hexagonal architecture, 4 inbound faces
**Researched:** 2026-06-16
**Confidence:** HIGH

## Executive Summary

graphql-mcp v2.0 transforms a feature-complete read-only GraphQL client brick into a production-grade platform. The research confirms that all five target capabilities — OpenTelemetry observability, security hardening, GraphQL subscriptions, DX/CI pipeline, and Copier template extraction — can be delivered using mature, well-documented libraries with minimal architectural disruption. The existing hexagonal architecture (domain → ports → adapters) is the primary enabler: every v2.0 feature integrates as new adapters or decorator wrappers, with **zero changes to the domain layer** and **zero changes to existing port contracts**. This is a rare position of strength — the v1.x architecture was built exactly right for this evolution.

The recommended approach follows a strict dependency-driven build order: OTEL first (so everything else is observable from day one), security second (harden before exposing new attack surface), subscriptions third (the highest-complexity feature, built on secure+traced transports), DX/CI fourth (requires stable API), and Copier template last (requires final architecture). All new dependencies ship as **optional extras** (`pip install graphql-mcp[otel,security,subscriptions]`), preserving the core library's minimal footprint.

The primary risk is subscription implementation complexity — the `graphql-transport-ws` protocol is a stateful bidirectional protocol with connection lifecycle management, backpressure, and keepalive concerns. This is the only HIGH-risk feature. Everything else follows established patterns with verified libraries. A secondary risk is the Copier template boundary design — separating generic brick skeleton from GraphQL-specific domain requires careful judgment. Both risks are manageable with proper phase planning and integration testing.

## Key Findings

### Recommended Stack

All v2.0 dependencies are optional extras. The core library (`from graphql_mcp import GraphQLClient`) remains unchanged. See [STACK.md](./STACK.md) for full version matrix and rationale.

**New dependencies by feature group:**

| Extra | Packages | Install Footprint |
|-------|----------|-------------------|
| `otel` | `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-exporter-otlp-proto-http`, `opentelemetry-instrumentation-fastapi`, `opentelemetry-instrumentation-httpx` (all `>=1.42,<2` / `>=0.63b0`) | Lightweight — HTTP exporter avoids grpcio's ~35 MB binary |
| `security` | `truststore>=0.10,<1`, `slowapi>=0.1.10,<1` | Minimal — mTLS uses stdlib `ssl.SSLContext`, token rotation uses existing `httpx.Auth` |
| `subscriptions` | `websockets>=14,<17`, `sse-starlette>=3.4,<4` | Small — gql already uses `websockets`; Starlette WS is built-in |
| `dev` (addition) | `pytest-xdist>=3.5` | Test parallelism for growing suite |

**Critical stack decisions:**
- **OTLP HTTP over gRPC**: Avoids `grpcio` binary dependency, simpler cibuildwheel matrix
- **No JWT validation**: Brick is a client/proxy that *forwards* tokens, not a service that validates them
- **No Ariadne/Strawberry**: Brick is not a GraphQL server — full frameworks are architectural overreach
- **Copier not Cookiecutter**: `copier update` enables re-applying template improvements to sister bricks

### Expected Features

See [FEATURES.md](./FEATURES.md) for full feature table with complexity/risk/confidence ratings.

**Must have (table stakes — T1–T10):**
- **T1–T5**: OTEL tracing (inbound + outbound), metrics (count/latency/errors), log correlation, OTLP export
- **T6**: Query depth/complexity validation (prevents adversarial queries from OOMing upstream)
- **T7**: Rate limiting on REST face (prevents capacity exhaustion)
- **T8**: RBAC header passthrough (`Authorization`, `X-User-Id`, `X-Roles` forwarded to upstream)
- **T9**: PyPI publish CI with OIDC Trusted Publishing (sister bricks need `pip install`)
- **T10**: Copier template extraction (reference brick → reusable skeleton)

**Differentiators (D1–D7):**
- **D1**: WebSocket subscriptions (`graphql-transport-ws` protocol) — real-time data streaming
- **D2**: SSE fallback for subscriptions (corporate proxy environments)
- **D3**: mTLS for outbound connections (enterprise deployments)
- **D4**: Token rotation (OAuth2 client_credentials, automatic refresh)
- **D5**: Structured audit logging (who queried what, with trace correlation)
- **D6**: Integration test harness + SDK examples
- **D7**: `AsyncGraphQLClient.subscribe()` → `AsyncIterator[QueryResult]`

**Anti-features (explicitly NOT building):**
- GraphQL server/resolver execution (A1), schema composition (A2), mutation by default (A3)
- Query result caching (A4), multi-endpoint routing (A5), built-in Prometheus scrape endpoint (A6)
- WS-based MCP transport (A7), Python 3.9 support (A8)

### Architecture Approach

The v1.x hexagonal architecture absorbs all v2.0 features cleanly. See [ARCHITECTURE.md](./ARCHITECTURE.md) for full component analysis and dependency graphs.

**Integration strategy by feature:**

| Feature | Integration Pattern | Architecture Layer |
|---------|--------------------|--------------------|
| OTEL | Transport decorator (`TracedTransport`) wrapping existing ports | Outbound adapter (cross-cutting) |
| Security (mTLS, tokens) | SSL context + token provider injection via constructor | Outbound adapter + config |
| Security (rate limit, audit) | FastAPI middleware chain | Inbound adapter |
| Subscriptions | New port (`SubscriptionTransport`) + new inbound/outbound adapters | All layers (port + 3 adapters) |
| DX/CI | GitHub Actions workflows, examples directory | Peripheral (no architecture) |
| Copier | Separate template repo; graphql-mcp is a clean instance | External |

**New files: 13 | Modified files: 9 | Domain/ports unchanged: all existing contracts preserved**

**Major architectural components for v2.0:**
1. **Telemetry layer** (`adapters/outbound/telemetry.py`, `traced_transport.py`) — OTEL bootstrap + transport decorator
2. **Security layer** (`tls_config.py`, `token_refresh.py`, `middleware/rate_limit.py`, `middleware/audit_log.py`) — layered across transport + middleware
3. **Subscription layer** (`ports/subscription.py`, `ws_subscription.py`, `ws_handler.py`, `sse_handler.py`) — new port + 3 adapters
4. **CI/CD layer** (`.github/workflows/publish.yml`) — PyPI Trusted Publishing pipeline

### Critical Pitfalls

> Note: PITFALLS.md was not produced as a separate document. Pitfalls are synthesized from anti-patterns identified across STACK.md, FEATURES.md, and ARCHITECTURE.md.

1. **OTEL leaking into domain** — Importing `opentelemetry` in `domain/` or `ports/` violates hexagonal purity and makes domain untestable without OTEL SDK. **Prevention:** Decorator pattern in `adapters/outbound/`; domain stays clean. Verify with `grep -r "opentelemetry" src/graphql_mcp/domain/` = zero hits.

2. **WebSocket handler conflating protocol + business logic** — A monolithic `ws_handler.py` implementing both `graphql-transport-ws` protocol AND query validation/routing. **Prevention:** Protocol handling in outbound adapter (`ws_subscription.py`); inbound handler is a thin bridge that delegates.

3. **Subscription polling masquerading as real-time** — Implementing subscriptions as periodic `query()` calls defeats the purpose. **Prevention:** Proper WebSocket connection to remote GraphQL server using `graphql-transport-ws` protocol with persistent connection.

4. **Per-worker rate limiter state divergence** — Module-level rate limiter dict shared across uvicorn worker forks means each worker has independent limits. **Prevention:** Accept per-worker limiting for single-brick deployment; document Redis backend option for multi-worker scenarios.

5. **Copier template with hardcoded `graphql_mcp` references** — Generated `kafka-mcp` would have `graphql_mcp` imports. **Prevention:** Thorough Jinja2 parameterization audit (`{{module_name}}`, `{{client_class_name}}`); integration test: generate + import + run tests on generated project.

6. **slowapi incompatibility with WebSocket endpoints** — slowapi does NOT support WebSocket rate limiting. **Prevention:** Use asyncio semaphore per client IP for WS connection limiting; slowapi only on REST routes.

## Implications for Roadmap

Based on combined research, the following 5-phase structure is recommended. The ordering follows a strict dependency chain: observability → security → subscriptions → polish → template.

### Phase 1: OpenTelemetry Observability
**Rationale:** Everything else benefits from tracing and metrics. Without OTEL, debugging subscriptions or security issues is flying blind. Lowest risk, most well-understood feature set. Auto-instrumentation libraries make this fast.
**Delivers:** Full distributed tracing (inbound + outbound), custom metrics (query count/latency/errors by error_class), log correlation (trace_id + span_id in structured logs), OTLP export to suite's Jaeger/Prometheus.
**Addresses:** T1, T2, T3, T4, T5
**New files:** `adapters/outbound/telemetry.py`, `adapters/outbound/traced_transport.py`, `ports/telemetry.py` (optional)
**Modified:** `config.py`, `lib.py`, `async_lib.py`, `rest.py`, `cli.py`
**Avoids:** OTEL-in-domain pitfall (decorator pattern enforced)
**Estimated effort:** ~2 days | **Risk:** LOW

### Phase 2: Security Hardening
**Rationale:** Security must come before exposing new attack surface (subscriptions add WebSocket endpoints). mTLS and token rotation affect the transport layer that subscriptions will build upon. Rate limiting protects existing REST surface immediately.
**Delivers:** Query depth/complexity validation, rate limiting, RBAC header passthrough, mTLS outbound connections, token rotation (OAuth2 client_credentials), structured audit logging.
**Addresses:** T6, T7, T8, D3, D4, D5
**New files:** `tls_config.py`, `token_refresh.py`, `middleware/rate_limit.py`, `middleware/audit_log.py`
**Modified:** `config.py`, `http_transport.py`, `async_http_transport.py`, `lib.py`, `async_lib.py`, `rest.py`
**Avoids:** Rate limiter state divergence pitfall; slowapi + WS incompatibility
**Stack used:** `truststore`, `slowapi`, stdlib `ssl.SSLContext`, httpx `Auth` protocol
**Estimated effort:** ~3 days | **Risk:** MEDIUM (header passthrough threading through domain layer)

### Phase 3: GraphQL Subscriptions
**Rationale:** Depends on Phase 1 (tracing subscription streams) and Phase 2 (rate limiting WS connections, auth for WS handshake). Most complex feature — stateful connections, bidirectional protocol, resource lifecycle management. Building on secure+traced transport reduces debugging burden.
**Delivers:** WebSocket subscription proxy (`graphql-transport-ws`), SSE fallback endpoint, `AsyncGraphQLClient.subscribe()` → `AsyncIterator[QueryResult]`, MCP stdio `subscribe_once` tool.
**Addresses:** D1, D2, D7
**New files:** `ports/subscription.py`, `ws_subscription.py`, `ws_handler.py`, `sse_handler.py`
**Modified:** `domain/models.py` (minor), `async_lib.py`, `rest.py`, `mcp_stdio.py`, `config.py`
**Avoids:** Polling-as-subscriptions pitfall; monolithic WS handler pitfall
**Stack used:** `websockets`, `sse-starlette`, gql `WebsocketsTransport`
**Estimated effort:** ~4 days | **Risk:** HIGH (protocol state machine, concurrency, backpressure)

### Phase 4: DX & Ecosystem
**Rationale:** Requires stable API (all features shipped). PyPI publish enables sister bricks to `pip install`. Integration tests validate the full stack. Can partially overlap with Phase 3 if capacity allows.
**Delivers:** PyPI publish workflow (OIDC Trusted Publishing), integration test harness with docker-compose mock, SDK examples directory, CI improvements (coverage gate, parallel tests).
**Addresses:** T9, D6
**New files:** `.github/workflows/publish.yml`, `tests/integration/`, `examples/`
**Modified:** `.github/workflows/ci.yml`, `pyproject.toml`
**Stack used:** `pypa/gh-action-pypi-publish`, `pytest-xdist`
**Estimated effort:** ~2 days | **Risk:** LOW

### Phase 5: Copier Template Extraction
**Rationale:** Template must capture the **final** v2.0 architecture. Doing it earlier means re-extracting after every structural change. This is the capstone phase that multiplies the brick's value across the suite.
**Delivers:** Copier template with Jinja2 variables, conditional features (rust native, subscriptions, OTEL), `copier.yml` questions, generation of kafka-mcp as validation test.
**Addresses:** T10
**Architecture decision:** Separate template repo (recommended in ARCHITECTURE.md) vs in-repo `template/` directory. Recommend separate repo for clean separation.
**Stack used:** `copier>=9.15,<10`
**Avoids:** Hardcoded `graphql_mcp` references pitfall
**Estimated effort:** ~2 days | **Risk:** MEDIUM (template boundary design)

### Phase Ordering Rationale

1. **Dependency chain:** OTEL → Security → Subscriptions follows a strict "build infrastructure before features" discipline. Each layer inherits capabilities from the layer below.
2. **Risk reduction:** The highest-risk feature (subscriptions) is built third, on top of proven, traced, secure transports. Problems are visible via OTEL from the moment subscriptions code is written.
3. **Hexagonal preservation:** All three research documents independently confirm that every feature integrates as adapters/middleware, not domain changes. The build order respects this: config extensions → outbound adapters → inbound adapters → peripheral tooling.
4. **Template last:** Both STACK.md and FEATURES.md flag that Copier extraction must capture final structure. Building it last is unanimously recommended.
5. **DX/CI is parallel-safe:** Phase 4 has no architectural dependencies on Phase 3. Teams with capacity can start publish pipeline work during subscription implementation.

### Research Flags

**Phases likely needing deeper research during planning:**
- **Phase 3 (Subscriptions):** The `graphql-transport-ws` protocol implementation is the most complex feature. The protocol spec is well-documented, but Python client-side implementation patterns (whether to use `websockets` directly or gql's `WebsocketsTransport`) need validation during planning. Connection lifecycle, backpressure, and multi-subscription multiplexing are under-specified in available sources.
- **Phase 5 (Copier Template):** Template boundary design — what's generic brick skeleton vs. GraphQL-specific — needs analysis during planning. Architecture recommends separate template repo, but the exact file-by-file split needs specification.

**Phases with standard patterns (skip research-phase):**
- **Phase 1 (OTEL):** Auto-instrumentation for FastAPI + httpx is one-liner setup. Context7 docs verified. Decorator transport pattern is textbook hexagonal.
- **Phase 2 (Security):** mTLS via `ssl.SSLContext`, token rotation via `httpx.Auth`, rate limiting via `slowapi` — all standard patterns with official documentation verified.
- **Phase 4 (DX/CI):** PyPI Trusted Publishing is a documented GitHub Actions workflow. Standard CI/CD.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | **HIGH** | All package versions verified via `pip index versions` on 2026-06-16. 12/12 packages confirmed on PyPI. HTTP exporter decision validated. |
| Features | **HIGH** | Feature scope is clear. Table stakes vs. differentiators cleanly separated. Complexity and risk ratings cross-validated between FEATURES.md and ARCHITECTURE.md. |
| Architecture | **HIGH** | Full codebase analysis (22 source files). Hexagonal boundaries verified. Decorator/middleware injection patterns confirmed feasible. Zero domain changes required. |
| Pitfalls | **MEDIUM** | No dedicated PITFALLS.md produced. Pitfalls synthesized from anti-pattern sections in ARCHITECTURE.md and exclusion lists in STACK.md/FEATURES.md. Coverage is good but not systematic. |

**Overall confidence:** **HIGH** — Three research documents converge on the same architecture, build order, and technology choices with strong source verification. The missing PITFALLS.md reduces confidence slightly for risk identification but the anti-pattern analysis in ARCHITECTURE.md partially compensates.

### Gaps to Address

- **WebSocket library choice validation:** ARCHITECTURE.md notes MEDIUM confidence on WS outbound (graphql-ws protocol). Need to validate during Phase 3 planning whether to use `websockets` directly or leverage gql 4.0's built-in `WebsocketsTransport` (which already handles protocol negotiation).
- **slowapi vs. in-house middleware:** STACK.md flags slowapi as a possible replacement candidate if its `limits` dependency causes conflicts. Evaluate during Phase 2 planning.
- **MCP stdio subscription semantics:** MCP stdio is request-response, not streaming. `subscribe_once(query, variables, timeout)` is a compromise — define exact API contract during Phase 3 planning.
- **Multi-worker rate limiting:** Per-worker token bucket is acceptable for single-brick deployment but may not suffice under scale. Flag for operational documentation.
- **Template repo location:** Separate template repo vs. in-repo `template/` directory. ARCHITECTURE.md recommends separate; FEATURES.md shows in-repo structure. Resolve during Phase 5 planning.
- **OTEL SDK version compatibility with instrumentation betas:** `opentelemetry-instrumentation-*` packages are `0.63b0` (beta) while SDK is `1.42` (stable). Verify no breaking changes between beta instrumentation and stable SDK during Phase 1.

## Sources

### Primary (HIGH confidence)
- **OpenTelemetry Python SDK:** Context7 `/open-telemetry/opentelemetry.io` — TracerProvider, MeterProvider, OTLP exporters, FastAPI/httpx auto-instrumentation
- **FastAPI WebSocket + SSE:** Context7 `/fastapi/fastapi` — WebSocket handlers, `EventSourceResponse`, SSE streaming
- **Copier template engine:** Context7 `/copier-org/copier` — `copier.yml`, Jinja2 templating, `copier update`, answers file
- **gql WebSocket subscriptions:** Context7 `/graphql-python/gql` — `WebsocketsTransport`, `subscribe()` API
- **sse-starlette:** Context7 `/sysid/sse-starlette` — `EventSourceResponse`, disconnect handling, W3C SSE compliance
- **PyPI Trusted Publishing:** `docs.pypi.org/trusted-publishers/` — OIDC workflow for GitHub Actions
- **PyPI package versions:** `pip index versions` for all 12 new packages, verified 2026-06-16

### Secondary (MEDIUM confidence)
- **graphql-transport-ws protocol:** Protocol spec from `graphql-ws` npm package documentation — message types, error codes, lifecycle
- **httpx SSL/Auth:** Official httpx docs — `ssl.SSLContext` injection, `httpx.Auth` protocol with `auth_flow()` generator
- **Starlette WebSocket:** Context7 `/kludex/starlette` — WebSocketRoute, subprotocol selection

### Tertiary (needs validation)
- **WS outbound implementation pattern:** Whether to wrap `websockets` directly or use gql's `WebsocketsTransport` — needs prototype during Phase 3
- **slowapi long-term viability:** Version <1.0, evaluate if in-house ASGI middleware is lighter — decide during Phase 2

---
*Research completed: 2026-06-16*
*Documents synthesized: STACK.md, FEATURES.md, ARCHITECTURE.md (3/4 — PITFALLS.md not produced)*
*Ready for roadmap: yes*
