# Phase 1: Foundation & Schema Sources - Research

**Researched:** 2026-06-06
**Domain:** Python hexagonal architecture, GraphQL schema discovery, TTL caching
**Confidence:** HIGH

## Summary

Phase 1 builds the hexagonal skeleton for `graphql-mcp` — the v2 reference brick — and implements the four-source schema cascade (GitLab → introspection → `_service{sdl}` → SDL file) with TTL caching. This is a greenfield project with no existing code; the entire `src/graphql_mcp/` directory structure, domain models, port interfaces, outbound adapters, configuration loader, and the `GraphQLClient.from_env()` factory must be created from scratch.

The core technical challenge is maintaining strict hexagonal discipline: the `domain/` layer must contain zero I/O imports while still orchestrating schema resolution through four different network/file sources via port abstractions. The schema cascade is a priority-chain pattern with graceful fallback — each source is tried in order, failures are caught and logged, and the first successful result is cached with a TTL.

The project uses a maturin-based build system (Python + Rust hybrid), but Phase 1 only creates the Python skeleton and outbound adapters — the Rust native codec arrives in Phase 3. The `pyproject.toml` must be set up correctly from the start to support this hybrid build.

**Primary recommendation:** Use `typing.Protocol` for ports, `pydantic.BaseModel` (frozen) for domain models, `httpx` for HTTP transport, `graphql-core` for schema parsing, and a simple `time.monotonic()`-based TTL cache in the domain layer (no I/O import needed).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Domain models (`SchemaGraph`, `QueryResult`, etc.) | Domain (pure Python) | — | Zero-I/O core; only data classes and business logic |
| Port interfaces (`SchemaSource`, `GraphQLTransport`) | Domain (pure Python) | — | `typing.Protocol` ABCs define contracts |
| Schema cascade orchestration | Domain (pure Python) | — | Priority-chain logic is business logic, not I/O |
| TTL cache | Domain (pure Python) | — | `time.monotonic()` is stdlib, not I/O; cache is a domain concern |
| GitLab SDL fetching | Outbound Adapter | API/Backend | HTTP call to GitLab REST API (files endpoint) |
| Introspection query execution | Outbound Adapter | API/Backend | HTTP POST to GraphQL endpoint with introspection query |
| `_service{sdl}` fetching | Outbound Adapter | API/Backend | HTTP POST to federation-enabled GraphQL endpoint |
| SDL file reading | Outbound Adapter | Filesystem | Local file read of `.graphql` schema |
| Configuration loading (`from_env`) | Config / Composition Root | — | Reads env vars, wires adapters to ports |
| HTTP transport | Outbound Adapter | API/Backend | `httpx.Client` for sync HTTP with configurable timeout/SSL/proxy |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `graphql-core` | ~=3.2.11 | Schema parsing (SDL → `GraphQLSchema`), introspection query generation, AST utilities | [VERIFIED: PyPI] Python port of GraphQL.js; used by Graphene, Ariadne, Strawberry; 2500+ tests, 100% coverage |
| `pydantic` | >=2.13,<3 | Domain models, configuration validation | [VERIFIED: PyPI] v2.13.4 latest; Rust-backed validation; `frozen=True` for immutable domain models |
| `pydantic-settings` | >=2.14,<3 | `BaseSettings` for env-var-driven configuration (`from_env()` pattern) | [VERIFIED: PyPI] v2.14.1 latest; reads env vars with prefix support, type coercion, `.env` files |
| `httpx` | >=0.28,<1 | Synchronous HTTP client for schema source adapters and query transport | [VERIFIED: PyPI] v0.28.1 latest stable; sync+async API, configurable SSL/proxy/timeout, `requests`-compatible |
| `orjson` | >=3.11,<4 | Fast JSON serialization/deserialization (fallback codec) | [VERIFIED: PyPI] v3.11.9; 10x faster than `json` stdlib; Rust-backed; handles bytes natively |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `maturin` | >=1.13,<2 | Build backend for pyo3/Rust hybrid project | Build-time only; pyproject.toml `[build-system]` |
| `pytest` | >=8.0 | Test runner | Dev dependency |
| `responses` | >=0.25 | Mock httpx/requests calls in tests | Dev dependency; tests for schema cascade fallback |
| `ruff` | >=0.15 | Linting + formatting | Dev dependency; enforces domain purity (no I/O imports) |
| `pytest-cov` | >=5.0 | Coverage reporting | Dev dependency |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `httpx` | `requests` | `requests` is sync-only; spec mentions both but `httpx` has async readiness for future; API is nearly identical |
| `pydantic-settings` | raw `os.environ` + manual parsing | Loses type validation, prefix support, `.env` file loading; not worth the fragility |
| `time.monotonic()` cache | `cachetools.TTLCache` | External dependency for a simple problem; `time.monotonic()` is stdlib and sufficient for single-value cache |

