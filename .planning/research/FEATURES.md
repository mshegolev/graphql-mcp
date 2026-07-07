# Feature Landscape — generic-graphql-mcp v2.0

**Domain:** MCP brick — read-only GraphQL client with schema discovery, federation mapping, 4 inbound faces (lib, MCP stdio, REST/FastAPI, CLI)
**Researched:** 2026-06-16
**Focus:** v2.0 target features — observability, security, subscriptions, DX/CI, template extraction

---

## Table Stakes

Features that any production-grade MCP brick / GraphQL client library **must** have. Missing = not deployable to prod or not adoptable by sister bricks.

| # | Feature | Why Expected | Complexity | Depends On | Notes |
|---|---------|-------------|------------|------------|-------|
| T1 | **OTEL tracing on outbound HTTP** | Every gRPC/HTTP call to the upstream GraphQL endpoint must produce a span. Without this, distributed traces from `investigator` → `generic-graphql-mcp` → upstream gateway have a gap. Industry standard; Jaeger/Tempo already in the suite. | **Low** | httpx transport layer | `opentelemetry-instrumentation-httpx` auto-instruments `httpx.Client`/`AsyncClient`. One-line `HTTPXClientInstrumentor().instrument()` or per-client via `transport=` kwarg. Propagates W3C traceparent automatically. (HIGH confidence — Context7 verified) |
| T2 | **OTEL tracing on inbound REST** | FastAPI face must produce server spans so callers see the brick's latency and status. | **Low** | FastAPI app | `opentelemetry-instrumentation-fastapi` wraps `app` with middleware producing `http.server.duration`, `http.server.active_requests` metrics + per-request spans. (HIGH confidence — Context7 verified) |
| T3 | **OTEL metrics: request count, latency histogram, error rate** | Prometheus/Grafana dashboards need `generic_graphql_mcp.query.duration`, `generic_graphql_mcp.query.count`, `generic_graphql_mcp.query.errors` by `error_class` (transport/graphql/ok). Without metrics, on-call has no SLIs. | **Medium** | OTEL SDK MeterProvider | Manual instrumentation in `query_service.py` / transport layer: `meter.create_histogram("generic_graphql_mcp.query.duration")`, `meter.create_counter("generic_graphql_mcp.query.count")`. Record `error_class` as attribute for per-class breakdown. |
| T4 | **OTEL log correlation** | Structured logs must include `trace_id` + `span_id` so Loki/OpenSearch can link to Jaeger traces. | **Low** | OTEL SDK, stdlib logging | `opentelemetry.instrumentation.logging` or manual `LoggingInstrumentor().instrument()`. Injects `otelTraceID`, `otelSpanID` into `LogRecord`. Current code uses `logging.getLogger()` — compatible. |
| T5 | **OTLP exporter config** | Env-var driven (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`). Must work with the suite's Jaeger + Prometheus OTLP receiver. | **Low** | OTEL SDK | `opentelemetry-exporter-otlp` (already in system). `TracerProvider` + `BatchSpanProcessor(OTLPSpanExporter())`. All config via standard OTEL env vars — zero code for endpoint/protocol selection. |
| T6 | **Input validation / query depth limiting** | Malformed or adversarial queries (deeply nested, excessive aliases) can OOM the upstream. Table stakes for any GraphQL gateway/proxy. | **Medium** | `graphql-core` | `graphql-core` has `validate()` for schema-aware validation. Depth/complexity analysis needs a custom visitor: walk the AST, count nesting depth, reject > N. Also reject introspection in non-dev mode optionally. |
| T7 | **Rate limiting on REST face** | Without it, a single misbehaving caller can exhaust the upstream's capacity. Any public-facing API needs this. | **Low** | FastAPI app | `slowapi` (v0.1.10, actively maintained, MIT, wraps `limits` library). Decorator: `@limiter.limit("100/minute")`. Supports memory/redis backends. **Caveat:** does not support WebSocket endpoints. (HIGH confidence — verified PyPI) |
| T8 | **Bearer token forwarding / RBAC header passthrough** | The brick proxies queries to an authenticated upstream. Must forward `Authorization` headers from inbound caller → outbound transport, not just use a static env-var token. | **Medium** | Transport layer, REST adapter | Add `headers` parameter to `query()` / `raw()` that merges with default headers. FastAPI extracts `Authorization` from inbound request and passes through. Requires threading headers through domain layer (break-the-rules or context-var). |
| T9 | **PyPI publish CI workflow** | Sister bricks (`kafka-mcp`, `ordering-mcp`) and `investigator` need `pip install generic-graphql-mcp`. Without PyPI, they pin to git refs — fragile. | **Medium** | GitHub Actions, cibuildwheel (already built) | Add `publish.yml` triggered on `v*` tag push. Uses existing `wheels` + `sdist` jobs, then `pypa/gh-action-pypi-publish@release/v1`. Needs PyPI API token in repo secrets. Trusted Publishers (OIDC) preferred over static tokens. |
| T10 | **Copier template extraction** | PROJECT.md: "This is the v2 reference brick — its skeleton is copied by kafka-mcp / ordering-mcp." Currently manual copy. Must become `copier copy` with answers file. | **High** | Copier, project structure refactor | `copier.yml` at repo root with Jinja2 templates. Variables: `project_name`, `module_name`, `graphql_or_kafka`, `has_rust_native`. Requires separating graphql-specific domain from generic brick skeleton. `run_update()` for downstream bricks to absorb improvements. (HIGH confidence — Context7 verified) |

## Differentiators

Features that set generic-graphql-mcp apart from "just another GraphQL client." Not expected but high-value.

| # | Feature | Value Proposition | Complexity | Depends On | Notes |
|---|---------|-------------------|------------|------------|-------|
| D1 | **GraphQL Subscriptions via WebSocket** (`graphql-transport-ws` protocol) | Real-time data streaming — investigator can subscribe to order status changes, product catalog events. No other MCP brick offers live subscriptions. | **High** | FastAPI WebSocket, async transport | **Protocol:** `graphql-transport-ws` (sub-protocol), message types: `connection_init` → `connection_ack` → `subscribe` → `next`* → `complete`. Client acts as proxy: accepts WS from caller, opens WS to upstream, relays `next` messages. Must handle: connection_init timeout (4408), duplicate subscriber IDs (4409), ping/pong keepalive, graceful shutdown. New port: `SubscriptionTransport(Protocol)` with `subscribe(query, variables) -> AsyncIterator[QueryResult]`. New inbound adapter: `ws_subscription.py` mounted on FastAPI. (HIGH confidence — full protocol spec verified) |
| D2 | **SSE fallback for subscriptions** | Simpler consumers (curl, browser debug, MCP-over-HTTP) can't do WebSocket. SSE delivers the same subscription stream over plain HTTP. | **Medium** | D1, FastAPI SSE | FastAPI has built-in `EventSourceResponse` (verified in Context7). Each `next` message from upstream WS is yielded as SSE `data:` event. Endpoint: `GET /graphql/subscribe?query=...&variables=...`. Auto-reconnect via `id:` field + `Last-Event-ID` header. |
| D3 | **mTLS for outbound connections** | Enterprise deployments where upstream GraphQL is behind mutual TLS. Brick must present a client certificate. | **Medium** | httpx SSL context | httpx supports `ssl.SSLContext` with `load_cert_chain(certfile, keyfile)` passed via `verify=ctx`. (HIGH confidence — official httpx docs verified). Config: `GRAPHQL_CLIENT_CERT`, `GRAPHQL_CLIENT_KEY`, `GRAPHQL_CA_BUNDLE` env vars. Wired in `HttpTransport.__init__()` and `AsyncHttpTransport.__init__()`. |
| D4 | **Token rotation (automatic refresh)** | Long-running brick instances need token refresh (OAuth2 client_credentials grant). Without it, the brick dies after token expiry. | **Medium** | httpx auth flow | httpx has a `httpx.Auth` protocol with `auth_flow()` generator for custom auth. Build `OAuth2ClientCredentials(Auth)` that caches + refreshes tokens. Config: `GRAPHQL_OAUTH2_TOKEN_URL`, `GRAPHQL_OAUTH2_CLIENT_ID`, `GRAPHQL_OAUTH2_CLIENT_SECRET`. Alternative: simpler header-refresh callback `Callable[[], str]` in the transport constructor. |
| D5 | **Audit logging** | Security teams need to know who queried what. Structured log entry per operation: timestamp, caller identity (from header), query hash, error_class, latency. | **Low** | T3 (metrics), T4 (log correlation) | Middleware in FastAPI that logs `{"event": "graphql_query", "caller": request.headers.get("X-Caller-Id"), "query_hash": sha256(query)[:12], "trace_id": ..., "latency_ms": ..., "error_class": ...}`. Opt-in via `GRAPHQL_AUDIT_LOG=true`. |
| D6 | **SDK examples + integration test harness** | Adoption by sister bricks and external teams. A `tests/integration/` directory with docker-compose bringing up a mock GraphQL server + the brick, running real end-to-end queries. | **Medium** | Docker, pytest | `docker-compose.integration.yml` with a simple `graphql-yoga` or `Apollo Router` mock. `tests/integration/test_e2e.py` exercises all 7 operations. `examples/` directory with usage snippets for lib, MCP, REST faces. |
| D7 | **Streaming response support in lib face** | `AsyncGraphQLClient.subscribe()` returns `AsyncIterator[QueryResult]`, enabling investigator to process events as they arrive without buffering. | **Medium** | D1, async lib face | New method on `AsyncGraphQLClient`: `async def subscribe(self, query, variables) -> AsyncIterator[QueryResult]`. Wraps the WS subscription transport. Sync `GraphQLClient` does NOT get this (subscriptions are inherently async). |

## Anti-Features

Features to explicitly **NOT** build. Tempting but wrong for this brick.

| # | Anti-Feature | Why Avoid | What to Do Instead |
|---|-------------|-----------|-------------------|
| A1 | **GraphQL server / resolver execution** | The brick is a _client/proxy_, not a server. Adding resolvers turns it into a gateway (Apollo Router territory). Massive scope creep. | Forward queries to the upstream. Schema discovery is read-only inspection, not execution. |
| A2 | **Schema composition / supergraph building** | Federation composition (subgraph SDLs → supergraph) belongs in the gateway build pipeline, not in a runtime client. | Accept pre-built supergraph SDL as input (already does via `schema_sdl` config). |
| A3 | **Mutation execution by default** | PROJECT.md explicitly says "Anti/out-of-scope: мутации by default." The brick is a read-only investigation tool. | Keep `GRAPHQL_ALLOW_MUTATIONS=false` default. Mutation guard already shipped in v1. |
| A4 | **Custom caching layer (Redis/Memcached for query results)** | Upstream caching is the gateway's job (Apollo persisted queries, CDN). Adding caching in the proxy creates stale-data bugs and invalidation hell. | Schema TTL cache already exists (v1). Query result caching: out of scope. |
| A5 | **Multi-endpoint routing / query splitting** | Splitting a query across N subgraph endpoints = gateway functionality (Apollo Router, Hive Gateway). Far beyond a single-endpoint brick. | Single `GRAPHQL_ENDPOINT` per brick instance. Deploy multiple brick instances for multiple endpoints. |
| A6 | **Built-in Prometheus HTTP endpoint** | OTEL's OTLP exporter pushes metrics to a collector. Exposing `/metrics` scrape endpoint in the brick duplicates collector's job and couples the brick to Prometheus format. | Use OTLP push export → Prometheus via OTEL Collector's `prometheusexporter`. If pull mode is required, a sidecar or the OTEL Collector handles `/metrics`. |
| A7 | **WebSocket-based MCP transport** | MCP protocol uses stdio or HTTP+SSE. There is no standard "MCP-over-WebSocket." Building one invents a non-standard protocol. | MCP stdio (already shipped), MCP-over-HTTP (already shipped). GraphQL subscriptions WS is a separate feature for the REST face. |
| A8 | **Python 3.9 support** | `pyproject.toml` already says `>=3.10`. 3.9 is EOL. Supporting it blocks `match`, `|` union types, `ParamSpec` usage. | Keep `>=3.10`. CI tests 3.10–3.12. |

## Feature Dependencies

```
T1 (OTEL httpx tracing) ──┐
T2 (OTEL FastAPI tracing) ─┤
T3 (OTEL metrics) ─────────┤──→ T5 (OTLP exporter config) ← must be configured first
T4 (OTEL log correlation) ─┘

T5 (OTLP exporter) ──→ D5 (Audit logging) ← benefits from trace_id in logs

T6 (Input validation) ─── standalone (uses existing graphql-core)

T7 (Rate limiting) ─── standalone (FastAPI middleware)

T8 (Header passthrough) ─── standalone (transport layer change)

D1 (WS subscriptions) ──→ D2 (SSE fallback) ──→ D7 (lib face streaming)
                      └──→ T7 needs extension (rate limit WS connections)

D3 (mTLS) ─── standalone (transport layer change)
D4 (Token rotation) ─── standalone (transport layer change, pairs well with D3)

T9 (PyPI publish) ─── standalone (CI workflow addition)

T10 (Copier template) ─── standalone but should be LAST (needs stable brick structure)

D6 (Integration tests) ─── benefits from all features being in place
```

## Phasing Recommendation

### Phase 1: Observability Foundation (T1–T5)

**Why first:** Everything else benefits from tracing and metrics. Without OTEL, debugging subscriptions or security issues is flying blind. Also the lowest-risk, most well-understood feature set.

1. **T5** — OTEL SDK bootstrap (TracerProvider + MeterProvider + OTLP exporter) in `config.py` / new `telemetry.py`
2. **T1** — Instrument outbound httpx (one-liner auto-instrumentation)
3. **T2** — Instrument inbound FastAPI (middleware wrap)
4. **T3** — Custom metrics in domain layer (query count, latency histogram, error rate by class)
5. **T4** — Log correlation (inject trace_id/span_id into log records)

**Estimated effort:** ~2 days. Well-documented, auto-instrumentation available.
**Risk:** LOW — standard patterns, no architectural changes.

### Phase 2: Security Hardening (T6–T8, D3–D5)

**Why second:** Security must come before exposing new attack surface (subscriptions).

1. **T6** — Query depth/complexity validation
2. **T7** — Rate limiting on REST endpoints
3. **T8** — Header passthrough for RBAC
4. **D3** — mTLS for outbound connections
5. **D4** — Token rotation (OAuth2 client_credentials)
6. **D5** — Audit logging

**Estimated effort:** ~3 days. mTLS and token rotation need careful testing.
**Risk:** MEDIUM — header passthrough requires threading through the domain layer cleanly.

### Phase 3: GraphQL Subscriptions (D1, D2, D7)

**Why third:** Depends on observability (tracing subscription streams) and security (rate limiting WS connections, auth for WS handshake).

1. **D1** — WebSocket subscription proxy (`graphql-transport-ws` protocol)
2. **D2** — SSE fallback endpoint
3. **D7** — `AsyncGraphQLClient.subscribe()` in lib face

**Estimated effort:** ~4 days. Most complex feature. Protocol state machine, connection lifecycle, error handling, backpressure.
**Risk:** HIGH — stateful connections, concurrency bugs, resource leaks. Needs thorough integration testing.

### Phase 4: DX & Ecosystem (T9, D6)

**Why fourth:** Ship quality requires tests; publish requires stable API.

1. **T9** — PyPI publish workflow (Trusted Publishers OIDC)
2. **D6** — Integration test harness + SDK examples

**Estimated effort:** ~2 days.
**Risk:** LOW — standard CI/CD patterns.

### Phase 5: Copier Template Extraction (T10)

**Why last:** Template must capture the final v2 structure. Doing it earlier means re-extracting after every structural change.

1. **T10** — Copier template with Jinja2 variables, answers file, sister brick generation

**Estimated effort:** ~2 days. Requires careful separation of generic vs. graphql-specific code.
**Risk:** MEDIUM — getting the template boundaries right is design-heavy.

---

## Technical Details per Feature

### T1–T5: OpenTelemetry Stack

**Packages needed:**
```
opentelemetry-api>=1.27
opentelemetry-sdk>=1.27
opentelemetry-exporter-otlp>=1.27
opentelemetry-instrumentation-httpx>=0.48b0
opentelemetry-instrumentation-fastapi>=0.48b0
opentelemetry-instrumentation-logging>=0.48b0
```

**Bootstrap pattern** (new `src/generic_graphql_mcp/telemetry.py`):
```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter

def init_telemetry(service_name: str = "generic-graphql-mcp") -> None:
    # Traces
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)
    # Metrics
    reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    metrics.set_meter_provider(MeterProvider(metric_readers=[reader]))
