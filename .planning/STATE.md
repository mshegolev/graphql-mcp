---
gsd_state_version: 1.0
milestone: v2.3
milestone_name: Release & Staging Enablement
status: in-progress
last_updated: "2026-07-08T00:00:00.000Z"
last_activity: 2026-07-08
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# generic-graphql-mcp — Project State

## Project Reference

**Core value**: Generic read-only GraphQL MCP brick — schema discovery, query execution, 3-class error typing, and federation ownership mapping (field → subgraph → serviceName). Library-first: `from generic_graphql_mcp import GraphQLClient` works in pytest without network/MCP/FastAPI. Serves as the v2 hexagonal reference template copied by kafka-mcp and ordering-mcp.

**Investigator contract**: `GraphQLClient` exposes `query`, `raw`, `entities`, `introspect`, `describe_type`, `list_subgraphs`, `refresh_schema`. The `error_class` field lets investigator distinguish "service down" (transport) from "asked wrong thing" (graphql). `subgraph` on `TypeInfo` is the correlation key to `service_name` in Jaeger/OpenSearch.

**Repository**: `/opt/develop/aiqa/mcps/graphql-mcp/`
**Spec**: `/opt/develop/aiqa/docs/superpowers/specs/2026-06-05-investigation-mcp-suite-design.md` §3
**Roadmap**: `.planning/ROADMAP.md`
**Requirements**: `.planning/REQUIREMENTS.md`

---

## Current Position

**Milestone**: v2.3 Release & Staging Enablement
**Phase**: 20 — CI Hardening (not started)
**Plan**: —
**Status**: Roadmap created; ready to plan Phase 20
**Last activity**: 2026-07-08 — Roadmap created for v2.3 (Phases 20-22)

Progress bar: `[ ] Phase 20` `[ ] Phase 21` `[ ] Phase 22` — 0/3 complete

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
| v2.1 Phases | 3/3 (Phase 14 complete, Phase 15 complete, Phase 16 complete) |
| v2.1 Requirements | 19/19 (All requirements satisfied) |
| v2.2 Phases | 3/3 (Phase 17 complete, Phase 18 complete, Phase 19 complete) |
| v2.2 Requirements | 18/18 (All requirements satisfied) |
| v2.3 Phases | 0/3 (Phase 20 pending, Phase 21 pending, Phase 22 pending) |
| v2.3 Requirements | 0/10 (10 requirements mapped to roadmap) |

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

### v2.3 Decisions

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-07-08 | Renamed dist graphql-mcp → generic-graphql-mcp | PyPI name graphql-mcp taken; blocked Trusted Publishing |
| 2026-07-08 | OIDC Trusted Publishing over API token | No long-lived PyPI secret in CI; per-repo pending publisher configured on pypi.org |
| 2026-07-08 | ISSO Keycloak password-grant for staging auth | Real auth mechanism for EORD staging; `client_id=eordui-stage`, `username=sa0000eord` |
| 2026-07-08 | Staging config sourced from integration-tests/pytest.ini | Single source of truth for connection parameters; credentials from env only |
| 2026-07-08 | `native/Cargo.toml` as single version source | Tag → Cargo.toml version → distribution version; avoids version drift |

### Key Constraints

- `domain/` must never import fastapi, requests, httpx, or any I/O library — enforced by ruff + test
- Mutation-guard is always on unless `GRAPHQL_ALLOW_MUTATIONS=true`; applies to both `query` and `raw`
- Schema cascade priority: GitLab (pinned SDL) > introspection (live) > `_service{sdl}` (federation) > SDL file (offline)
- CI wheel matrix: Linux manylinux+musllinux x86_64+aarch64, macOS arm64+x86_64, Windows AMD64, py3.10–3.12 + sdist
- GitHub repo stays `graphql-mcp` (rename deferred to REPO-01); PyPI dist is `generic-graphql-mcp`
- GraphQL_AUTH_TOKEN in integration-tests/pytest.ini is a placeholder; real auth is ISSO password-grant

### Blockers

None currently.

---

## Session Continuity

**Last session**: 2026-07-08 — v2.3 roadmap created (Phases 20-22)
**Next action**: Plan Phase 20 — CI Hardening (`/gsd-plan-phase 20`)
**Context**: v2.3 roadmap maps 10 requirements across 3 phases. CI hardening (Phase 20) unblocks the release workflow. Phase 21 ships the PyPI distribution via OIDC Trusted Publishing. Phase 22 wires the server against the live EORD staging federation gateway with Keycloak password-grant auth.
