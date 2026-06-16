# Milestones

## v2.0 Production-Grade Platform (Shipped: 2026-06-16)

**Phases completed:** 5 phases (9-13), 10 plans, 17 requirements
**Tests:** 341 passing (from 229 at v1.1)

**Key accomplishments:**

- Full OpenTelemetry observability: distributed tracing, custom metrics, log correlation
- Security hardening: query depth limits, rate limiting, mTLS, OAuth2 token rotation, audit logging
- GraphQL subscriptions: WebSocket (graphql-transport-ws) + SSE fallback + async iterator
- DX ecosystem: PyPI publish pipeline, docker compose harness, SDK examples
- Copier template: parameterized MCP brick generation with optional features

---

## v1.1 Production Hardening (Shipped: 2026-06-08)

**Phases completed:** 4 phases (5-8), 10 plans
**Tests:** 229 passing

**Key accomplishments:**

- Tech debt resolved: codec wiring, error handling, resource lifecycle
- Async transport: AsyncGraphQLClient with full behavioral parity
- MCP-over-HTTP: FastAPI serve command with Dockerfile
- Federation entities: _entities pass-through in all faces

---

## v1.0 MVP (Shipped: 2026-06-05)

**Phases completed:** 4 phases (1-4), 9 plans
**Tests:** 128 passing

**Key accomplishments:**

- Foundation: hexagonal architecture, schema cascade, GraphQL client library
- Operations: query, raw, introspect, describe_type, list_subgraphs, refresh_schema
- Federation: subgraph mapping, 3-class error typing
- All faces: library, REST/FastAPI, MCP (stdio), CLI

---
