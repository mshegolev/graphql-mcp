# Technology Stack — v2.0 Additions

**Project:** generic-graphql-mcp v2.0 Production-Grade Platform
**Researched:** 2026-06-16
**Scope:** NEW libraries only — existing stack (httpx, FastAPI, pydantic, mcp, graphql-core, gql, orjson, pyo3/maturin, ruff, pytest) is validated and unchanged.

---

## Recommended Stack Additions

### 1. OpenTelemetry — Tracing, Metrics, Logs

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `opentelemetry-api` | `>=1.42,<2` | Vendor-neutral tracing/metrics API | Industry standard; suite already exports to Jaeger/Prometheus. API-only import keeps core library lightweight — no SDK dependency in production unless the deployer opts in. |
| `opentelemetry-sdk` | `>=1.42,<2` | TracerProvider, MeterProvider, LogProvider | Needed at composition-root (`server.py`) level only, not in domain code. Pin to same major as `api`. |
| `opentelemetry-exporter-otlp-proto-http` | `>=1.42,<2` | OTLP/HTTP exporter (traces + metrics + logs) | HTTP/protobuf transport — no grpcio native dependency. Smaller install footprint than gRPC variant. Default endpoint `http://localhost:4318` works with any OTEL Collector. |
| `opentelemetry-instrumentation-fastapi` | `>=0.63b0` | Auto-instrument FastAPI inbound requests | Creates spans for every REST route + WebSocket upgrade with zero manual code. Latest beta (0.63b1, May 2026) supports Python 3.10-3.14. |
| `opentelemetry-instrumentation-httpx` | `>=0.63b0` | Auto-instrument httpx outbound calls | Wraps both `httpx.Client` and `httpx.AsyncClient` — traces every GraphQL request to upstream. Supports request/response hooks for adding custom attributes (query hash, error_class). |

**Rationale — HTTP exporter over gRPC:** `opentelemetry-exporter-otlp-proto-grpc` pulls in `grpcio` (~35 MB compiled wheel with C extension). For a brick that ships cross-platform wheels via cibuildwheel, adding a grpcio build matrix is a maintenance burden with zero functional benefit. HTTP/proto is the OTEL community's recommended lightweight path and is the default since OTEL Collector 0.90+.

**Integration points:**
- `server.py` (composition root): Initialize `TracerProvider` + `MeterProvider` with OTLP exporter, instrument FastAPI app and httpx clients.
- `HttpTransport` / `AsyncHttpTransport`: Add custom span attributes (`graphql.operation_type`, `graphql.error_class`, `graphql.query_hash`).
- `config.py`: Add `GRAPHQL_OTEL_ENABLED=false` (opt-in), `GRAPHQL_OTEL_SERVICE_NAME`, `GRAPHQL_OTEL_ENDPOINT` env vars.
- Domain code (`query_service.py`, `schema_service.py`): Use `opentelemetry.api.trace.get_tracer()` for manual spans on schema resolution and query classification. API-only — no SDK linkage.

**What NOT to add:**
- ~~`opentelemetry-instrumentation-logging`~~ — We'll bridge structured logging via `opentelemetry-api` log bridge directly; the logging instrumentor is too heavy for this use case.
- ~~`opentelemetry-exporter-otlp-proto-grpc`~~ — grpcio binary bloat, unnecessary.
- ~~`opentelemetry-distro`~~ — Auto-detection magic; we want explicit instrumentation for predictable behavior.

**Confidence:** HIGH — Versions verified via PyPI (`pip index versions`); Context7 docs confirm FastAPI + httpx instrumentation patterns.

---

### 2. Security Hardening — mTLS, Rate Limiting, Input Validation

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `truststore` | `>=0.10,<1` | System CA store for mTLS client verification | Lets httpx use OS-native certificate stores (macOS Keychain, Windows CertStore, Linux system CA) instead of bundled certifi. Critical for enterprise mTLS where custom CA chains are common. |
| `slowapi` | `>=0.1.10,<1` | FastAPI rate limiting middleware | Thin wrapper over `limits` library. Decorator-based (`@limiter.limit("10/minute")`), integrates with FastAPI's `Request` object. Only ~200 lines of code — auditable and minimal. |