```

**Config integration:** Call `init_telemetry()` in `server.py` composition root. Respect `OTEL_SDK_DISABLED=true` for tests. All OTEL env vars (`OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_SERVICE_NAME`, etc.) work out of the box.

**Custom metrics in domain layer:**
```python
meter = metrics.get_meter("generic_graphql_mcp")
query_duration = meter.create_histogram("generic_graphql_mcp.query.duration_ms", unit="ms")
query_count = meter.create_counter("generic_graphql_mcp.query.count")
query_errors = meter.create_counter("generic_graphql_mcp.query.errors")
```

### T6: Input Validation

**Depth limiting:** Custom `graphql-core` visitor that walks the AST:
```python
from graphql import parse, visit, Visitor

class DepthLimitVisitor(Visitor):
    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.current_depth = 0
    
    def enter_field(self, node, *args):
        self.current_depth += 1
        if self.current_depth > self.max_depth:
            raise QueryTooDeepError(f"Query depth {self.current_depth} exceeds max {self.max_depth}")
    
    def leave_field(self, node, *args):
        self.current_depth -= 1
```

Config: `GRAPHQL_MAX_QUERY_DEPTH=10`, `GRAPHQL_MAX_QUERY_ALIASES=50`.

### T7: Rate Limiting

**slowapi integration:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/graphql/query")
@limiter.limit("100/minute")
def graphql_query(request: Request, req: QueryRequest):
    ...
```