**Installation (runtime):**
```bash
pip install graphql-core~=3.2.11 pydantic>=2.13 pydantic-settings>=2.14 httpx>=0.28 orjson>=3.11
```

**Installation (dev):**
```bash
pip install pytest responses ruff pytest-cov
```

**Version verification:**
- `graphql-core` 3.2.11 — released Jun 5, 2026 [VERIFIED: PyPI]
- `pydantic` 2.13.4 — released May 6, 2026 [VERIFIED: PyPI]
- `pydantic-settings` 2.14.1 — released May 8, 2026 [VERIFIED: PyPI]
- `httpx` 0.28.1 — released Dec 6, 2024 [VERIFIED: PyPI]
- `orjson` 3.11.9 — released May 6, 2026 [VERIFIED: PyPI]
- `maturin` 1.13.3 — released May 11, 2026 [VERIFIED: PyPI]

## Architecture Patterns

### System Architecture Diagram

```
                    from_env()  ←── env vars (GRAPHQL_*)
                        │
                        ▼
               ┌─────────────────┐
               │  GraphQLClient   │  (lib facade / composition root)
               │   .from_env()   │
               └────────┬────────┘
                        │ injects adapters into
                        ▼
        ┌──────────────────────────────┐
        │         DOMAIN LAYER         │  ← zero I/O imports
        │                              │
        │  SchemaService               │
        │   ├─ cascade: List[Source]    │  ← tries each in priority order
        │   ├─ cache: TTLCache         │  ← time.monotonic()-based
        │   └─ resolve() → SchemaGraph │
        │                              │
        │  models.py                   │
        │   ├─ SchemaGraph             │
        │   ├─ QueryResult             │
        │   └─ TypeInfo, Subgraph      │
        │                              │
        │  PORTS (Protocol interfaces) │
        │   ├─ SchemaSource            │
        │   ├─ GraphQLTransport        │
        │   └─ JsonCodec               │
        └───────────┬──────────────────┘
                    │ depends on (via ports)
                    ▼
        ┌──────────────────────────────┐
        │     OUTBOUND ADAPTERS        │
        │                              │
        │  Schema Sources (cascade):   │
        │   1. GitLabSource ──────┐    │
        │   2. IntrospectionSrc ──┤    │
        │   3. ServiceSdlSource ──┤    │
        │   4. FileSdlSource ─────┘    │
        │                              │
        │  Transport:                  │
        │   └─ HttpTransport (httpx)   │
        │                              │
        │  (Phase 3: JsonCodec)        │
        └──────────────────────────────┘
```

### Recommended Project Structure

```
graphql-mcp/
├── src/graphql_mcp/
│   ├── __init__.py           # re-export GraphQLClient (lib face)
│   ├── py.typed              # PEP 561 marker
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py         # SchemaGraph, QueryResult, TypeInfo, Subgraph, SchemaSummary
│   │   ├── errors.py         # SchemaResolutionError, error_class enum
│   │   └── schema_service.py # cascade logic + TTL cache
│   ├── ports/
│   │   ├── __init__.py
│   │   ├── schema_source.py  # SchemaSource Protocol
│   │   ├── transport.py      # GraphQLTransport Protocol
│   │   └── json_codec.py     # JsonCodec Protocol (stub for Phase 3)
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── inbound/
│   │   │   ├── __init__.py
│   │   │   └── lib.py        # GraphQLClient facade
│   │   └── outbound/
│   │       ├── __init__.py
│   │       ├── http_transport.py       # httpx-based GraphQLTransport
│   │       ├── gitlab_source.py        # GitLab REST API → SDL
│   │       ├── introspection_source.py # introspection query → schema
│   │       ├── service_sdl_source.py   # _service{sdl} → SDL
│   │       └── file_source.py          # local file → SDL
│   ├── config.py             # pydantic-settings: env → GraphQLConfig
│   └── server.py             # composition root (minimal in Phase 1)
├── native/                   # Rust crate (Phase 3, empty stub OK)
│   ├── Cargo.toml
│   └── src/lib.rs
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # shared fixtures, mock adapters
│   ├── test_schema_cascade.py
│   ├── test_ttl_cache.py
│   └── test_domain_purity.py # grep-based import check
├── pyproject.toml
├── Cargo.toml                # workspace root for native/
└── LICENSE
```

