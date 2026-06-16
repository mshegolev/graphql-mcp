---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Production-Grade Platform
status: executing
last_updated: 2026-06-16
last_activity: 2026-06-16 -- Phase 10 complete (291 tests, SEC-01 through SEC-06 satisfied)
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 5
  completed_plans: 5
  percent: 40
stopped_at: null
---

# graphql-mcp — Project State

## Project Reference

**Core value**: Generic read-only GraphQL MCP brick — schema discovery, query execution, 3-class error typing, and federation ownership mapping (field → subgraph → serviceName). Library-first: `from graphql_mcp import GraphQLClient` works in pytest without network/MCP/FastAPI. Serves as the v2 hexagonal reference template copied by kafka-mcp and ordering-mcp.

**Investigator contract**: `GraphQLClient` exposes `query`, `raw`, `entities`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`. The `error_class` field lets investigator distinguish "service down" (transport) from "asked wrong thing" (graphql). `subgraph` on `TypeInfo` is the correlation key to `service_name` in Jaeger/OpenSearch.

**Repository**: `/opt/develop/aiqa/mcps/graphql-mcp/`
**Spec**: `/opt/develop/aiqa/docs/superpowers/specs/2026-06-05-investigation-mcp-suite-design.md` §3
**Roadmap**: `.planning/ROADMAP.md`
**Requirements**: `.planning/REQUIREMENTS.md`

---

## Current Position

Phase: 11 — GraphQL Subscriptions (next)
Plan: —
Status: Phase 10 complete, proceeding to Phase 11
Last activity: 2026-06-16 — Phase 10 complete (291 tests, all security requirements satisfied)

## Performance Metrics

| Metric | Value |
|--------|-------|
| v1.0 Phases | 4/4 complete |
| v1.0 Requirements | 10/10 complete |
| v1.0 Plans | 9/9 complete |
| v1.0 Tests | 128 passing |
| v1.1 Tests | 229 passing |
| v1.1 Phases | 4/4 complete |
| v1.1 Plans | 10/10 complete (Phase 05 done, Phase 06 done, Phase 07 done, Phase 08 done) |
| v1.1 Requirements | 9/13 complete |
| v2.0 Tests | 291 passing |
| v2.0 Phases | 2/5 complete |
| v2.0 Plans | 5/5 complete (Phase 09 done, Phase 10 done) |
| v2.0 Requirements | 11/17 complete (OTEL-01–05, SEC-01–06) |

---

## Accumulated Context

### Architecture Decisions (inherited from umbrella + v1.0)

- D1: Hybrid — deterministic collectors + optional LLM correlator (approach C)
- D2: Library-first; MCP/REST/CLI are thin inbound adapters
- D5: Python core + Rust hot paths (pyo3/maturin); pure-Python orjson fallback
- D7: Hexagonal architecture — domain has zero I/O or framework imports
- D8: FastAPI primary face (k8s/team sharing); stdio second (Glama + local agent)
- D9: Rust JsonCodec via pyo3; orjson fallback; parity under test; maturin CI

### v2.0 Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-16 | OTEL as opt-in [otel] extra | OTEL packages are heavy; graceful no-op via import guards when absent |
| 2026-06-16 | HTTPXClientInstrumentor global patch | Auto-instruments all httpx clients; no transport constructor changes needed |
| 2026-06-16 | Custom metrics in lib facade (not transport) | Facade is where error_class is known and all faces converge |
| 2026-06-16 | LoggingInstrumentor with set_logging_format=True | Injects otelTraceID/otelSpanID into every log record during traced requests |
| 2026-06-16 | init_otel() in serve command only | Library users call init_otel() themselves; serve command auto-initializes |
| 2026-06-16 | In-memory sliding window rate limiter (no Redis) | Zero external dependencies; suitable for single-process deployments |
| 2026-06-16 | Query depth via graphql-core AST visitor | Reuses existing dependency; checks before upstream call |
| 2026-06-16 | Header forwarding explicit whitelist | Authorization, X-User-Id, X-Roles only; prevents header injection |
| 2026-06-16 | mTLS via stdlib ssl.SSLContext | Zero new deps; httpx verify= param accepts SSLContext |
| 2026-06-16 | OAuth2TokenManager with thread-safe cache | Token refreshed before expiry; Bearer injected per-request |
| 2026-06-16 | Audit logging gated by GRAPHQL_AUDIT_LOG=true | Zero overhead when disabled; SHA-256 query hash (raw queries never logged) |

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
| 2026-06-08 | streamable_http_path=/ for MCP sub-app | Avoids /mcp/mcp double-path when mounted at /mcp on FastAPI |
| 2026-06-08 | MCP sub-app tested directly (not via FastAPI mount) | FastAPI doesn't invoke sub-app lifespans; Starlette TestClient does |
| 2026-06-08 | DNS rebinding protection disabled in test fixtures only | Production security preserved; testserver host fails DNS check |
| 2026-06-08 | Two-stage pip install in Dockerfile (wheel then extras) | pip doesn't support *.whl[extras] syntax for local file paths |
| 2026-06-08 | stdlib urllib HEALTHCHECK (no curl) | python:3.12-slim doesn't include curl; urllib always available |
| 2026-06-08 | _ENTITIES_QUERY uses __typename-only selection set | Gateway resolves entity fields; client just passes representations through |
| 2026-06-08 | entities() bypasses mutation guard | _entities is a query operation, not a mutation — guard not applicable |
| 2026-06-08 | pyproject.toml version left dynamic | maturin/Cargo.toml controls version; no static bump needed in pyproject.toml |

### Key Constraints

- `domain/` must never import fastapi, requests, httpx, or any I/O library — enforced by ruff + test
- Mutation-guard is always on unless `GRAPHQL_ALLOW_MUTATIONS=true`; applies to both `query` and `raw`
- Schema cascade priority: GitLab (pinned SDL) > introspection (live) > `_service{sdl}` (federation) > SDL file (offline)
- CI wheel matrix: Linux manylinux+musllinux x86_64+aarch64, macOS arm64+x86_64, Windows AMD64, py3.10–3.12 + sdist

### v1.0 Tech Debt (to be resolved in v1.1)

1. ~~Codec dead code — RustJsonCodec/OrjsonCodec never wired into HttpTransport production path~~ ✅ Resolved in 05-01
2. ~~SchemaResolutionError unhandled in all inbound adapters → 500/traceback~~ ✅ Resolved in 05-02
3. ~~HttpTransport.close() never called — no resource cleanup~~ ✅ Resolved in 05-03
4. ~~MCP-over-HTTP deferred — only stdio transport~~ ✅ Resolved in 07-01

### Blockers

None currently.

---

## Session Continuity

**Last session**: 2026-06-16 — Phase 10 complete (291 tests, SEC-01 through SEC-06 satisfied)
**Next action**: Phase 11 — GraphQL Subscriptions (discuss → plan → execute)
**Context**: v2.0 Phases 9-10 complete. Phase 9: OTEL (tracing, metrics, log correlation). Phase 10: Security (depth limits, rate limiting, header forwarding, mTLS, OAuth2, audit logging). 291 tests passing. Next: Phase 11 GraphQL Subscriptions (SUB-01 through SUB-03).
