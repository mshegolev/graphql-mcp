# Architecture Patterns — v2.0 Integration Analysis

**Domain:** GraphQL MCP brick — production-grade platform upgrade
**Researched:** 2026-06-16
**Overall Confidence:** HIGH (based on codebase analysis + Context7 verified docs)

## Current Architecture Map

```
src/graphql_mcp/
  domain/          # Pure logic, no I/O
    models.py        QueryResult, ErrorClass, SchemaGraph, TypeInfo, Subgraph, SchemaSummary
    errors.py        SchemaResolutionError, MutationGuardError
    schema_service.py  SchemaService (cascade resolve + TTL cache)

  ports/           # Protocol interfaces (hexagonal contracts)
    transport.py     GraphQLTransport, AsyncGraphQLTransport
    schema_source.py SchemaSource
    json_codec.py    JsonCodec

  adapters/
    inbound/       # Entry points (consumers of domain)
      lib.py           GraphQLClient (sync facade, composition root)
      async_lib.py     AsyncGraphQLClient (async facade)
      rest.py          FastAPI app (REST + MCP-over-HTTP mount at /mcp)
      mcp_stdio.py     FastMCP stdio adapter
      mcp_http.py      MCP streamable HTTP sub-app factory
      cli.py           Click CLI (serve, query, introspect, etc.)

    outbound/      # External dependencies (injected via ports)
      http_transport.py       HttpTransport (httpx.Client sync)
      async_http_transport.py AsyncHttpTransport (httpx.AsyncClient)
      codec_factory.py        get_codec() → Rust native or orjson fallback
      json_native.py          RustJsonCodec (pyo3)
      json_orjson.py          OrjsonCodec (fallback)
      query_guard.py          Mutation detection via graphql-core AST
      schema_analyzer.py      SDL → SchemaSummary, TypeInfo, Subgraph
      gitlab_source.py        GitLabSource (SchemaSource impl)
      introspection_source.py IntrospectionSource (SchemaSource impl)
      service_sdl_source.py   ServiceSdlSource (SchemaSource impl)
      file_source.py          FileSdlSource (SchemaSource impl)

  config.py        GraphQLConfig (pydantic-settings, GRAPHQL_* env prefix)
  __init__.py      Re-exports: GraphQLClient, AsyncGraphQLClient

native/            # Rust pyo3 crate (JSON codec)
```

### Current Data Flow

```
[Consumer] → Inbound Adapter → GraphQLClient facade
                                    ├→ SchemaService.resolve() → SchemaSource cascade
                                    ├→ HttpTransport.execute() → remote GraphQL endpoint
                                    ├→ SchemaAnalyzer (local SDL analysis)
                                    └→ QueryGuard (mutation detection)
```

### Hexagonal Invariants (Must Preserve)

1. **Domain is pure** — `domain/` has zero I/O imports, no framework deps
2. **Ports are Protocol** — `ports/` are `@runtime_checkable` Protocols, not ABCs
3. **Adapters depend inward** — adapters import domain/ports, never reverse
4. **Library-first** — `GraphQLClient.from_env()` works without FastAPI/MCP/uvicorn
5. **Config via env** — single `GraphQLConfig` with `GRAPHQL_*` prefix

---

## Feature Integration Analysis

### 1. OpenTelemetry (Tracing + Metrics + Logs)

**Goal:** Instrument all operations across all transports with OTEL spans, counters, histograms.

#### Integration Strategy: Cross-Cutting Concern as Outbound Adapter

OTEL is NOT a domain concern — it's an infrastructure cross-cutting concern. It belongs in `adapters/outbound/` as an **observability adapter**, injected as a decorator/wrapper around existing ports.

#### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `adapters/outbound/telemetry.py` | New file | OTEL bootstrap: `init_telemetry(config) → TracerProvider, MeterProvider` |
| `adapters/outbound/traced_transport.py` | New file | Decorator wrapping `GraphQLTransport`/`AsyncGraphQLTransport` with span creation |
| `ports/telemetry.py` | New file (optional) | `Telemetry` Protocol for testability without OTEL SDK |
| Config additions | `config.py` | `otel_enabled`, `otel_service_name`, `otel_exporter_endpoint`, `otel_exporter_protocol` |

#### What Changes in Existing Code

| File | Change | Why |
|------|--------|-----|
| `config.py` | Add `otel_*` fields | Environment-driven OTEL configuration |
| `adapters/inbound/lib.py` | Wrap transport in `TracedTransport` during `from_env()` | Decorator injection at composition root |
| `adapters/inbound/async_lib.py` | Same wrapping for `AsyncTracedTransport` | Async parity |
| `adapters/inbound/rest.py` | Add OTEL FastAPI middleware (auto-instrumentation) | Request-level spans for HTTP |
| `adapters/inbound/cli.py` → `serve()` | Call `init_telemetry()` before uvicorn.run | Bootstrap OTEL once at process start |

#### Architecture Pattern: Transport Decorator

```python
# adapters/outbound/traced_transport.py
class TracedTransport:
    """Decorator: adds OTEL spans around any GraphQLTransport."""
    def __init__(self, inner: GraphQLTransport, tracer: Tracer):
        self._inner = inner
        self._tracer = tracer

    def execute(self, query, variables=None) -> QueryResult:
        with self._tracer.start_as_current_span("graphql.execute") as span:
            span.set_attribute("graphql.operation", _extract_op_name(query))
            result = self._inner.execute(query, variables)
            span.set_attribute("graphql.error_class", result.error_class.value)
            if result.error_class != ErrorClass.OK:
                span.set_status(StatusCode.ERROR)
            return result
```

This preserves the hexagonal invariant: domain never sees OTEL. Transport port stays clean. The `from_env()` composition root wraps if `otel_enabled=True`.

#### OTEL Packages Required

```
opentelemetry-api
opentelemetry-sdk
opentelemetry-exporter-otlp-proto-grpc   # or -http
opentelemetry-instrumentation-fastapi     # auto-instrument REST
opentelemetry-instrumentation-httpx       # auto-instrument outbound HTTP
opentelemetry-instrumentation-logging     # correlate logs with trace IDs
```

#### Metrics to Capture

| Metric | Type | Where |
|--------|------|-------|
| `graphql_mcp.query.duration` | Histogram | TracedTransport |
| `graphql_mcp.query.count` | Counter | TracedTransport (by error_class) |
| `graphql_mcp.schema.resolve.duration` | Histogram | Schema service wrapper |
| `graphql_mcp.schema.cache.hit` | Counter | Schema service wrapper |
| `graphql_mcp.transport.error` | Counter | TracedTransport (by error type) |

#### Confidence: HIGH
- Context7 verified: OTEL Python SDK, OTLP exporters, FastAPI/httpx auto-instrumentation all well-documented
- Decorator pattern is textbook for cross-cutting concerns in hexagonal architecture
- httpx instrumentation covers both sync and async clients automatically

---

### 2. Security Hardening (mTLS, Token Rotation, RBAC, Rate Limiting, Audit)

**Goal:** mTLS for outbound connections, token rotation, RBAC header forwarding, audit logging, rate limiting, input validation.

#### Integration Strategy: Layered Security — Config + Transport + Middleware

Security touches three layers:
1. **Transport layer** (mTLS, token rotation) → outbound adapter changes
2. **Middleware layer** (rate limiting, RBAC forwarding) → inbound adapter additions
3. **Config layer** (certificates, token refresh) → config.py extensions

#### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `adapters/outbound/tls_config.py` | New file | Build `ssl.SSLContext` from cert/key/CA paths for mTLS |
| `adapters/outbound/token_refresh.py` | New file | Token rotation logic: refresh-before-expiry, caching |
| `adapters/inbound/middleware/rate_limit.py` | New file | FastAPI middleware: token-bucket or sliding-window rate limiter |
| `adapters/inbound/middleware/audit_log.py` | New file | Structured audit logging for all inbound operations |
| `adapters/inbound/middleware/__init__.py` | New file | Middleware package |
| Config additions | `config.py` | TLS cert paths, token refresh URL, rate limit params |

#### What Changes in Existing Code

| File | Change | Why |
|------|--------|-----|
| `config.py` | Add `tls_cert_path`, `tls_key_path`, `tls_ca_path`, `token_refresh_url`, `token_refresh_interval`, `rate_limit_rpm`, `audit_log_enabled` | Security config via env |
| `adapters/outbound/http_transport.py` | Accept optional `ssl_context` in constructor, pass to `httpx.Client(verify=ssl_context)` | mTLS support |
| `adapters/outbound/async_http_transport.py` | Same change | Async parity |
| `adapters/inbound/lib.py` → `from_env()` | Build SSLContext from config, inject into transport; wire token refresher | Composition root wiring |
| `adapters/inbound/async_lib.py` → `from_env()` | Same | Async parity |
| `adapters/inbound/rest.py` | Mount rate-limit + audit-log middleware on FastAPI app | Middleware chain |

#### Architecture Pattern: SSL Context Injection

```python
# adapters/outbound/tls_config.py
import ssl
def build_ssl_context(cert: str, key: str, ca: str) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_cert_chain(cert, key)
    ctx.load_verify_locations(ca)
    return ctx

# In http_transport.py, change:
#   verify=ssl_verify  →  verify=ssl_context or ssl_verify
# httpx supports ssl.SSLContext in the `verify` param directly.
```

#### Architecture Pattern: Token Rotation

```python
# adapters/outbound/token_refresh.py
class TokenRefresher:
    """Refreshes bearer token before expiry. Thread-safe."""
    def __init__(self, refresh_url: str, current_token: str, refresh_interval: int): ...
    def get_token(self) -> str:
        """Return current valid token, refreshing if near expiry."""
        ...
```

The `HttpTransport` gains an optional `token_provider: Callable[[], str]` injected at construction. On each request, it calls `token_provider()` instead of using a static header. This is clean injection without domain contamination.

#### Rate Limiting Approach

Use **in-process rate limiting** (not Redis-backed) because this is a single-brick MCP tool, not a distributed API gateway. A simple token-bucket middleware on FastAPI is sufficient.

```python
# adapters/inbound/middleware/rate_limit.py
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, rpm: int = 60): ...
    async def dispatch(self, request, call_next):
        if not self._allow():
            return JSONResponse(status_code=429, content={"error": "rate limited"})
        return await call_next(request)
```

#### Confidence: HIGH
- httpx `verify=ssl.SSLContext` is documented and tested
- FastAPI middleware is well-established pattern
- Token rotation is standard refresh-before-expiry pattern
- No domain changes needed — all in adapters/config

---

### 3. GraphQL Subscriptions (WebSocket + SSE)

**Goal:** Support GraphQL subscriptions via WebSocket (graphql-ws protocol) and SSE fallback.

#### Integration Strategy: New Port + New Adapters (Both Inbound and Outbound)

Subscriptions are fundamentally different from query/raw — they're **streaming**, **stateful**, and **bidirectional** (WS) or **unidirectional** (SSE). This requires:
- A new **port** (`SubscriptionTransport`) — the streaming contract
- New **outbound adapter** — WebSocket client connecting to the remote GraphQL server
- New **inbound adapters** — exposing subscriptions to consumers via WS and SSE

#### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `ports/subscription.py` | New file | `SubscriptionTransport` Protocol: `subscribe(query, variables) → AsyncIterator[QueryResult]` |
| `domain/models.py` additions | Modified | `SubscriptionEvent` model (extends QueryResult with event metadata) |
| `adapters/outbound/ws_subscription.py` | New file | WebSocket outbound: connects to remote GQL server via graphql-ws protocol |
| `adapters/inbound/ws_handler.py` | New file | FastAPI WebSocket endpoint: proxies subscription from client to outbound WS |
| `adapters/inbound/sse_handler.py` | New file | FastAPI SSE endpoint: wraps subscription as `EventSourceResponse` stream |
| `adapters/inbound/async_lib.py` additions | Modified | `subscribe()` method on `AsyncGraphQLClient` |
| Config additions | `config.py` | `ws_endpoint`, `subscription_enabled`, `subscription_timeout` |

#### What Changes in Existing Code

| File | Change | Why |
|------|--------|-----|
| `config.py` | Add `ws_endpoint`, `subscription_enabled`, `subscription_timeout` | Subscription config |
| `domain/models.py` | Add `SubscriptionEvent` model (optional; or reuse `QueryResult`) | Type streaming results |
| `adapters/inbound/rest.py` | Mount WS + SSE endpoints | Expose subscription inbound |
| `adapters/inbound/async_lib.py` | Add `subscribe()` method returning `AsyncIterator[QueryResult]` | Library-first subscription API |
| `adapters/inbound/mcp_stdio.py` | Subscription tool (limited: MCP stdio is request-response, not streaming) | Best-effort MCP support |
| `ports/__init__.py` or `ports/subscription.py` | New subscription port | Clean hexagonal contract |

#### Architecture Pattern: Subscription Port

```python
# ports/subscription.py
from typing import AsyncIterator, Protocol, runtime_checkable

@runtime_checkable
class SubscriptionTransport(Protocol):
    async def subscribe(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> AsyncIterator[QueryResult]:
        """Open a subscription and yield results as they arrive."""
        ...
```

#### Architecture Pattern: WebSocket Outbound (graphql-ws protocol)

The `graphql-ws` protocol (used by Apollo, Relay, etc.) runs over WebSocket with a specific message flow:

```
Client → Server: ConnectionInit { type: "connection_init", payload: {auth} }
Server → Client: ConnectionAck { type: "connection_ack" }
Client → Server: Subscribe { type: "subscribe", id: "1", payload: {query, variables} }
Server → Client: Next { type: "next", id: "1", payload: {data, errors} }  (repeating)
Server → Client: Complete { type: "complete", id: "1" }
```

```python
# adapters/outbound/ws_subscription.py
import websockets  # or httpx-ws

class WsSubscriptionTransport:
    """graphql-ws protocol over WebSocket to remote GraphQL server."""

    async def subscribe(self, query, variables=None) -> AsyncIterator[QueryResult]:
        async with websockets.connect(self._ws_endpoint, ...) as ws:
            await ws.send(json.dumps({"type": "connection_init", "payload": self._auth}))
            ack = json.loads(await ws.recv())
            assert ack["type"] == "connection_ack"

            sub_id = str(uuid4())
            await ws.send(json.dumps({
                "type": "subscribe", "id": sub_id,
                "payload": {"query": query, "variables": variables}
            }))

            async for msg_raw in ws:
                msg = json.loads(msg_raw)
                if msg["type"] == "next" and msg["id"] == sub_id:
                    yield _parse_result(msg["payload"])
                elif msg["type"] == "complete" and msg["id"] == sub_id:
                    break
                elif msg["type"] == "error":
                    yield _parse_error(msg["payload"])
                    break
```

#### Inbound: WebSocket Proxy Handler

```python
# adapters/inbound/ws_handler.py
@app.websocket("/graphql/subscribe")
async def ws_subscription(websocket: WebSocket):
    await websocket.accept(subprotocol="graphql-transport-ws")
    # Bridge: client WS ↔ outbound subscription transport
    # Forward graphql-ws messages bidirectionally
```

#### Inbound: SSE Fallback