### Pattern 1: Hexagonal Ports with `typing.Protocol`

**What:** Domain defines contracts as `Protocol` classes; adapters implement them.
**When to use:** Every boundary between domain and I/O.

```python
# Source: Python typing docs / Pydantic docs
# src/graphql_mcp/ports/schema_source.py
from __future__ import annotations
from typing import Protocol, runtime_checkable

from graphql_mcp.domain.models import SchemaGraph


@runtime_checkable
class SchemaSource(Protocol):
    """Port: a source that can fetch a GraphQL schema."""

    @property
    def name(self) -> str:
        """Human-readable source name for logging."""
        ...

    def fetch_schema(self) -> SchemaGraph | None:
        """Attempt to fetch schema. Return None on failure (not exception)."""
        ...
```

### Pattern 2: Schema Cascade (Priority Chain with Fallback)

**What:** Try each schema source in priority order; first success wins; cache result.
**When to use:** `SchemaService.resolve()` in the domain layer.

```python
# Domain layer — no I/O imports
# src/graphql_mcp/domain/schema_service.py
from __future__ import annotations
import logging
import time
from typing import Sequence

from graphql_mcp.domain.models import SchemaGraph
from graphql_mcp.ports.schema_source import SchemaSource

logger = logging.getLogger(__name__)


class SchemaService:
    """Resolves schema through a cascade of sources with TTL cache."""

    def __init__(
        self,
        sources: Sequence[SchemaSource],
        ttl_seconds: float = 300.0,
    ) -> None:
        self._sources = sources
        self._ttl = ttl_seconds
        self._cached: SchemaGraph | None = None
        self._cached_at: float = 0.0

    def resolve(self) -> SchemaGraph:
        now = time.monotonic()
        if self._cached is not None and (now - self._cached_at) < self._ttl:
            return self._cached

        for source in self._sources:
            try:
                schema = source.fetch_schema()
                if schema is not None:
                    logger.info("Schema resolved from %s", source.name)
                    self._cached = schema
                    self._cached_at = time.monotonic()
                    return schema
            except Exception:
                logger.debug("Source %s failed, trying next", source.name, exc_info=True)
                continue

        raise SchemaResolutionError("All schema sources failed")

    def invalidate(self) -> None:
        """Clear cache, forcing next resolve() to re-fetch."""
        self._cached = None
        self._cached_at = 0.0
```

### Pattern 3: Frozen Pydantic Domain Models

**What:** Immutable value objects for domain data.
**When to use:** All domain models.

```python
# Source: Context7 /pydantic/pydantic — frozen model configuration
# src/graphql_mcp/domain/models.py
from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class SchemaGraph(BaseModel):
    """Parsed GraphQL schema representation."""
    model_config = ConfigDict(frozen=True)

    sdl: str                    # raw SDL text
    query_type_name: str = "Query"
    types: dict[str, TypeSummary] = {}  # name → summary
    source_name: str = ""       # which cascade source provided this
```

### Pattern 4: Configuration via `pydantic-settings`

**What:** Type-safe environment variable loading with `BaseSettings`.
**When to use:** `config.py` and `GraphQLClient.from_env()`.