**What we implement in-house (no new dependencies):**
- **mTLS client cert passing:** httpx already supports `ssl_context` via `httpx.Client(verify=ssl_context)`. We add `GRAPHQL_CLIENT_CERT` / `GRAPHQL_CLIENT_KEY` env vars to `config.py` and construct `ssl.SSLContext` in transport constructor. Zero new deps.
- **Token rotation:** Implement a `TokenProvider` protocol in `ports/` with a `RefreshableTokenProvider` adapter that refreshes bearer tokens before expiry. Uses existing `httpx` + `pydantic`. No new deps.
- **RBAC header forwarding:** Pass-through of `Authorization`, `X-User-Id`, `X-Roles` headers from inbound request to outbound GraphQL call. Pure FastAPI `Request.headers` → httpx `headers` dict. No new deps.
- **Audit logging:** Structured JSON logging using Python stdlib `logging` with `orjson` formatter. Feed into OTEL log bridge. No new deps.
- **Input validation / query depth limiting:** Implement using `graphql-core`'s `DocumentNode` visitor (already a dependency). Add `GRAPHQL_MAX_QUERY_DEPTH` and `GRAPHQL_MAX_QUERY_COMPLEXITY` config options. No new deps.

**Rationale — No `python-jose`/`PyJWT` for token validation:** This brick is a **client** that forwards tokens, not a service that validates them. The upstream GraphQL gateway handles authz. Adding JWT validation would violate the brick's read-only-passthrough contract.

**Confidence:** HIGH for truststore (PyPI verified 0.10.4); MEDIUM for slowapi (0.1.10 is stable but version <1 — evaluate if simple in-house ASGI middleware is lighter).

---

### 3. GraphQL Subscriptions — WebSocket + SSE

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `websockets` | `>=14,<17` | WebSocket protocol (graphql-ws subprotocol) | gql 4.0 uses `websockets` for its `WebsocketsTransport`. Latest is 16.0. Needed for subscription client (outbound). For inbound, Starlette (bundled with FastAPI) provides `WebSocket` class natively. |
| `sse-starlette` | `>=3.4,<4` | Server-Sent Events for subscription fallback | W3C-compliant SSE implementation for FastAPI/Starlette. Production-ready (v3.4.4). Handles client disconnect detection, graceful shutdown, send timeouts. Perfect for environments where WebSocket is blocked (corporate proxies). |

**Architecture decision — Client vs Server subscriptions:**

This brick operates in two subscription modes:

1. **Client mode (outbound):** `AsyncGraphQLClient.subscribe()` opens a WebSocket to the upstream GraphQL gateway using gql's `WebsocketsTransport`. This is the primary use case — the investigator subscribes to live data streams.

2. **Server mode (inbound):** The REST/FastAPI face exposes subscriptions to downstream consumers via:
   - **WebSocket endpoint** (`/ws/graphql`) — Starlette's built-in WebSocket support, implementing the `graphql-ws` protocol server-side. No extra deps.
   - **SSE endpoint** (`/graphql/subscribe`) — Uses `sse-starlette` to stream subscription events as SSE. Fallback for HTTP-only clients.

**What NOT to add:**
- ~~`graphql-ws` (Python package)~~ — Dead project. Last release 2021, Python 2 support, tied to Graphene. Don't use.
- ~~`ariadne`~~ — Full GraphQL server framework (1.1.0, very active, has subscriptions + OTEL). But this brick doesn't serve a GraphQL schema — it's a *client* that proxies to an upstream server. Adding Ariadne would be architectural overreach.
- ~~`strawberry-graphql`~~ — Same reasoning as Ariadne. We're a client, not a server.

**Integration points:**
- New port: `ports/subscription.py` — `AsyncSubscriptionTransport` protocol.
- New outbound adapter: `adapters/outbound/ws_transport.py` — Wraps gql's `WebsocketsTransport`.
- New inbound adapter: `adapters/inbound/ws_subscription.py` — Starlette WebSocket handler implementing `graphql-ws` protocol.
- New inbound adapter: `adapters/inbound/sse_subscription.py` — SSE handler using `sse-starlette`.
- `AsyncGraphQLClient` gets `.subscribe(query, variables)` → `AsyncIterator[SubscriptionEvent]`.

**Confidence:** HIGH — gql 4.0 verified installed, websockets/sse-starlette versions confirmed on PyPI.

---

### 4. DX & CI — PyPI Publishing Pipeline

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pypa/gh-action-pypi-publish` | `release/v1` | GitHub Action: OIDC-based PyPI publish | Trusted Publishing — no API tokens needed. GitHub OIDC identity → PyPI short-lived token. Already the standard for maturin-built projects. |
| `pypa/cibuildwheel` | `v2.23` (existing) | Multi-platform wheel builds | Already in CI. No changes needed — just wire the upload artifact → publish step. |

**CI Workflow additions (`.github/workflows/publish.yml`):**

```yaml
# Triggered on GitHub Release (tag push)
on:
  release:
    types: [published]