```python
# adapters/inbound/sse_handler.py
from fastapi.sse import EventSourceResponse, ServerSentEvent

@app.get("/graphql/subscribe/sse", response_class=EventSourceResponse)
async def sse_subscription(query: str, variables: str | None = None):
    client = _get_async_client()
    async def event_stream():
        async for result in client.subscribe(query, parsed_vars):
            yield ServerSentEvent(data=result.model_dump(), event="next")
    return event_stream()
```

#### MCP Stdio Limitation

MCP stdio is request-response. Subscriptions can only be exposed as:
- `subscribe_once(query, variables, timeout)` → returns first N events or times out
- Not a true streaming API, but useful for investigator use cases

#### WebSocket Library Choice

Use **`websockets`** (not `httpx-ws`) because:
- `websockets` is the standard Python WebSocket library, actively maintained
- FastAPI's WebSocket support is built on Starlette which uses `websockets` under the hood
- `httpx-ws` is newer and less battle-tested for persistent subscription connections
- `websockets` version >=14 supports async context managers cleanly

#### Confidence: HIGH for SSE (FastAPI native support verified via Context7), MEDIUM for WS
- SSE: FastAPI `EventSourceResponse` is native and well-documented (Context7 confirmed)
- WebSocket inbound: FastAPI WebSocket support is mature (Context7 confirmed)
- WebSocket outbound (graphql-ws protocol): requires careful protocol implementation
- The graphql-ws protocol is well-specified but Python client-side libraries (`gql` has WS support) should be evaluated

---

### 4. DX & CI Improvements

**Goal:** PyPI publish pipeline, GitHub Actions CI improvements, better error messages, SDK examples, integration test harness.

#### Integration Strategy: Peripheral — No Architecture Changes

DX/CI changes are entirely outside the hexagonal architecture. They're build/tooling concerns.

#### New Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `.github/workflows/publish.yml` | New file | PyPI publish on tag push (trusted publisher) |
| `.github/workflows/ci.yml` | Modified | Add coverage, type checking, security scan |
| `examples/` | New directory | SDK usage examples (query, subscribe, etc.) |
| `tests/integration/` | New directory | Integration tests (require real GraphQL endpoint) |
| `tests/conftest.py` | Modified | Fixtures for integration test mode |

#### What Changes in Existing Code

| File | Change | Why |
|------|--------|-----|
| `.github/workflows/ci.yml` | Add coverage reporting, mypy, integration test step | CI hardening |
| `pyproject.toml` | Add `[project.urls]`, optional mypy config | Package metadata |
| `domain/errors.py` | Enrich error messages with context | Better DX |

#### Confidence: HIGH — standard GitHub Actions patterns

---

### 5. Copier Template Extraction

**Goal:** Extract graphql-mcp skeleton into a Copier template so kafka-mcp/ordering-mcp can be generated from it.

#### Integration Strategy: Overlay — Template Files Alongside Source

Copier template extraction means the **source files themselves become templates**. Two approaches:

**Approach A: Separate template repo** (recommended)
- Create `investigate-mcp-template/` as a separate repo
- Files use Jinja2 templating: `{{project_name}}/`, `{{module_name}}.py.jinja`
- graphql-mcp is the first **instance** generated from this template

**Approach B: In-repo `template/` directory** (simpler but less clean)
- `template/` directory within graphql-mcp with `copier.yml` + templated sources
- Other bricks run `copier copy ./template ../kafka-mcp`

**Recommendation: Approach A** — separate template repo. The graphql-mcp repo should not contain template meta-files; it should be a clean instance. The template lives in the umbrella (`investigate-suite/`) or its own repo.

#### What the Template Needs from graphql-mcp

The template extracts the **hexagonal skeleton**:

```yaml
# copier.yml
project_name:
  type: str
  help: "Project name (e.g., kafka-mcp)"

module_name:
  type: str
  default: "{{ project_name | replace('-', '_') }}"
  help: "Python module name"

graphql_protocol:
  type: str
  default: "graphql"
  help: "Protocol type this brick handles"

has_native_rust:
  type: bool
  default: true
  help: "Include Rust pyo3 native extension?"

has_subscriptions:
  type: bool
  default: false
  help: "Include subscription support?"
```

