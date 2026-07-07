# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.2.0] - 2026-07-07

### Changed
- MCP stdio tools return domain Pydantic models directly, so FastMCP derives an `outputSchema` and emits `structuredContent`
- MCP stdio tools annotated with `readOnlyHint`/`openWorldHint` (and `idempotentHint` for `refresh_schema`)
- Blocked mutations and unavailable schemas now surface as MCP tool errors (`ToolError` / `isError`) with actionable hints, instead of success results carrying an `error` field
- Synced package version to the crate manifest (`native/Cargo.toml`) so the built wheel version matches the release tag

## [1.1.0] - 2026-06-08

### Added
- `entities()` operation — federation `_entities(representations:)` pass-through on `GraphQLClient` and `AsyncGraphQLClient`
- `POST /graphql/entities` REST endpoint
- `entities` MCP tool
- `graphql-mcp entities` CLI command
- `AsyncGraphQLClient` — async counterpart to `GraphQLClient` with full behavioral parity
- `AsyncHttpTransport` — async httpx-based transport
- `graphql-mcp serve` CLI command — starts FastAPI with REST + MCP-over-HTTP
- MCP-over-HTTP transport on FastAPI app (streamable HTTP alongside REST)
- `/ready` endpoint — readiness probe (200 when schema resolvable, 503 otherwise)
- Dockerfile with multi-stage build, health probes, non-root user
- Codec performance benchmarks (pytest-benchmark) with EVALUATION.md

### Fixed
- Wired `JsonCodec` into `HttpTransport` via `get_codec()` — Rust native codec now used in production
- `SchemaResolutionError` handled in all inbound adapters — no unhandled tracebacks
- Resource lifecycle — `GraphQLClient` context manager, `close()`, `atexit` cleanup

## [1.0.0] - 2026-06-05

### Added
- `GraphQLClient` — library-first facade with 6 operations: `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`
- 3-class error typing: `ok`, `graphql`, `transport`
- Mutation guard — blocks mutations by default, opt-in via `GRAPHQL_ALLOW_MUTATIONS=true`
- Schema cascade: GitLab → introspection → `_service{sdl}` → local SDL file
- Federation ownership mapping: types/fields → subgraphs via supergraph SDL parsing
- Rust native JSON codec (pyo3) with automatic orjson fallback
- FastAPI REST adapter with 6 endpoints
- MCP stdio adapter with 6 tools
- Click CLI adapter with 6 commands
- `server.json` and `glama.json` MCP manifests