Config: `GRAPHQL_RATE_LIMIT=100/minute` env var. Memory backend default; redis backend via `GRAPHQL_RATE_LIMIT_STORAGE_URI=redis://...`.

**Note:** slowapi does NOT support WebSocket endpoints. WS rate limiting needs a custom connection counter (e.g., asyncio semaphore per client IP).

### D1: WebSocket Subscriptions (`graphql-transport-ws`)

**Architecture:**
```
Client ←─WS─→ FastAPI /ws/graphql ←─WS─→ Upstream GraphQL Server
         (graphql-transport-ws)        (graphql-transport-ws)
```

**New components:**
- `ports/subscription_transport.py` — `SubscriptionTransport(Protocol)` with `subscribe(query, vars) -> AsyncIterator[QueryResult]`
- `adapters/outbound/ws_transport.py` — WebSocket client to upstream using `websockets` library
- `adapters/inbound/ws_subscription.py` — FastAPI WebSocket endpoint implementing protocol server side

**Protocol state machine:**
```
INIT → connection_init → [validate auth] → connection_ack → READY
READY → subscribe(id, query) → execute upstream → STREAMING(id)
STREAMING(id) → next(id, data)* → complete(id) → READY
Any state → ping/pong (bidirectional keepalive)
Client disconnect → cleanup all active subscriptions
```