jobs:
  # Reuse existing wheels/sdist jobs from ci.yml
  publish:
    needs: [wheels, sdist]
    runs-on: ubuntu-latest
    environment: pypi                    # GitHub Environment with protection rules
    permissions:
      id-token: write                    # MANDATORY for Trusted Publishing
    steps:
      - uses: actions/download-artifact@v4  # Download all wheel + sdist artifacts
      - uses: pypa/gh-action-pypi-publish@release/v1
```

**What NOT to add:**
- ~~`twine`~~ — Superseded by `gh-action-pypi-publish` with Trusted Publishing.
- ~~Manual PyPI API tokens~~ — OIDC eliminates secret management.
- ~~TestPyPI step~~ — Can be added later; v2.0 ships to PyPI directly with release tag gating.

**Additional CI enhancements:**
- Add `pytest-xdist` (`>=3.5`) for parallel test execution — the test suite is growing with subscription + OTEL tests.
- Add `coverage` reporting via existing `pytest-cov` — add `--cov-fail-under=80` to CI.

**Confidence:** HIGH — PyPI Trusted Publishing docs verified. Workflow pattern confirmed.

---

### 5. Copier Template Extraction

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `copier` | `>=9.15,<10` | Project template generation & updates | Copier (not Cookiecutter) because: (1) supports `copier update` to replay template changes onto existing projects (kafka-mcp, ordering-mcp), (2) Jinja2 templating with conditional questions, (3) typed answers file (`.copier-answers.yml`), (4) PROJECT.md already documents this decision (D: "Copier for template extraction"). |

**Template structure (`template/`):**

```
template/
  copier.yml                    # Questions: brick_name, description, has_rust, has_subscriptions, has_otel
  {{brick_name}}/
    pyproject.toml.jinja        # Templated with optional-dependencies conditional on features
    src/{{brick_name}}/
      __init__.py
      config.py.jinja
      domain/
      ports/
      adapters/
        inbound/
        outbound/
    native/                     # Conditional: only if has_rust == true
    tests/
    .github/workflows/
      ci.yml.jinja
      publish.yml.jinja
    Dockerfile.jinja
```

**Key copier.yml questions:**
- `brick_name` (str): Python package name (e.g., `kafka_mcp`)
- `brick_description` (str): One-line description
- `has_rust_native` (bool): Include pyo3/maturin native module
- `has_subscriptions` (bool): Include WebSocket + SSE subscription support
- `has_otel` (bool): Include OpenTelemetry instrumentation
- `python_versions` (list): Target Python versions for CI matrix

**What NOT to add:**
- ~~`cookiecutter`~~ — No `update` command. One-shot generation only.
- ~~`cruft`~~ — Abandoned wrapper over cookiecutter. Copier does it natively.

**Note:** Copier is a **dev-time tool**, not a runtime dependency. It goes in development docs, not in `pyproject.toml` dependencies.

**Confidence:** HIGH — Copier 9.15.2 verified on PyPI, Context7 docs confirm Jinja templating + `copier.yml` configuration.

---

## Summary: New Optional Dependencies in pyproject.toml

```toml
[project.optional-dependencies]
# ... existing extras unchanged ...

otel = [
    "opentelemetry-api>=1.42,<2",
    "opentelemetry-sdk>=1.42,<2",
    "opentelemetry-exporter-otlp-proto-http>=1.42,<2",
    "opentelemetry-instrumentation-fastapi>=0.63b0",
    "opentelemetry-instrumentation-httpx>=0.63b0",
]

security = [
    "truststore>=0.10,<1",
    "slowapi>=0.1.10,<1",
]

subscriptions = [
    "websockets>=14,<17",
    "sse-starlette>=3.4,<4",
]

all = [
    "generic-graphql-mcp[server,mcp,cli,otel,security,subscriptions]",
]

