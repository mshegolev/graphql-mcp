# graphql-mcp

![CI](https://github.com/mshegolev/graphql-mcp/actions/workflows/ci.yml/badge.svg)
[![Coverage](https://img.shields.io/badge/Coverage-80%25-yellow.svg)](https://github.com/mshegolev/graphql-mcp)
[![Testing Quality](https://img.shields.io/badge/Testing-Quality%20Assured-green.svg)](https://github.com/mshegolev/graphql-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Generic read-only GraphQL MCP brick — schema discovery, query execution, 3-class error typing, federation ownership mapping, and entity resolution.

## Features

- **8 operations**: `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`, `entities`, `subscribe`
- **3-class error typing**: `ok` (success), `graphql` (response contains errors), `transport` (HTTP / network failure)
- **Mutation guard**: blocks mutations by default; opt-in via `GRAPHQL_ALLOW_MUTATIONS=true`
- **Schema cascade**: GitLab (pinned SDL) → introspection (live) → `_service{sdl}` (federation) → local SDL file
- **Federation ownership**: maps types and fields to subgraphs via supergraph SDL parsing
- **Rust-native JSON codec**: pyo3 extension for high-throughput JSON processing, with automatic orjson fallback
- **Async support**: `AsyncGraphQLClient` with full behavioral parity for FastAPI and async workflows
- **Library-first**: `from graphql_mcp import GraphQLClient` works in pytest without network, MCP, or FastAPI
- **Real-time subscriptions**: Server-Sent Events (SSE) and WebSocket support for real-time GraphQL subscriptions

## Installation

```bash
# Core (includes Rust native extension when available)
pip install graphql-mcp

# With FastAPI REST adapter
pip install graphql-mcp[server]

# With MCP stdio support
pip install graphql-mcp[mcp]

# With Click CLI
pip install graphql-mcp[cli]

# With WebSocket subscription support
pip install graphql-mcp[subscriptions]

# Everything
pip install graphql-mcp[all]
```

## Quick Start

```python
from graphql_mcp import GraphQLClient

# Create client from GRAPHQL_* environment variables
client = GraphQLClient.from_env()

# Execute a query
result = client.query("{ users { id name } }")
print(result.data)          # {"users": [{"id": "1", "name": "Alice"}]}
print(result.error_class)   # ErrorClass.OK

# Introspect the schema
summary = client.introspect()
print(summary.query_fields)  # ["users", "orders", ...]

# Describe a specific type
info = client.describe_type("User")
print(info.fields)       # [{"name": "id", ...}, {"name": "name", ...}]
print(info.subgraph)     # "users-service" (if supergraph SDL available)

# List federation subgraphs
subgraphs = client.list_subgraphs()
for sg in subgraphs:
    print(f"{sg.name}: {sg.url} owns {sg.owned_types}")

# Force schema re-fetch
client.refresh_schema()

# Resolve federation entities
result = client.entities([
    {"__typename": "Product", "id": "123"},
    {"__typename": "User", "id": "456"},
])
print(result.data)  # {"_entities": [{"__typename": "Product", ...}, ...]}

# Subscribe to real-time events (requires websockets extra)
for result in client.subscribe("subscription { events { id type payload } }"):
    if result.data:
        print(f"Event: {result.data}")
    if result.errors:
        print(f"Errors: {result.errors}")
    break  # Just show one event for example
```

### Async Usage

```python
from graphql_mcp import AsyncGraphQLClient

async with AsyncGraphQLClient.from_env() as client:
    result = await client.query("{ users { id } }")
    entities = await client.entities([{"__typename": "User", "id": "1"}])
    
    # Subscribe to real-time events
    async for result in client.subscribe("subscription { events { id type payload } }"):
        if result.data:
            print(f"Event: {result.data}")
        if result.errors:
            print(f"Errors: {result.errors}")
        break  # Just show one event for example
```

## Configuration

All settings are read from environment variables with the `GRAPHQL_` prefix.

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAPHQL_ENDPOINT` | `""` | GraphQL endpoint URL |
| `GRAPHQL_BEARER_TOKEN` | `""` | Bearer token for Authorization header |
| `GRAPHQL_TIMEOUT` | `30` | Request timeout in seconds |
| `GRAPHQL_SSL_VERIFY` | `true` | Verify SSL certificates |
| `GRAPHQL_NOPROXY` | `""` | Comma-separated list of hosts to bypass proxy |
| `GRAPHQL_SCHEMA_SOURCE` | `auto` | Schema source strategy: `auto`, `gitlab`, `introspection`, `federation`, `sdl_file` |
| `GRAPHQL_SCHEMA_SDL` | `""` | Path to local SDL file (used when source is `sdl_file` or `auto` fallback) |
| `GRAPHQL_SCHEMA_TTL` | `300` | Schema cache TTL in seconds |
| `GRAPHQL_SCHEMA_GITLAB_URL` | `""` | GitLab instance URL for schema source |
| `GRAPHQL_SCHEMA_GITLAB_PROJECT_ID` | `""` | GitLab project ID containing the schema file |
| `GRAPHQL_SCHEMA_GITLAB_FILE_PATH` | `""` | Path to schema file in GitLab repo |
| `GRAPHQL_SCHEMA_GITLAB_REF` | `HEAD` | Git ref to fetch schema from |
| `GRAPHQL_GITLAB_TOKEN` | `""` | GitLab personal access token |
| `GRAPHQL_ALLOW_MUTATIONS` | `false` | Allow mutation queries (guard disabled when `true`) |
| `GRAPHQL_SUPERGRAPH_SOURCE` | `auto` | Supergraph parsing: `auto` (detect from SDL) or `off` |
| `GRAPHQL_SUBSCRIPTION_ENDPOINT` | `""` | WebSocket endpoint for upstream subscription connections |
| `GRAPHQL_SUBSCRIPTION_QUEUE_SIZE` | `128` | Bounded async queue size for subscription backpressure |
| `GRAPHQL_SUBSCRIPTION_RATE_LIMIT` | `"10/minute"` | Rate limit for subscription connections per IP (`"{count}/{window}"`) |
| `GRAPHQL_MAX_CONCURRENT_SUBSCRIPTIONS` | `100` | Maximum concurrent subscription connections per IP |

## API Documentation

Detailed API documentation is available in the [OpenAPI specification](./openapi/openapi.yaml) which describes all REST endpoints exposed by the service.

### Adapters

### Library (Python)

Direct in-process usage — ideal for tests and scripts:

```python
from graphql_mcp import GraphQLClient
client = GraphQLClient.from_env()
result = client.query("{ __typename }")
```

### FastAPI REST

HTTP API for team sharing and Kubernetes deployments:

```bash
pip install graphql-mcp[server]
uvicorn graphql_mcp.adapters.inbound.rest:app --host 0.0.0.0 --port 8000
```

Endpoints:
- `GET /health` — health check
- `POST /graphql/query` — execute query (`{"query": "...", "variables": {...}}`)
- `GET /graphql/introspect` — schema summary
- `GET /graphql/type/{name}` — describe type
- `GET /graphql/subgraphs` — list federation subgraphs
- `POST /graphql/refresh` — clear schema cache
- `POST /graphql/entities` — resolve federation entities
- `GET /graphql/subscribe` — subscribe to GraphQL events via Server-Sent Events (query params: `query`, `variables`)
- `GET /ready` — readiness probe (200 when schema resolvable, 503 otherwise)

WebSocket endpoints:
- `GET /graphql/subscribe` — subscribe to GraphQL events via WebSocket (graphql-transport-ws protocol)

### MCP stdio

For Glama, Claude Desktop, and other MCP-compatible AI agents:

```bash
pip install graphql-mcp[mcp]
python -m graphql_mcp.adapters.inbound.mcp_stdio
```

Exposes 8 MCP tools: `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`, `entities`, `subscribe`.

### CLI

Ad-hoc terminal queries:

```bash
pip install graphql-mcp[cli]

graphql-mcp query '{ __typename }'
graphql-mcp introspect
graphql-mcp describe-type User
graphql-mcp list-subgraphs
graphql-mcp refresh
graphql-mcp entities '[{"__typename": "Product", "id": "123"}]'
graphql-mcp subscribe 'subscription { events { id type payload } }'
```

### Serve (REST + MCP-over-HTTP)

Start FastAPI with REST endpoints and MCP-over-HTTP transport:

```bash
pip install graphql-mcp[all]

# Start the server
graphql-mcp serve --host 0.0.0.0 --port 8000
```

### Docker

```bash
docker build -t graphql-mcp .
docker run -e GRAPHQL_ENDPOINT=https://api.example.com/graphql \
  -p 8000:8000 graphql-mcp
```

## Architecture

graphql-mcp follows **hexagonal architecture** (ports & adapters):

```
┌─────────────────────────────────────────────────┐
│                Inbound Adapters                 │
│   Library │ FastAPI REST │ MCP stdio │ CLI       │
├─────────────────────────────────────────────────┤
│                    Ports                        │
│         Transport │ SchemaSource                │
├─────────────────────────────────────────────────┤
│                   Domain                        │
│   Models │ SchemaService │ Errors                │
│   (zero I/O imports — pure business logic)      │
├─────────────────────────────────────────────────┤
│              Outbound Adapters                  │
│  HTTP Transport │ GitLab │ Introspection │ SDL  │
│  QueryGuard │ SchemaAnalyzer │ JsonCodec        │
└─────────────────────────────────────────────────┘
```

- **Domain** has zero I/O or framework imports — enforced by ruff and tests
- **Ports** define Protocol interfaces for transport and schema sources
- **Inbound adapters** are thin facades that delegate to `GraphQLClient`
- **Outbound adapters** handle HTTP, schema resolution, JSON codec, and mutation detection

## Testing

This project uses comprehensive testing strategies to ensure code quality and prevent regressions:

### Coverage Testing
- **Branch coverage**: Minimum 80% coverage required (enforced in CI)
- **Per-module reporting**: Coverage is measured separately for domain, adapters, and ports
- **HTML/XML reports**: Generated locally and in CI for detailed analysis

To run tests with coverage locally:
```bash
pytest --cov=src --cov-report=html
```

### Contract Testing
- **Schema snapshots**: GraphQL schema structure is validated against stored snapshots
- **Response validation**: API response shapes are validated to prevent breaking changes
- **Pact integration**: Consumer-driven contract testing framework implemented

### Property-Based Testing
- **Hypothesis framework**: Comprehensive input validation through property-based testing
- **Invariant testing**: Domain model contracts verified under random inputs
- **Edge case coverage**: Malformed inputs and boundary conditions tested

### Mutation Testing
- **Mutmut integration**: Test suite effectiveness measured through mutation testing
- **Domain-focused**: Mutation analysis scoped to critical domain modules
- **Threshold enforcement**: CI blocks merges when mutation scores drop below threshold

### Continuous Integration
All tests are run in CI on every pull request, with coverage reports uploaded to Codecov for visualization and tracking. Multi-version testing ensures compatibility across Python 3.10, 3.11, and 3.12.

## License

MIT
