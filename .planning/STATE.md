---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Production Hardening
status: executing
last_updated: "2026-06-08T13:17:26Z"
last_activity: 2026-06-08 -- Completed Phase 06 Plan 02 (async GraphQL client)
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 6
  completed_plans: 6
  percent: 75
---

# graphql-mcp — Project State

## Project Reference

**Core value**: Generic read-only GraphQL MCP brick — schema discovery, query execution, 3-class error typing, and federation ownership mapping (field → subgraph → serviceName). Library-first: `from graphql_mcp import GraphQLClient` works in pytest without network/MCP/FastAPI. Serves as the v2 hexagonal reference template copied by kafka-mcp and ordering-mcp.

**Investigator contract**: `GraphQLClient` exposes `query`, `raw`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`. The `error_class` field lets investigator distinguish "service down" (transport) from "asked wrong thing" (graphql). `subgraph` on `TypeInfo` is the correlation key to `service_name` in Jaeger/OpenSearch.

**Repository**: `/opt/develop/aiqa/mcps/graphql-mcp/`
**Spec**: `/opt/develop/aiqa/docs/superpowers/specs/2026-06-05-investigation-mcp-suite-design.md` §3
**Roadmap**: `.planning/ROADMAP.md`
**Requirements**: `.planning/REQUIREMENTS.md`

---

## Current Position

Phase: 06 (Async Transport & Perf Benchmarks) — COMPLETE
Plan: 3 of 3 (all complete)
Status: Phase 06 Complete
Last activity: 2026-06-08 -- Completed Phase 06 Plan 02 (async GraphQL client)

## Performance Metrics

| Metric | Value |
|--------|-------|
| v1.0 Phases | 4/4 complete |
| v1.0 Requirements | 10/10 complete |
| v1.0 Plans | 9/9 complete |
| v1.0 Tests | 128 passing |
| v1.1 Tests | 204 passing |
| v1.1 Phases | 2/4 complete |
| v1.1 Plans | 6/6 complete (Phase 05 done, Phase 06 done) |
| v1.1 Requirements | 5/13 complete |

---

## Accumulated Context

### Architecture Decisions (inherited from umbrella + v1.0)

- D1: Hybrid — deterministic collectors + optional LLM correlator (approach C)
- D2: Library-first; MCP/REST/CLI are thin inbound adapters
- D5: Python core + Rust hot paths (pyo3/maturin); pure-Python orjson fallback
- D7: Hexagonal architecture — domain has zero I/O or framework imports
- D8: FastAPI primary face (k8s/team sharing); stdio second (Glama + local agent)
- D9: Rust JsonCodec via pyo3; orjson fallback; parity under test; maturin CI

### v1.1 Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-08 | Separate AsyncGraphQLClient (not dual methods) | Clean API boundary, no sync/async confusion. FastAPI uses async, CLI/lib use sync. |
| 2026-06-08 | _entities as pass-through | Send to gateway, return typed result. Full resolution is a separate product (Apollo Router). |
| 2026-06-08 | v1.1 not v2.0 | _entities is additive (new operation), not breaking. Tech debt + infra hardening is minor version scope. |
| 2026-06-08 | Codec-agnostic ValueError/TypeError catch in transport | orjson.JSONDecodeError is ValueError subclass; codec-neutral error handling |
| 2026-06-08 | FastAPI exception_handler (global) for SchemaResolutionError | Single handler catches all endpoints; cleaner than per-endpoint try/except |
| 2026-06-08 | Idempotent close via _closed flag | Both atexit and context manager call close(); _closed prevents double transport.close() |
| 2026-06-08 | atexit in from_env() only, not __init__ | Manual construction shouldn't auto-register cleanup; caller controls lifecycle |
| 2026-06-08 | AsyncHttpTransport mirrors sync exactly | Same constructor, error handling, codec injection — behavioral parity over DRY abstraction |
| 2026-06-08 | asyncio_mode=auto for pytest | Global config in pyproject.toml — async test functions auto-detected without per-test markers |
| 2026-06-08 | Benchmarks disabled by default (--benchmark-disable) | Users enable explicitly with --benchmark-enable; prevents slowing normal test runs |
| 2026-06-08 | Transport round-trip benchmarks deferred | Codec is CPU-bound/reproducible; transport measures httpx+network, not our code |
| 2026-06-08 | AsyncGraphQLClient mirrors sync exactly | Same constructor, operations, error handling — behavioral parity over DRY abstraction |
| 2026-06-08 | query/raw async, schema ops sync | Schema resolution is in-process (no I/O); only transport-bound ops need await |
| 2026-06-08 | atexit sync cleanup for async client | atexit cannot await; use httpx.AsyncClient sync close path for cleanup |
| 2026-06-08 | from_env() skips introspection/federation sources | Async client cannot use sync HttpTransport-based schema sources |

### Key Constraints

- `domain/` must never import fastapi, requests, httpx, or any I/O library — enforced by ruff + test
- Mutation-guard is always on unless `GRAPHQL_ALLOW_MUTATIONS=true`; applies to both `query` and `raw`
- Schema cascade priority: GitLab (pinned SDL) > introspection (live) > `_service{sdl}` (federation) > SDL file (offline)
- CI wheel matrix: Linux manylinux+musllinux x86_64+aarch64, macOS arm64+x86_64, Windows AMD64, py3.10–3.12 + sdist

### v1.0 Tech Debt (to be resolved in v1.1)

1. ~~Codec dead code — RustJsonCodec/OrjsonCodec never wired into HttpTransport production path~~ ✅ Resolved in 05-01
2. ~~SchemaResolutionError unhandled in all inbound adapters → 500/traceback~~ ✅ Resolved in 05-02
3. ~~HttpTransport.close() never called — no resource cleanup~~ ✅ Resolved in 05-03
4. MCP-over-HTTP deferred — only stdio transport

### Blockers

None currently.

---

## Session Continuity

**Last session**: 2026-06-08 — Completed Phase 06 Plan 02 (async GraphQL client)
**Next action**: Execute Phase 07 (next milestone phase)
**Context**: Phase 06 fully complete — async transport (01), async client (02), codec benchmarks (03). AsyncGraphQLClient with 6 operations, 204 tests passing. Both sync and async clients importable from package.

## Operator Next Steps

- Execute Phase 07 (next v1.1 phase)
