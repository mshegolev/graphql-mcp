---
phase: 01-foundation-schema-sources
plan: 02
subsystem: schema-cascade
tags: [schema-service, outbound-adapters, http-transport, cascade, ttl-cache, hexagonal]
dependency_graph:
  requires: [domain-models, port-protocols]
  provides: [schema-service, http-transport, gitlab-source, introspection-source, federation-sdl-source, file-sdl-source]
  affects: [01-03]
tech_stack:
  added: []
  patterns: [priority-chain-cascade, ttl-cache-monotonic, protocol-adapters, 3-class-error-typing]
key_files:
  created:
    - src/graphql_mcp/domain/schema_service.py
    - src/graphql_mcp/adapters/outbound/http_transport.py
    - src/graphql_mcp/adapters/outbound/gitlab_source.py
    - src/graphql_mcp/adapters/outbound/introspection_source.py
    - src/graphql_mcp/adapters/outbound/service_sdl_source.py
    - src/graphql_mcp/adapters/outbound/file_source.py
  modified: []
decisions:
  - "SchemaService uses time.monotonic() for TTL cache — stdlib, no I/O imports needed in domain"
  - "HttpTransport uses orjson.dumps() for request body serialization for consistency with future native codec"
  - "GitLabSource uses /raw endpoint (not base64-encoded standard endpoint) per RESEARCH.md Pitfall 3"
  - "IntrospectionSource uses build_client_schema + print_schema (not build_schema) per RESEARCH.md Pitfall 2"
metrics:
  duration: "317s (~5min)"
  completed: "2026-06-05T20:08:37Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 6
  files_modified: 0
---

# Phase 01 Plan 02: SchemaService Cascade + Outbound Adapters Summary

Priority-chain schema cascade service with TTL cache (time.monotonic, 300s default) orchestrating four outbound adapters — GitLabSource (REST /raw), IntrospectionSource (build_client_schema), ServiceSdlSource (federation _service{sdl}), FileSdlSource (local SDL) — all implementing SchemaSource protocol with None-on-failure semantics, plus HttpTransport with 3-class error typing (OK/GRAPHQL/TRANSPORT).

## What Was Done

### Task 1: Create SchemaService domain class with cascade and TTL cache
- Created `src/graphql_mcp/domain/schema_service.py` — the cascade orchestrator
- Accepts `Sequence[SchemaSource]` in constructor, tries each in priority order
- TTL cache using `time.monotonic()` with configurable `ttl_seconds` (default 300.0)
- `resolve()` returns cached schema within TTL, otherwise cascades through sources
- `invalidate()` clears cache forcing next `resolve()` to re-fetch
- Raises `SchemaResolutionError` when all sources fail
- Zero I/O imports verified — only `logging`, `time`, `typing`, and internal domain/ports
- **Commit:** `449541e`

### Task 2: Create HttpTransport and four schema source outbound adapters
- Created `HttpTransport` — httpx-based with connection pooling via `httpx.Client`
  - 3-class error classification: `TRANSPORT` for HTTP errors, `GRAPHQL` for response errors, `OK` for clean
  - Configurable timeout (30s default, connect capped at 10s), SSL verification, bearer token auth
  - Uses `orjson.dumps()` for request body serialization
- Created `GitLabSource` — fetches SDL via GitLab REST API `/repository/files/{path}/raw` endpoint
  - Uses `PRIVATE-TOKEN` header (never logged), validates SDL with `build_schema()`
- Created `IntrospectionSource` — live introspection query via transport
  - Uses `build_client_schema(result.data)` + `print_schema()` to convert introspection JSON to SDL
- Created `ServiceSdlSource` — federation `_service{sdl}` query via transport
  - Validates returned SDL with `build_schema()`
- Created `FileSdlSource` — reads local `.graphql` file via `pathlib.Path`
  - Validates non-empty content with `build_schema()`
- All four schema sources implement `SchemaSource` protocol, return `None` on failure (no exceptions)
- **Commit:** `c485720`

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

- `SchemaService` importable, zero I/O imports verified — PASS
- All five adapter files importable — PASS
- `GitLabSource` satisfies `SchemaSource` protocol (`isinstance` check) — PASS
- `FileSdlSource` satisfies `SchemaSource` protocol — PASS
- `IntrospectionSource` satisfies `SchemaSource` protocol — PASS
- `ServiceSdlSource` satisfies `SchemaSource` protocol — PASS
- `HttpTransport` satisfies `GraphQLTransport` protocol — PASS
- `FEDERATION_SDL_QUERY` contains `_service` and `sdl` — PASS

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `time.monotonic()` for TTL cache in domain layer | stdlib, avoids I/O imports; monotonic clock immune to system time changes |
| `orjson.dumps()` for request body in HttpTransport | Consistent with future Rust native codec path; faster than `json.dumps` |
| GitLab `/raw` endpoint (not base64) | Returns raw SDL text directly; avoids decoding step per RESEARCH.md Pitfall 3 |
| `build_client_schema` for introspection (not `build_schema`) | Introspection JSON is a client-side representation; `build_schema` expects SDL text; per RESEARCH.md Pitfall 2 |

## Self-Check: PASSED

- [x] `src/graphql_mcp/domain/schema_service.py` exists — FOUND
- [x] `src/graphql_mcp/adapters/outbound/http_transport.py` exists — FOUND
- [x] `src/graphql_mcp/adapters/outbound/gitlab_source.py` exists — FOUND
- [x] `src/graphql_mcp/adapters/outbound/introspection_source.py` exists — FOUND
- [x] `src/graphql_mcp/adapters/outbound/service_sdl_source.py` exists — FOUND
- [x] `src/graphql_mcp/adapters/outbound/file_source.py` exists — FOUND
- [x] Commit `449541e` exists — FOUND
- [x] Commit `c485720` exists — FOUND
