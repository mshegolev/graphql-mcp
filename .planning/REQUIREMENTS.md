# graphql-mcp v2.0 — Requirements

**Milestone:** v2.0 Production-Grade Platform
**Scope:** Observability (OpenTelemetry), security hardening (mTLS, token rotation, rate limiting, audit), GraphQL subscriptions (WebSocket + SSE), DX & ecosystem (PyPI publish, integration tests), Copier template extraction.
**Predecessor:** v1.1 Production Hardening (shipped 2026-06-08, 13/13 requirements satisfied, 229 tests)

---

## Requirements

### Observability

- [ ] **OTEL-01**: User can see distributed traces for all outbound HTTP calls to the upstream GraphQL endpoint, with W3C traceparent propagation — verified by test that checks span export contains `http.method`, `http.url` attributes.
- [ ] **OTEL-02**: User can see server spans for all inbound REST/FastAPI requests, with `http.server.duration` and `http.server.active_requests` metrics — verified by test asserting spans from FastAPI middleware.
- [ ] **OTEL-03**: User can view `graphql_mcp.query.duration` histogram, `graphql_mcp.query.count` counter, and `graphql_mcp.query.errors` counter broken down by `error_class` (transport/graphql/ok) — verified by test recording metrics and asserting counters.
- [ ] **OTEL-04**: User can correlate structured logs with Jaeger traces via `trace_id` and `span_id` fields injected into every log record — verified by test asserting log records contain `otelTraceID` and `otelSpanID`.
- [ ] **OTEL-05**: User can configure OTEL export via standard env vars (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`) with OTLP HTTP exporter — verified by test that initializes TracerProvider with env-based configuration.

### Security

- [ ] **SEC-01**: User can set a maximum query depth limit (`GRAPHQL_MAX_QUERY_DEPTH`, default 10) that rejects deeply nested queries with a 400 error before forwarding to upstream — verified by test with query exceeding depth limit.
- [ ] **SEC-02**: User can rate-limit REST face requests per caller IP (configurable via `GRAPHQL_RATE_LIMIT`, default `100/minute`) with 429 response and `Retry-After` header — verified by test exceeding limit.
- [ ] **SEC-03**: User can pass `Authorization`, `X-User-Id`, and `X-Roles` headers from inbound REST request through to upstream GraphQL endpoint — verified by test asserting headers forwarded to mock upstream.
- [ ] **SEC-04**: User can configure mTLS for outbound connections via `GRAPHQL_CLIENT_CERT`, `GRAPHQL_CLIENT_KEY`, `GRAPHQL_CA_BUNDLE` env vars — verified by test with mock TLS server requiring client certificate.
- [ ] **SEC-05**: User can configure OAuth2 client_credentials token rotation (`GRAPHQL_OAUTH2_TOKEN_URL`, `GRAPHQL_OAUTH2_CLIENT_ID`, `GRAPHQL_OAUTH2_CLIENT_SECRET`) that automatically refreshes expired tokens — verified by test with mock OAuth2 server.
- [ ] **SEC-06**: User can enable structured audit logging (`GRAPHQL_AUDIT_LOG=true`) that records caller identity, query hash, error_class, latency_ms, and trace_id per operation — verified by test asserting log output contains required fields.

### Subscriptions

- [ ] **SUB-01**: User can subscribe to GraphQL subscriptions via WebSocket on `ws://host/graphql/subscribe` using `graphql-transport-ws` sub-protocol, receiving `QueryResult` events as `next` messages — verified by test with mock WS server.
- [ ] **SUB-02**: User can subscribe via SSE fallback endpoint (`GET /graphql/subscribe?query=...&variables=...`) for environments where WebSocket is unavailable — verified by test reading SSE event stream.
- [ ] **SUB-03**: User can call `async for result in client.subscribe(query, variables)` on `AsyncGraphQLClient` to get an `AsyncIterator[QueryResult]` for lib-face streaming — verified by test iterating subscription results.

### DX & Ecosystem

- [ ] **DX-01**: User can `pip install graphql-mcp` from PyPI, published automatically via GitHub Actions OIDC Trusted Publishing on `v*` tag push — verified by CI workflow dry-run.
- [ ] **DX-02**: User can run integration tests via `docker-compose` harness with mock GraphQL server, and find SDK usage examples in `examples/` directory — verified by `docker compose up` + `pytest tests/integration/`.

### Template

- [ ] **TPL-01**: User can run `copier copy <template-repo> <new-brick>` to generate a new MCP brick with parameterized module name, env prefix, and optional features (Rust native, subscriptions, OTEL) — verified by generating a test brick and running its test suite.

---

## Future Requirements (deferred from v2.0 scoping)

_None — all proposed features selected for v2.0._

## Out of Scope

| Feature | Reason |
|---------|--------|
| GraphQL server/resolver execution | Brick is a client/proxy, not a server |
| Schema composition / supergraph building | Belongs in gateway build pipeline |
| Mutation by default | Read-only investigation tool by design |
| Query result caching (Redis/Memcached) | Upstream gateway responsibility |
| Multi-endpoint routing / query splitting | Gateway functionality |
| Built-in Prometheus scrape `/metrics` | Use OTLP push → collector |
| WebSocket-based MCP transport | No standard MCP-over-WS exists |
| Python 3.9 support | EOL; project requires >=3.10 |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| OTEL-01 | Phase 9 | Pending |
| OTEL-02 | Phase 9 | Pending |
| OTEL-03 | Phase 9 | Pending |
| OTEL-04 | Phase 9 | Pending |
| OTEL-05 | Phase 9 | Pending |
| SEC-01 | Phase 10 | Pending |
| SEC-02 | Phase 10 | Pending |
| SEC-03 | Phase 10 | Pending |
| SEC-04 | Phase 10 | Pending |
| SEC-05 | Phase 10 | Pending |
| SEC-06 | Phase 10 | Pending |
| SUB-01 | Phase 11 | Pending |
| SUB-02 | Phase 11 | Pending |
| SUB-03 | Phase 11 | Pending |
| DX-01 | Phase 12 | Pending |
| DX-02 | Phase 12 | Pending |
| TPL-01 | Phase 13 | Pending |
