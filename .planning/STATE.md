---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
last_updated: "2026-06-05T22:16:00.000Z"
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 7
  completed_plans: 7
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

Phase: 03 (Native & Faces) — COMPLETE ✅
Plan: 2 of 2 ✅
**Current phase**: Phase 3 — Native & Faces — COMPLETE ✅
**Current plan**: 03-02-PLAN.md ✅ complete — FastAPI REST + MCP stdio + CLI inbound adapters
**Status**: Phase 3 complete. All inbound adapters (REST, MCP stdio, CLI) live with 128 tests passing. Phase 4 (Ship) next.
**Phase goal**: The pyo3 JsonCodec crate builds via maturin, the orjson fallback passes the same parity test, and all four inbound adapters expose the full operation set. ✅ ACHIEVED

```
Progress: [███████████████░░░░░] 75% (Phase 3/4 ✅, Plan 2/2 ✅)
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases total | 4 |
| Phases complete | 3 |
| Requirements total | 10 |
| Requirements complete | 9 |
| Plans written | 7 |
| Plans complete | 7 |

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

- [x] Run `/gsd-plan-phase 1` to decompose Phase 1 into executable plans
- [x] Verify pyproject.toml maturin build-backend config before Phase 3
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
| 2026-06-05 | AST parse (not regex) for mutation detection | graphql-core OperationType.MUTATION — reliable, no false positives |
| 2026-06-05 | Unparseable queries pass through to server | Server-side validation decides; don't block on client parse errors |
| 2026-06-05 | SDL-hash caching via SHA-256 in SchemaAnalyzer | Avoid redundant build_schema() calls on same SDL |
| 2026-06-05 | build_schema fallback to assume_valid_sdl=True | Supergraph SDL has duplicate @link directives that fail strict mode |
| 2026-06-05 | Dual validation for supergraph detection | Both join__Graph enum AND @join__graph directive required — prevents false positives |
| 2026-06-05 | ErrorClass + QueryResult as runtime imports in lib.py | Needed for return values — cannot be TYPE_CHECKING only |
| 2026-06-05 | Mutation guard runs before transport None check | Block mutations even when no endpoint is configured |
| 2026-06-05 | respx mock uses trailing-slash URL | httpx base_url adds trailing slash on .post("") |
| 2026-06-05 | Upgraded pyo3 0.25 → 0.28 for pythonize compatibility | pythonize 0.28 (latest) requires pyo3 0.28; no compatible version for 0.25 |
| 2026-06-05 | pythonize for Python↔serde conversion | Direct object conversion; avoids double-serialization |
| 2026-06-05 | TYPE_CHECKING for JsonCodec in codec_factory | Satisfies ruff TCH001 |
| 2026-06-05 | Lazy singleton _get_client() in all adapters | Defers from_env() until first request; avoids startup cost |
| 2026-06-05 | CLI deferred imports in command handlers | Fast --help response; doesn't load GraphQLClient until command executes |
| 2026-06-05 | set_client() public API in rest.py | Explicit test injection without monkeypatching globals |
| 2026-06-05 | MCP tools as module-level functions | FastMCP @mcp.tool() decorator idiom; matches library pattern |

---

## Session Continuity

**Last session**: 2026-06-05 — Executed 03-02-PLAN.md (FastAPI REST + MCP stdio + CLI inbound adapters)
**Stopped at**: Completed 03-02-PLAN.md, Phase 3 fully complete
**Next action**: Plan and execute Phase 4 (Ship) — pytest suite + bench, CI wheel matrix, README + Glama publish
**Context needed for next session**: Phase 1-3 complete. All 6 operations wired through 4 faces (lib, REST, MCP stdio, CLI). Rust native codec + orjson fallback at parity. 128 tests passing. GQL-10 partially complete (native codec + faces done, CI + publish remains for Phase 4).
