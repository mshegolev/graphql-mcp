---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-06-05T20:20:01Z"
progress:
  total_phases: 4
  completed_phases: 1
  total_plans: 3
  completed_plans: 3
  percent: 25
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

Phase: 01 (Foundation & Schema Sources) — COMPLETE
Plan: 3 of 3 (all complete)
**Current phase**: Phase 1 — Foundation & Schema Sources — COMPLETE
**Current plan**: All plans complete
**Status**: Phase 1 complete, ready for Phase 2
**Phase goal**: The hexagonal skeleton compiles and the schema cascade resolves a live or offline schema through all four source adapters.

```
Progress: [█████░░░░░░░░░░░░░░░] 25% (Phase 1/4, Plan 3/3 ✅)
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases total | 4 |
| Phases complete | 1 |
| Requirements total | 10 |
| Requirements complete | 1 |
| Plans written | 3 |
| Plans complete | 3 |

---

## Accumulated Context

### Architecture Decisions (inherited from umbrella)

- D1: Hybrid — deterministic collectors + optional LLM correlator (approach C)
- D2: Library-first; MCP/REST/CLI are thin inbound adapters
- D5: Python core + Rust hot paths (pyo3/maturin); pure-Python orjson fallback
- D7: Hexagonal architecture — domain has zero I/O or framework imports
- D8: FastAPI primary face (k8s/team sharing); stdio second (Glama + local agent)
- D9: Rust JsonCodec via pyo3; orjson fallback; parity under test; maturin CI

### Key Constraints

- `domain/` must never import fastapi, requests, httpx, or any I/O library — enforced by ruff + test
- Mutation-guard is always on unless `GRAPHQL_ALLOW_MUTATIONS=true`; applies to both `query` and `raw`
- Schema cascade priority: GitLab (pinned SDL) > introspection (live) > `_service{sdl}` (federation) > SDL file (offline)
- `_entities` tool is explicitly deferred to v2
- CI wheel matrix: Linux manylinux+musllinux x86_64+aarch64, macOS arm64+x86_64, Windows AMD64, py3.10–3.12 + sdist

### Build Order (within brick)

domain → ports → outbound adapters (http/schema sources) → Rust native + orjson fallback (parity test) → inbound adapters (lib → mcp_stdio → FastAPI → CLI) → tests/bench → CI wheels → README + Glama

### Todos

- [ ] Run `/gsd-plan-phase 1` to decompose Phase 1 into executable plans
- [ ] Verify pyproject.toml maturin build-backend config before Phase 3
- [ ] Confirm Glama submission requirements before Phase 4

### Blockers

None currently.

### Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-05 | 4 coarse phases derived from build order | Granularity=coarse; build order maps cleanly to Foundation/Operations/Native+Faces/Ship |
| 2026-06-05 | GQL-10 split across Phase 3 (native+faces) and Phase 4 (CI+publish) | Single requirement spans two natural delivery boundaries; both phases required for full v2 template |
| 2026-06-05 | Used respx (not responses) for httpx mocking | respx is purpose-built for httpx; RESEARCH.md recommended it |
| 2026-06-05 | Added .gitignore for build artifacts | Cargo workspace generates target/ and Cargo.lock; must not be tracked |
| 2026-06-05 | SchemaService uses time.monotonic() for TTL cache | stdlib, no I/O imports needed in domain layer |
| 2026-06-05 | HttpTransport uses orjson.dumps() for request body | Consistency with future Rust native codec path |
| 2026-06-05 | GitLab /raw endpoint (not base64) | Returns raw SDL text directly; avoids decoding step |
| 2026-06-05 | build_client_schema for introspection | Introspection JSON requires client-side builder, not build_schema |
| 2026-06-05 | from_env(**overrides: Any) not str | Config has int/bool fields; pydantic-settings coerces at runtime |
| 2026-06-05 | TYPE_CHECKING block for domain imports in lib.py | Satisfies ruff TC001; domain types only needed for annotations |

---

## Session Continuity

**Last session**: 2026-06-05 — Executed 01-03-PLAN.md (Config, GraphQLClient.from_env(), test suite)
**Next action**: Plan Phase 2 — Operations, Errors & Federation
**Context needed for next session**: Phase 1 complete. Full hexagonal skeleton working: domain models (SchemaGraph, QueryResult, TypeInfo, etc.), ports (SchemaSource, GraphQLTransport, JsonCodec), SchemaService with TTL cascade, 4 outbound adapters (GitLab, introspection, federation SDL, file), HttpTransport with 3-class error typing, GraphQLConfig (pydantic-settings), GraphQLClient.from_env() composition root, `from graphql_mcp import GraphQLClient` works. 13 tests pass: domain purity, cascade fallback, TTL cache. Need Phase 2: operations (query, raw, introspect, describe_type, list_subgraphs, refresh_schema), mutation guard, federation ownership.