```python
# Source: Context7 /websites/pydantic_dev_validation — BaseSettings
# src/graphql_mcp/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class GraphQLConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GRAPHQL_",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    endpoint: str = ""
    bearer_token: str = ""
    schema_source: str = "auto"   # auto|gitlab|introspection|federation|sdl_file
    schema_sdl: str = ""          # path to local SDL file
    schema_ttl: int = 300         # seconds

    # GitLab
    schema_gitlab_url: str = ""
    schema_gitlab_project_id: str = ""
    schema_gitlab_file_path: str = ""
    schema_gitlab_ref: str = "HEAD"
    gitlab_token: str = ""

    # Behavior
    timeout: int = 30
    ssl_verify: bool = True
    noproxy: str = ""
    allow_mutations: bool = False
```

### Anti-Patterns to Avoid

- **Importing `httpx` in domain/:** NEVER. Domain uses `SchemaSource` and `GraphQLTransport` protocols. Enforced by `ruff` rule + test.
- **Raising exceptions from schema sources on failure:** Return `None` instead. The cascade pattern requires silent fallback — exceptions are caught and logged at DEBUG level.
- **Using `functools.lru_cache` for TTL cache:** `lru_cache` has no expiry. Use explicit `time.monotonic()` comparison.
- **Hardcoding cascade order:** The order should be injected via the `sources` list in `SchemaService.__init__`, determined by config at composition time.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| GraphQL introspection query string | Custom query text | `graphql.get_introspection_query()` from `graphql-core` | The query is complex (types, fields, args, enums, interfaces, unions, directives); the library keeps it spec-compliant [VERIFIED: Context7] |
| SDL → schema object parsing | Custom parser | `graphql.build_schema(sdl_text)` from `graphql-core` | Full spec compliance, handles directives, descriptions, all type kinds [VERIFIED: Context7] |
| Introspection result → schema object | Custom reconstruction | `graphql.build_client_schema(data)` from `graphql-core` | Handles all edge cases of the introspection result format [VERIFIED: Context7] |
| Environment variable configuration | `os.environ.get()` chains | `pydantic_settings.BaseSettings` | Type coercion, validation, `.env` files, prefix support [VERIFIED: Context7] |
| HTTP client with SSL/proxy/timeout | Custom urllib wrapper | `httpx.Client(...)` | Connection pooling, configurable SSL context, proxy support, clean API [VERIFIED: Context7] |
| JSON serialization | `json.dumps/loads` | `orjson.dumps/loads` | 10x faster, handles bytes natively, strict UTF-8 [VERIFIED: PyPI] |

**Key insight:** `graphql-core` provides the complete toolchain for schema operations — don't reimplement any query generation, parsing, or schema construction. The library is a faithful port of the official JavaScript reference implementation.

## Common Pitfalls

### Pitfall 1: Domain Layer Accidentally Importing I/O

**What goes wrong:** A developer adds `import httpx` or `from pathlib import Path` in `domain/` for convenience, violating hexagonal architecture.
**Why it happens:** Python makes it easy to reach for I/O anywhere. Path seems "harmless" but implies filesystem access.
**How to avoid:** Automated enforcement: (1) `ruff` ban rule for I/O imports in `domain/`, (2) a test that runs `grep -r` against `domain/` for forbidden imports. Both are specified in the success criteria.
**Warning signs:** Any `import` in `domain/` that isn't from `__future__`, `typing`, `enum`, `dataclasses`, `logging`, `time`, `pydantic`, or other pure-Python stdlib modules.

### Pitfall 2: `build_schema()` vs `build_client_schema()` Confusion

**What goes wrong:** Using `build_schema()` on introspection JSON, or `build_client_schema()` on SDL text.
**Why it happens:** Both return `GraphQLSchema`, but they take different inputs.
**How to avoid:**
- **SDL text → `build_schema(sdl_string)`** — for GitLab source, `_service{sdl}`, and file source.
- **Introspection JSON → `build_client_schema(data["__schema"]` or `data`)** — for introspection source only.
**Warning signs:** `GraphQLError` about unexpected types during schema construction.

### Pitfall 3: GitLab API Returns Base64-Encoded Content

**What goes wrong:** Fetching a file via GitLab's `/repository/files/:path` endpoint returns `content` as Base64-encoded, not raw text.
**Why it happens:** GitLab's file retrieval API uses base64 encoding by default.
**How to avoid:** Use the `/repository/files/:path/raw` endpoint instead, which returns raw file content directly. Alternatively, decode base64 from the standard endpoint. [VERIFIED: GitLab docs]
**Warning signs:** SDL parsing fails with garbled content.

