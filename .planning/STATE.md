---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: Testing & Quality
status: planning
last_updated: "2026-06-16T12:00:00.000Z"
last_activity: 2026-06-16
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
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

Phase: 14 — Coverage & Snapshot Infrastructure
Plan: —
Status: Not started (roadmap defined, awaiting plan-phase)
Last activity: 2026-06-16 — v2.1 roadmap created (3 phases, 19 requirements)

```
v2.1 ████░░░░░░░░░░░░░░░░ 0% (0/3 phases)
```

## Performance Metrics

| Metric | Value |
|--------|-------|
| v1.0 Phases | 4/4 complete |
| v1.0 Requirements | 10/10 complete |
| v1.0 Plans | 9/9 complete |
| v1.0 Tests | 128 passing |
| v1.1 Tests | 229 passing |
| v1.1 Phases | 4/4 complete |
| v1.1 Plans | 10/10 complete |
| v1.1 Requirements | 9/13 complete |
| v2.0 Tests | 341 passing (330 unit + 11 integration) |
| v2.0 Phases | 5/5 complete |
| v2.0 Plans | 10/10 complete |
| v2.0 Requirements | 17/17 complete |
| v2.1 Phases | 0/3 (Phase 14, 15, 16) |
| v2.1 Requirements | 0/19 (COV-01..03, CTR-01..03, MUT-01..03, PROP-01..03, SNAP-01..03, CI-01..04) |

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
| 2026-06-16 | UpstreamWSTransport with graphql-transport-ws | Full sub-protocol lifecycle; bounded asyncio.Queue for backpressure |
| 2026-06-16 | websockets as [subscriptions] optional extra | Zero deps when not needed; clear ImportError message |
| 2026-06-16 | SSE as StreamingResponse fallback | Works where WebSocket unavailable; X-Accel-Buffering: no for nginx |
| 2026-06-16 | OIDC Trusted Publishing over API tokens | No secrets to rotate; GitHub identity verified by PyPI |
| 2026-06-16 | stdlib HTTPServer + graphql-core for mock server | Zero external deps beyond graphql-core for integration test harness |
| 2026-06-16 | Session-scoped mock server subprocess | Auto-starts in local dev mode; GRAPHQL_ENDPOINT switches to docker compose mode |
| 2026-06-16 | Copier _subdirectory: project | Separates template config from template content |
| 2026-06-16 | hatchling default, maturin opt-in | Simpler build for non-Rust projects; maturin only when rust_native=true |
| 2026-06-16 | Domain files not Jinja2-templated | models.py, errors.py have no module_name refs; stay as plain Python |
| 2026-06-16 | Config class name derived from env_prefix | KafkaConfig, OrderingConfig — derived via Jinja2 title() filter |

### Key Constraints

- `domain/` must never import fastapi, requests, httpx, or any I/O library — enforced by ruff + test
- Mutation-guard is always on unless `GRAPHQL_ALLOW_MUTATIONS=true`; applies to both `query` and `raw`
- Schema cascade priority: GitLab (pinned SDL) > introspection (live) > `_service{sdl}` (federation) > SDL file (offline)
- CI wheel matrix: Linux manylinux+musllinux x86_64+aarch64, macOS arm64+x86_64, Windows AMD64, py3.10–3.12 + sdist

### Blockers

None currently.

---

## Session Continuity

**Last session**: 2026-06-16 — v2.1 roadmap created (3 phases: 14-16, 19 requirements mapped)
**Next action**: `/gsd-plan-phase 14` — plan Coverage & Snapshot Infrastructure
**Context**: v2.1 milestone started. Phase 14: COV-01..03 + SNAP-01..03 (coverage enforcement + snapshot regression). Phase 15: CTR-01..03 + PROP-01..03 (contract + property-based testing). Phase 16: MUT-01..03 + CI-01..04 (mutation testing + CI quality gates). All 19 requirements mapped.