#### Template File Mapping

```
template/
  copier.yml
  {{module_name}}/
    __init__.py.jinja
    config.py.jinja                # GRAPHQL_ → {{env_prefix}}_
    domain/
      models.py.jinja              # QueryResult stays; protocol-specific models templated
      errors.py.jinja
      schema_service.py            # Unchanged (generic cascade pattern)
    ports/
      transport.py.jinja           # Protocol-specific execute signature
      schema_source.py             # Unchanged
      json_codec.py                # Unchanged
    adapters/
      inbound/
        lib.py.jinja               # {{module_name}}Client
        rest.py.jinja              # FastAPI app for {{project_name}}
        mcp_stdio.py.jinja
        cli.py.jinja
      outbound/
        http_transport.py.jinja    # Endpoint-specific transport
        codec_factory.py           # Unchanged
  {% if has_native_rust %}
  native/
    Cargo.toml.jinja
    src/lib.rs                     # Unchanged (JSON codec)
  {% endif %}
  pyproject.toml.jinja
  Dockerfile.jinja
  .github/workflows/ci.yml.jinja
```

#### What Changes in Existing Code

| File | Change | Why |
|------|--------|-----|
| None in graphql-mcp | — | Template lives in separate repo |
| PROJECT.md | Document that graphql-mcp is the reference brick | Traceability |

#### Confidence: HIGH
- Copier template structure verified via Context7
- Jinja2 templating, conditional sections, typed questions all documented
- `copier update` supports re-applying template changes to existing projects

---

## Component Dependency Graph

```
                           ┌─────────────┐
                           │  config.py   │ ← env vars
                           └──────┬───────┘
                                  │
                    ┌─────────────┼─────────────────────────┐
                    │             │                          │
              ┌─────▼─────┐ ┌────▼──────┐  ┌──────────────▼──────────┐
              │ Telemetry │ │ TLS/Token │  │ Subscription config     │
              │  bootstrap│ │  config   │  │ (ws_endpoint, enabled)  │
              └─────┬─────┘ └────┬──────┘  └──────────┬──────────────┘
                    │            │                     │
         ┌──────────┼────────────┼─────────────────────┼──────────────┐
         │          │            │                     │              │
    ┌────▼───┐ ┌───▼────┐  ┌───▼──────┐  ┌──────────▼─────┐  ┌────▼──────┐
    │ Traced │ │ mTLS   │  │ Token    │  │ WS Subscription│  │ Rate Limit│
    │Transp. │ │SSLCtx  │  │Refresher │  │  Transport     │  │ Middleware│
    │(decor.)│ │        │  │          │  │                │  │           │
    └────┬───┘ └───┬────┘  └───┬──────┘  └──────┬─────────┘  └────┬──────┘
         │         │           │                 │                  │
         │    ┌────▼───────────▼──┐              │             ┌───▼───────┐
         │    │  HttpTransport    │              │             │ FastAPI   │
         │    │  (now with SSL +  │              │             │ rest.py   │
         └────► token provider)  │              │             │ + WS + SSE│
              └──────────────────┘              │             └───────────┘
                                                │
                                     ┌──────────▼──────────┐
                                     │ AsyncGraphQLClient  │
                                     │ .subscribe() method │
                                     └────────────────────┘
```

## New vs Modified Summary

### New Files (13)

