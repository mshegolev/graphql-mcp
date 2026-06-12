# graphql-mcp

![CI](https://github.com/mshegolev/graphql-mcp/actions/workflows/ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Generic read-only GraphQL MCP brick — schema discovery, query execution, 3-class error typing, federation ownership mapping, and entity resolution.

## Features

- **7 operations**: `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`, `entities`
- **3-class error typing**: `ok` (success), `graphql` (response contains errors), `transport` (HTTP / network failure)
- **Mutation guard**: blocks mutations by default; opt-in via `GRAPHQL_ALLOW_MUTATIONS=true`
- **Schema cascade**: GitLab (pinned SDL) → introspection (live) → `_service{sdl}` (federation) → local SDL file
- **Federation ownership**: maps types and fields to subgraphs via supergraph SDL parsing
- **Rust-native JSON codec**: pyo3 extension for high-throughput JSON processing, with automatic orjson fallback
- **Async support**: `AsyncGraphQLClient` with full behavioral parity for FastAPI and async workflows
- **Library-first**: `from graphql_mcp import GraphQLClient` works in pytest without network, MCP, or FastAPI

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
```

### Async Usage

```python
from graphql_mcp import AsyncGraphQLClient

async with AsyncGraphQLClient.from_env() as client:
    result = await client.query("{ users { id } }")
    entities = await client.entities([{"__typename": "User", "id": "1"}])
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

## Adapters

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
- `GET /ready` — readiness probe (200 when schema resolvable, 503 otherwise)

### MCP stdio

For Glama, Claude Desktop, and other MCP-compatible AI agents:

```bash
pip install graphql-mcp[mcp]
python -m graphql_mcp.adapters.inbound.mcp_stdio
```

Exposes 7 MCP tools: `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`, `entities`.

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

## License

MIT