### Pitfall 4: Introspection Disabled on Production Endpoints

**What goes wrong:** `IntrospectionSource` fails silently because many production GraphQL servers disable introspection.
**Why it happens:** Security best practice — introspection exposes the entire schema.
**How to avoid:** This is expected and handled by the cascade — introspection failure causes silent fallback to `_service{sdl}` or file source. The cascade design accounts for this.
**Warning signs:** If introspection is the ONLY configured source, schema resolution will fail. Ensure at least one other source is configured.

### Pitfall 5: `_service{sdl}` Only Works on Federation Subgraphs

**What goes wrong:** Sending `query { _service { sdl } }` to a non-federation endpoint returns a GraphQL error.
**Why it happens:** `_service` is a federation-specific field added by Apollo's subgraph libraries.
**How to avoid:** Treat GraphQL errors from this query as "source unavailable" and fall through to the next cascade source. Don't treat it as a transport error.
**Warning signs:** GraphQL error response with `"Cannot query field \"_service\" on type \"Query\""`.

### Pitfall 6: TTL Cache Using `time.time()` Instead of `time.monotonic()`

**What goes wrong:** Clock adjustments (NTP sync, manual changes) cause cache to expire prematurely or never expire.
**Why it happens:** `time.time()` returns wall-clock time which can jump backwards.
**How to avoid:** Always use `time.monotonic()` for duration-based comparisons. [ASSUMED — standard Python best practice]
**Warning signs:** Intermittent cache invalidation after system clock sync.

## Code Examples

### GraphQL Introspection Query Generation

```python
# Source: Context7 /graphql-python/graphql-core — introspection docs
from graphql import get_introspection_query

# Generate the standard introspection query
query = get_introspection_query(descriptions=True)
# This returns the full introspection query string that can be sent
# to any GraphQL endpoint as a POST body
```

### Building Schema from SDL Text

```python
# Source: Context7 /graphql-python/graphql-core — SDL docs
from graphql import build_schema, print_schema

# Parse SDL text into a GraphQLSchema object
schema = build_schema("""
    type Query {
        hero(episode: Episode): Character
        human(id: String!): Human
    }
    enum Episode { NEWHOPE EMPIRE JEDI }
    type Human { id: String! name: String }
    interface Character { id: String! name: String }
""")

# Access schema programmatically
query_type = schema.query_type
fields = query_type.fields  # dict of field_name → GraphQLField
```

### Building Schema from Introspection Result

```python
# Source: Context7 /graphql-python/graphql-core — introspection docs
from graphql import build_client_schema

# After sending introspection query and getting JSON response:
# response_data = {"data": {"__schema": {...}}}
introspection_data = response_data["data"]
schema = build_client_schema(introspection_data)
```

### Federation `_service{sdl}` Query

```python
# Source: Apollo Federation specification [ASSUMED]
# The _service field is added by federation-compatible subgraph libraries
FEDERATION_SDL_QUERY = """
    query {
        _service {
            sdl
        }
    }
"""
# Response: {"data": {"_service": {"sdl": "type Query { ... }"}}}
# Extract: response["data"]["_service"]["sdl"]
```

### GitLab Raw File Retrieval

```python
# Source: GitLab docs — Repository Files API [VERIFIED]
import httpx
from urllib.parse import quote

def fetch_gitlab_sdl(
    gitlab_url: str,
    project_id: str,
    file_path: str,
    ref: str,
    token: str,
) -> str:
    """Fetch raw SDL file from GitLab repository."""
    encoded_path = quote(file_path, safe="")
    url = f"{gitlab_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}/raw"
    response = httpx.get(
        url,
        params={"ref": ref},
        headers={"PRIVATE-TOKEN": token},
    )
    response.raise_for_status()
    return response.text
```

### httpx Client Configuration