| File | Layer | Feature |
|------|-------|---------|
| `ports/subscription.py` | Port | Subscription contract |
| `ports/telemetry.py` | Port | Optional telemetry abstraction |
| `adapters/outbound/telemetry.py` | Outbound | OTEL bootstrap (TracerProvider, MeterProvider) |
| `adapters/outbound/traced_transport.py` | Outbound | Transport decorator with OTEL spans |
| `adapters/outbound/tls_config.py` | Outbound | SSL context builder for mTLS |
| `adapters/outbound/token_refresh.py` | Outbound | Token rotation logic |
| `adapters/outbound/ws_subscription.py` | Outbound | WebSocket graphql-ws client |
| `adapters/inbound/ws_handler.py` | Inbound | WebSocket proxy endpoint |
| `adapters/inbound/sse_handler.py` | Inbound | SSE subscription endpoint |
| `adapters/inbound/middleware/__init__.py` | Inbound | Middleware package |
| `adapters/inbound/middleware/rate_limit.py` | Inbound | Rate limiting |
| `adapters/inbound/middleware/audit_log.py` | Inbound | Structured audit logging |
| `.github/workflows/publish.yml` | CI/CD | PyPI publish pipeline |

### Modified Files (9)

| File | Change Scope | Feature |
|------|-------------|---------|
| `config.py` | Add ~15 new fields | OTEL + security + subscription config |
| `domain/models.py` | Add SubscriptionEvent (minor) | Subscription types |
| `adapters/inbound/lib.py` | `from_env()` wiring for OTEL + mTLS + token | Composition root |
| `adapters/inbound/async_lib.py` | `from_env()` wiring + `subscribe()` method | Composition root + subscriptions |
| `adapters/inbound/rest.py` | Mount middleware + WS + SSE endpoints | Inbound surface |
| `adapters/inbound/mcp_stdio.py` | Add subscription tool | MCP subscription support |
| `adapters/outbound/http_transport.py` | Accept ssl_context + token_provider | mTLS + token rotation |
| `adapters/outbound/async_http_transport.py` | Same | Async parity |
| `.github/workflows/ci.yml` | Coverage, mypy, security scan | CI hardening |

### Unchanged Files (everything else)

Domain purity preserved: `schema_service.py`, `errors.py` — zero changes.
All outbound schema sources — zero changes.
Ports `transport.py`, `schema_source.py`, `json_codec.py` — zero changes.
Rust native crate — zero changes.

---

## Suggested Build Order

Build order is driven by **dependency chains** and **risk reduction**:

### Phase 1: OTEL Observability (foundation — everything else benefits from tracing)

```
config.py (otel fields)
  → adapters/outbound/telemetry.py (bootstrap)
  → adapters/outbound/traced_transport.py (decorator)
  → lib.py / async_lib.py from_env() wiring
  → rest.py OTEL middleware
  → tests
```

**Rationale:** Once OTEL is in place, all subsequent features (subscriptions, security) are automatically traced. Build this first so you can observe the rest of the work.

### Phase 2: Security Hardening (transport-layer, before subscriptions)

```
config.py (security fields)
  → adapters/outbound/tls_config.py
  → adapters/outbound/token_refresh.py
  → http_transport.py / async_http_transport.py (SSL + token provider)
  → lib.py / async_lib.py from_env() wiring
  → adapters/inbound/middleware/ (rate_limit, audit_log)
  → rest.py middleware mount
  → tests
```

**Rationale:** Security must be in place before WebSocket connections are opened. mTLS and token rotation affect the transport layer that subscriptions will use.

### Phase 3: GraphQL Subscriptions (builds on secure, traced transport)

```
ports/subscription.py
  → domain/models.py (SubscriptionEvent if needed)
  → adapters/outbound/ws_subscription.py (graphql-ws protocol)
  → adapters/inbound/ws_handler.py (WebSocket proxy)
  → adapters/inbound/sse_handler.py (SSE fallback)
  → async_lib.py subscribe() method
  → rest.py mount WS + SSE endpoints
  → mcp_stdio.py subscribe_once tool
  → tests
```

**Rationale:** Subscriptions are the highest-complexity feature. By this point, the transport is secure and traced, so WS connections inherit mTLS and OTEL spans.

### Phase 4: DX & CI (polish — no deps on other features)