**Key considerations:**
- Connection multiplexing: one WS connection, multiple subscription IDs
- Backpressure: if client is slow to consume, buffer N messages then drop/error
- Keepalive: server-initiated ping every 30s, close on pong timeout
- Resource limits: max N concurrent subscriptions per connection, max M connections per IP

### D2: SSE Fallback

```python
from fastapi.sse import EventSourceResponse

@app.get("/graphql/subscribe", response_class=EventSourceResponse)
async def subscribe_sse(query: str, variables: str | None = None) -> AsyncIterable[dict]:
    async for result in subscription_transport.subscribe(query, parsed_vars):
        yield {"data": result.data, "errors": result.errors, "error_class": result.error_class.value}
```

SSE is simpler: unidirectional server→client, auto-reconnect via `Last-Event-ID`, no protocol negotiation. Good for MCP-over-HTTP consumers.

### D3: mTLS

```python
import ssl

def _build_ssl_context(config: GraphQLConfig) -> ssl.SSLContext | bool:
    if not config.client_cert:
        return config.ssl_verify  # existing behavior
    ctx = ssl.create_default_context(cafile=config.ca_bundle or None)
    ctx.load_cert_chain(certfile=config.client_cert, keyfile=config.client_key)
    return ctx
```

New config fields: `GRAPHQL_CLIENT_CERT`, `GRAPHQL_CLIENT_KEY`, `GRAPHQL_CA_BUNDLE`.