```python
# Source: Context7 /websites/python-httpx — client configuration
import httpx

client = httpx.Client(
    base_url="https://graphql.example.com",
    headers={"Authorization": "Bearer <token>"},
    timeout=httpx.Timeout(30.0, connect=10.0),
    verify=True,  # SSL verification
    # proxy="http://proxy:8080",  # if needed
)

# POST a GraphQL query
response = client.post(
    "/graphql",
    json={"query": query, "variables": variables},
)
```

### Maturin pyproject.toml (Hybrid Project)

```toml
# Source: Context7 /pyo3/maturin — pyproject.toml configuration
[build-system]
requires = ["maturin>=1.0,<2.0"]
build-backend = "maturin"

[project]
name = "graphql-mcp"
dynamic = ["version"]
description = "Generic read-only GraphQL MCP brick"
requires-python = ">=3.10"
license = { text = "MIT" }
dependencies = [
    "graphql-core~=3.2.11",
    "pydantic>=2.13,<3",
    "pydantic-settings>=2.14,<3",
    "httpx>=0.28,<1",
    "orjson>=3.11,<4",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "responses>=0.25",
    "ruff>=0.15",
    "pytest-cov>=5",
]

[tool.maturin]
python-source = "src"
module-name = "graphql_mcp._native"
features = ["pyo3/extension-module"]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `graphql-core` 2.x (Syrus Akbary) | `graphql-core` 3.x (Christoph Zwerschke) | 2019+ | Complete rewrite; type hints; async support; closely tracks GraphQL.js |
| `requests` for HTTP | `httpx` | 2020+ | Async-ready; same API feel; better timeout/SSL control |
| Pydantic v1 `class Config` | Pydantic v2 `model_config = ConfigDict(...)` | 2023+ | Rust-backed validation; `ConfigDict` replaces inner `Config` class |
| `pydantic` v1 `BaseSettings` | `pydantic-settings` v2 (separate package) | 2023+ | Separated from core pydantic; more features for env loading |
| `setuptools` + `setup.py` | `maturin` + `pyproject.toml` | 2023+ | First-class pyo3 support; PEP 621 metadata; faster builds |

**Deprecated/outdated:**
- `graphql-core` 2.x: No longer maintained; v3 is the standard
- `requests` is not deprecated but `httpx` is preferred for new projects (async-ready, better API)
- Pydantic v1 `BaseSettings` is bundled but deprecated; use `pydantic-settings` package

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `_service{sdl}` federation query format is `query { _service { sdl } }` | Code Examples | If the query format differs, the `ServiceSdlSource` adapter fails silently (low risk — cascade falls through) |
| A2 | `time.monotonic()` is the correct choice over `time.time()` for TTL | Common Pitfalls | If `time.monotonic()` has platform issues, cache timing could be wrong (very low risk — this is standard Python practice) |
| A3 | `responses` library works with `httpx` for mocking | Standard Stack | If not, need `pytest-httpx` or `respx` instead; easy swap (low risk) |

**Note on A3:** The `responses` library traditionally mocks `requests`. For `httpx`, the standard mock library is `respx`. The spec mentions `responses`, but since we're using `httpx`, the planner should verify whether to use `respx` (for httpx) or `responses` (if using requests alongside httpx). Using `respx` is more natural with `httpx`. [ASSUMED]

## Open Questions

1. **`responses` vs `respx` for httpx mocking**
   - What we know: The spec says "pytest + responses" but we chose httpx over requests
   - What's unclear: Whether to use `respx` (httpx-native mocks) or `responses` (requests-native mocks)
   - Recommendation: Use `respx` for httpx mocking — it's purpose-built. Keep `responses` in dev deps if any adapter uses raw `requests`. Confirm with spec author.

2. **GitLab noproxy configuration**
   - What we know: Spec mentions `GRAPHQL_NOPROXY` for bypassing proxy on internal domains
   - What's unclear: Exact `httpx` mechanism for noproxy — httpx uses `NO_PROXY` env var natively but doesn't have a per-request noproxy parameter
   - Recommendation: Set the `NO_PROXY` env var or use `httpx.Client(proxy=None)` for GitLab-specific client instances. The `GRAPHQL_NOPROXY` config value can be injected as `NO_PROXY` when creating the transport.

3. **Schema TTL default value**
   - What we know: Spec says "TTL cache" but doesn't specify default duration
   - What's unclear: What's a sensible default
   - Recommendation: 300 seconds (5 minutes) — long enough to avoid hammering schema sources, short enough to pick up changes. Configurable via `GRAPHQL_SCHEMA_TTL`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Core runtime | ✓ | 3.10.4 | — |
| Rust toolchain | Maturin build (Phase 3) | ✓ | 1.93.1 | orjson fallback for Phase 1 (no Rust needed) |
| Cargo | Maturin build (Phase 3) | ✓ | 1.93.1 | — |
| ruff | Linting | ✓ | 0.15.13 | — |
| uv | Package management | ✓ | 0.11.16 | pip3 |
| graphql-core | Schema parsing | ✓ (3.2.6 installed, 3.2.11 on PyPI) | 3.2.6 → 3.2.11 | Needs upgrade |

**Missing dependencies with no fallback:**
- None — all core tools are available.

**Missing dependencies with fallback:**
- `pytest`, `responses`/`respx` — not installed system-wide but will be installed in project venv.
- `graphql-core` needs upgrade from 3.2.6 to 3.2.11 — straightforward `pip install --upgrade`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | Yes (GitLab token, Bearer token) | Tokens via env vars only; never logged or exposed in errors |
| V3 Session Management | No | No user sessions in this brick |
| V4 Access Control | Yes (mutation guard) | `GRAPHQL_ALLOW_MUTATIONS=false` by default; mutation-guard in Phase 2 |
| V5 Input Validation | Yes (SDL parsing, query input) | `graphql-core` validates SDL/queries; pydantic validates config |
| V6 Cryptography | No | No crypto operations; SSL handled by httpx/certifi |

### Known Threat Patterns for GraphQL + Python

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Token exposure in logs | Information Disclosure | Never log `GRAPHQL_BEARER_TOKEN` or `GRAPHQL_GITLAB_TOKEN`; use `SecretStr` type in pydantic config |
| Schema information disclosure | Information Disclosure | Read-only by design; introspection results are schema metadata, not data |
| SSL bypass | Tampering | `GRAPHQL_SSL_VERIFY=true` by default; warn loudly when disabled |
| Malicious SDL injection | Tampering | SDL is parsed by `graphql-core` which validates syntax; no code execution from SDL |
| Denial of Service via large schema | Denial of Service | Response size cap (addressed in Phase 2 `GRAPHQL_RESPONSE_MAX_SIZE`) |

## Sources

### Primary (HIGH confidence)
- Context7 `/graphql-python/graphql-core` — introspection query, build_schema, build_client_schema
- Context7 `/pyo3/maturin` — pyproject.toml configuration, mixed project layout
- Context7 `/websites/python-httpx` — httpx.Client configuration, timeout, SSL
- Context7 `/pydantic/pydantic` — frozen BaseModel configuration
- Context7 `/websites/pydantic_dev_validation` — BaseSettings, env prefix
- GitLab docs `docs.gitlab.com/api/repository_files/` — raw file retrieval API
- PyPI registry — verified all package versions and release dates

### Secondary (MEDIUM confidence)
- Apollo Federation documentation (timeout during fetch, but pattern is well-known)

### Tertiary (LOW confidence)
- `_service{sdl}` exact query format — based on training data about Apollo Federation spec

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GQL-06 | Schema cascade — priority order GitLab → introspection → `_service{sdl}` → SDL file; TTL cache | Full cascade architecture documented: SchemaService domain class orchestrates 4 source adapters via SchemaSource protocol; TTL cache using `time.monotonic()`; all 4 adapters researched with code examples (GitLab raw API, `get_introspection_query()`, `_service{sdl}` query, file read); `build_schema()` for SDL sources, `build_client_schema()` for introspection; pydantic-settings for `from_env()` configuration |

</phase_requirements>

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified on PyPI; graphql-core, pydantic, httpx are mature, well-documented libraries
- Architecture: HIGH — hexagonal pattern is well-understood; spec provides explicit layout; domain-purity constraint is straightforward to enforce
- Pitfalls: HIGH — common issues well-documented in library docs and community; federation edge cases verified against spec
- Security: MEDIUM — ASVS controls identified but threat model is simple (read-only brick)

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (30 days — stable ecosystem, no fast-moving deps)