```
.github/workflows/ (publish, CI improvements)
  → examples/ directory
  → tests/integration/ harness
  → error message improvements
  → pyproject.toml metadata
```

**Rationale:** Can run in parallel with Phase 3 if team capacity allows. No architectural dependencies.

### Phase 5: Copier Template (last — needs stable architecture)

```
Analyze final graphql-mcp structure
  → Create template repo with copier.yml
  → Jinja2-ify all templatable files
  → Test: generate kafka-mcp from template
  → Verify generated project passes tests
```

**Rationale:** Template must capture the **final** architecture including OTEL, security, and subscriptions. Building it before those features stabilize means re-templating.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Leaking OTEL into Domain
**What:** Importing `opentelemetry` in `domain/` or `ports/`
**Why bad:** Violates hexagonal purity; makes domain untestable without OTEL SDK installed
**Instead:** Decorator pattern in adapters; domain stays clean

### Anti-Pattern 2: Subscription as Polling
**What:** Implementing subscriptions as periodic query polling
**Why bad:** Defeats the purpose; wastes resources; doesn't give real-time semantics
**Instead:** Proper WebSocket connection to remote GraphQL server using graphql-ws protocol

### Anti-Pattern 3: Global Rate Limiter State
**What:** Module-level rate limiter dict shared across uvicorn workers
**Why bad:** Each worker fork gets its own copy; limits are per-worker not per-server
**Instead:** Per-worker rate limiting (acceptable for single-brick), or shared backend if needed

### Anti-Pattern 4: Copier Template with Hardcoded graphql-mcp References
**What:** Template files that still reference `graphql_mcp` or `GraphQLClient` literally
**Why bad:** Generated kafka-mcp would have graphql_mcp imports
**Instead:** Thorough Jinja2 parameterization: `{{module_name}}`, `{{client_class_name}}`

### Anti-Pattern 5: WebSocket Handler Doing Protocol + Business Logic
**What:** Single ws_handler.py that implements graphql-ws protocol AND query validation
**Why bad:** Violates SRP; untestable; hard to switch protocols
**Instead:** Protocol handling in outbound adapter (ws_subscription.py); inbound handler is a thin bridge

---

## Scalability Considerations

| Concern | Current (v1.1) | v2.0 Target | At Scale (100+ clients) |
|---------|-----------------|-------------|-------------------------|
| Request tracing | None (logging only) | OTEL spans + metrics | OTLP → collector → Jaeger/Tempo |
| Connection security | Bearer token + SSL verify | mTLS + token rotation | Certificate rotation via env/secret |
| Subscription connections | N/A | WS per-client | Connection pooling; max connections config |
| Rate limiting | None | Per-worker token bucket | Consider Redis-backed if multi-worker |
| Audit trail | Logging | Structured JSON audit logs | Log pipeline to OpenSearch |

---

## Sources

- **Context7 (HIGH confidence):**
  - OpenTelemetry Python SDK: TracerProvider, MeterProvider, BatchSpanProcessor, OTLP exporters — `/open-telemetry/opentelemetry.io`
  - OpenTelemetry httpx auto-instrumentation — `/open-telemetry/opentelemetry.io`
  - FastAPI WebSocket support — `/fastapi/fastapi`
  - FastAPI SSE (EventSourceResponse, ServerSentEvent) — `/fastapi/fastapi`
  - Copier template structure (copier.yml, Jinja2 templating, answers file) — `/copier-org/copier`

- **Codebase analysis (HIGH confidence):**
  - All 22 source files read and analyzed
  - Hexagonal boundaries verified: domain has zero external imports
  - Composition root pattern (`from_env()`) identified as injection point
  - Transport Protocol → decorator pattern confirmed feasible

- **graphql-ws protocol (MEDIUM confidence):**
  - Protocol spec from graphql-ws npm package documentation
  - Python implementation patterns from `gql` library WebSocket transport
  - Needs validation: whether to use `websockets` directly or `gql`'s WS transport