### D4: Token Rotation

```python
import httpx
import time

class OAuth2ClientCredentials(httpx.Auth):
    def __init__(self, token_url: str, client_id: str, client_secret: str):
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self._token: str | None = None
        self._expires_at: float = 0

    def auth_flow(self, request):
        if not self._token or time.monotonic() >= self._expires_at:
            self._refresh()
        request.headers["Authorization"] = f"Bearer {self._token}"
        yield request

    def _refresh(self):
        resp = httpx.post(self.token_url, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._expires_at = time.monotonic() + data.get("expires_in", 3600) - 30  # 30s buffer
```

Config: `GRAPHQL_OAUTH2_TOKEN_URL`, `GRAPHQL_OAUTH2_CLIENT_ID`, `GRAPHQL_OAUTH2_CLIENT_SECRET`. Passed to httpx via `auth=` parameter — transparent to the rest of the transport.

### T9: PyPI Publish CI

```yaml
# .github/workflows/publish.yml
name: Publish to PyPI
on:
  push:
    tags: ['v*']
jobs:
  # ... reuse wheels + sdist jobs from ci.yml ...
  publish:
    needs: [wheels, sdist]
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # OIDC for Trusted Publishers
    steps:
      - uses: actions/download-artifact@v4
        with: { path: dist/, merge-multiple: true }
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**Trusted Publishers** (OIDC) — no static API tokens. Configure on PyPI: project → settings → publishing → add GitHub Actions publisher.

### T10: Copier Template

**Structure:**
```
template/
  copier.yml                    # questions + defaults
  {{ module_name }}/
    __init__.py.jinja
    domain/...
    ports/...
    adapters/...
  pyproject.toml.jinja
  Dockerfile.jinja
  .github/workflows/ci.yml.jinja