dev = [
    # ... existing dev deps ...
    "pytest-xdist>=3.5",       # Parallel test execution
]
```

**Design principle:** All v2.0 features are **optional extras**. The core library (`from generic_graphql_mcp import GraphQLClient`) keeps its minimal dependency footprint. Features activate based on installed extras + config flags.

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| OTEL exporter | `otlp-proto-http` | `otlp-proto-grpc` | grpcio adds ~35 MB binary dep + cibuildwheel complexity |
| Rate limiting | `slowapi` | In-house ASGI middleware | slowapi is 200 LOC, well-tested; reimplementing wastes time. **Revisit** if slowapi's `limits` dep causes conflicts. |
| SSE | `sse-starlette` | Raw `StreamingResponse` | sse-starlette handles reconnection, keep-alive, W3C compliance, disconnect detection. Not worth reimplementing. |
| Subscriptions client | gql `WebsocketsTransport` | Raw `websockets` | gql already handles graphql-ws protocol negotiation, keep-alive, subscription lifecycle. Already a dependency. |
| WS server protocol | In-house `graphql-ws` impl on Starlette | `ariadne` / `strawberry` | We're a proxy, not a schema server. Full GQL frameworks are overkill for relaying subscription events. |
| Template engine | `copier` | `cookiecutter` | No `update` support. Can't replay template changes. |
| PyPI publish | Trusted Publishing (OIDC) | API token | OIDC eliminates secret rotation. Industry best practice since 2024. |
| Token rotation | In-house `TokenProvider` port | `authlib` | authlib is 10K+ LOC. We need a simple "refresh before expiry" pattern — 50 lines of code. |
| mTLS | stdlib `ssl.SSLContext` + `truststore` | `certifi` bundle management | truststore uses OS CA store. certifi requires manual bundle updates. |

---

## Version Verification Matrix

| Package | PyPI Latest | Verified Date | Confidence |
|---------|-------------|---------------|------------|
| `opentelemetry-api` | 1.42.1 | 2026-06-16 | HIGH (pip index) |
| `opentelemetry-sdk` | 1.42.1 | 2026-06-16 | HIGH (pip index) |
| `opentelemetry-exporter-otlp-proto-http` | 1.42.1 | 2026-06-16 | HIGH (pip index) |
| `opentelemetry-exporter-otlp-proto-grpc` | 1.42.1 | 2026-06-16 | HIGH (pip index, not used) |
| `opentelemetry-instrumentation-fastapi` | 0.63b1 | 2026-06-16 | HIGH (PyPI page) |
| `opentelemetry-instrumentation-httpx` | 0.63b1 | 2026-06-16 | HIGH (PyPI page) |
| `truststore` | 0.10.4 | 2026-06-16 | HIGH (pip index) |
| `slowapi` | 0.1.10 | 2026-06-16 | HIGH (pip index) |
| `websockets` | 16.0 | 2026-06-16 | HIGH (pip index) |
| `sse-starlette` | 3.4.4 | 2026-06-16 | HIGH (pip index) |
| `gql` | 4.0.0 | 2026-06-16 | HIGH (pip show, installed) |
| `copier` | 9.15.2 | 2026-06-16 | HIGH (pip index) |

---

## Integration Dependency Graph

```
                    ┌─────────────────┐
                    │  pyproject.toml │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
    [otel] extra      [subscriptions]     [security] extra
          │              extra                  │
          ▼                  │                  ▼
  ┌───────────────┐         │         ┌──────────────┐
  │ otel-api      │         │         │ truststore   │
  │ otel-sdk      │    ┌────┴────┐    │ slowapi      │
  │ otel-exporter │    │         │    └──────────────┘
  │ otel-fastapi  │    ▼         ▼           │
  │ otel-httpx    │ websockets  sse-       Integrates
  └───────┬───────┘ (gql uses)  starlette    with
          │              │         │      ┌──────────┐
          │              │         │      │ config.py│
          │              │         │      │ rest.py  │
          ▼              ▼         ▼      └──────────┘
    ┌─────────┐   ┌──────────┐  ┌──────────┐
    │server.py│   │ws_trans- │  │sse_sub-  │
    │(comp.   │   │port.py   │  │scription │
    │ root)   │   │(outbound)│  │.py       │
    └─────────┘   └──────────┘  │(inbound) │
                                └──────────┘
```

---

## Sources

- OpenTelemetry Python SDK: Context7 `/open-telemetry/opentelemetry.io` — instrumentation patterns, exporter config
- OpenTelemetry instrumentation-httpx: PyPI project page (0.63b1, May 2026) — usage examples, hook API
- OpenTelemetry instrumentation-fastapi: PyPI project page (0.63b1, May 2026) — auto-instrumentation
- gql WebSocket subscriptions: Context7 `/graphql-python/gql` — WebsocketsTransport, subscribe() API
- sse-starlette: Context7 `/sysid/sse-starlette` — EventSourceResponse, disconnect handling
- Starlette WebSocket: Context7 `/kludex/starlette` — WebSocketRoute, WebSocketEndpoint
- Copier configuration: Context7 `/copier-org/copier` — copier.yml, Jinja templating, _external_data
- PyPI Trusted Publishing: docs.pypi.org/trusted-publishers/using-a-publisher/ — OIDC workflow for GitHub Actions
- All version numbers: `pip index versions <package>` on 2026-06-16