```

**Key questions in `copier.yml`:**
```yaml
project_name:
  type: str
  help: "Human-readable project name (e.g., 'kafka-mcp')"
module_name:
  type: str
  help: "Python module name (e.g., 'kafka_mcp')"
  default: "{{ project_name | replace('-', '_') }}"
has_rust_native:
  type: bool
  default: true
  help: "Include pyo3/Rust native extension?"
protocol_type:
  type: str
  choices: [graphql, kafka, http]
  help: "Primary protocol this brick proxies"
```

**Downstream update flow:** `copier update kafka-mcp/` pulls latest template changes, merges with existing answers, preserves local modifications via git diff.

---

## Complexity & Risk Summary

| Feature | Complexity | Risk | Confidence |
|---------|-----------|------|------------|
| T1–T5 OTEL stack | Low–Medium | LOW | HIGH — standard packages, auto-instrumentation |
| T6 Input validation | Medium | LOW | HIGH — graphql-core AST visitors well-documented |
| T7 Rate limiting | Low | LOW | HIGH — slowapi battle-tested |
| T8 Header passthrough | Medium | MEDIUM | MEDIUM — requires domain layer threading |
| D1 WS subscriptions | High | HIGH | HIGH on protocol, MEDIUM on implementation |
| D2 SSE fallback | Medium | LOW | HIGH — FastAPI built-in EventSourceResponse |
| D3 mTLS | Medium | LOW | HIGH — httpx SSL context verified |
| D4 Token rotation | Medium | LOW | HIGH — httpx Auth protocol documented |
| D5 Audit logging | Low | LOW | HIGH — middleware pattern |
| D6 Integration tests | Medium | LOW | MEDIUM — depends on mock server choice |
| D7 Lib face streaming | Medium | MEDIUM | MEDIUM — async iterator lifecycle |
| T9 PyPI CI | Medium | LOW | HIGH — standard GH Actions pattern |
| T10 Copier template | High | MEDIUM | HIGH on Copier, MEDIUM on template boundaries |

## Sources

- OpenTelemetry Python instrumentation: Context7 `/websites/opentelemetry_io` — auto-instrumentation for httpx, FastAPI middleware, manual trace/metric creation
- FastAPI WebSocket: Context7 `/fastapi/fastapi` — `@app.websocket`, `WebSocket.accept/receive/send`, `WebSocketDisconnect`
- FastAPI SSE: Context7 `/fastapi/fastapi` — `EventSourceResponse` built-in class, `AsyncIterable` return type with Pydantic validation
- graphql-transport-ws protocol: `github.com/enisdenjo/graphql-ws/PROTOCOL.md` — full protocol spec with message types, error codes, lifecycle
- httpx SSL/mTLS: `python-httpx.org/advanced/ssl/` — `ssl.SSLContext`, `load_cert_chain()`, client-side certificates
- Copier: Context7 `/copier-org/copier` — `run_copy`, `run_update`, `VcsRef.CURRENT`, answers file, conflict handling
- slowapi: PyPI `slowapi==0.1.10` — rate limiting for Starlette/FastAPI, memory/redis backends
- httpx Auth protocol: httpx docs — `httpx.Auth` with `auth_flow()` generator for custom authentication
