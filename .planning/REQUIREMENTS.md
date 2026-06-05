# graphql-mcp — Requirements

**Project:** graphql-mcp (Investigation MCP Suite — v2 reference brick)
**Scope:** v1 (MVP — hexagonal skeleton, 6 operations, federation, Rust native, CI wheels)

---

## v1 Requirements

### Category: Operations (query execution)

- **GQL-01**: `query(query, variables)` returns `data` and `errors` separately as a typed `QueryResult`
- **GQL-02**: Every result carries `error_class` — one of `transport` / `graphql` / `ok`
- **GQL-03**: Mutation-guard in `query` and `raw`; mutations blocked unless `GRAPHQL_ALLOW_MUTATIONS=true`
- **GQL-09**: `raw(body)` accepts arbitrary POST body and returns `QueryResult` (mutation-guard applies)

### Category: Schema discovery

- **GQL-04**: `introspect()` returns a summary of Query fields and types from the active schema source
- **GQL-05**: `describe_type(name)` returns field/arg details plus owning subgraph when supergraph SDL is available
- **GQL-06**: Schema cascade — priority order GitLab → introspection → `_service{sdl}` → SDL file; TTL cache
- **GQL-07**: `refresh_schema()` clears schema cache and forces re-fetch from cascade

### Category: Federation

- **GQL-08**: `list_subgraphs()` returns `Subgraph{name, url, owned_types}` list parsed from supergraph SDL; graceful null degradation without supergraph

### Category: Ship / template

- **GQL-10**: Publishable v2 template: lib + stdio + FastAPI + CLI inbound faces; pyo3 JsonCodec crate with orjson fallback at parity; full CI wheel matrix (Linux manylinux/musllinux x86_64+aarch64, macOS arm64/x86_64, Windows AMD64, py3.10–3.12 + sdist); README and Glama publication

---

## Out of Scope (v1)

The following are explicitly deferred and must NOT be implemented in v1:

| Item | Reason |
|------|--------|
| Mutations by default | Security stance: read-only by default; guard enforced |
| Subscriptions | Out of scope for investigation use-case |
| Schema composition | Parsing only; no `@composeDirective` or composition tooling |
| `_entities(representations:)` tool | Deferred to v2 per §3.2 |
| LLM correlator / investigator flow | Lives in `investigator` repo, not this brick |
| Ordering/Kafka domain semantics | Other bricks; graphql-mcp is generic |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GQL-01 | Phase 2 | Pending |
| GQL-02 | Phase 2 | Pending |
| GQL-03 | Phase 2 | Pending |
| GQL-04 | Phase 2 | Pending |
| GQL-05 | Phase 2 | Pending |
| GQL-06 | Phase 1 | Complete |
| GQL-07 | Phase 2 | Pending |
| GQL-08 | Phase 2 | Pending |
| GQL-09 | Phase 2 | Pending |
| GQL-10 | Phase 3 + Phase 4 | Pending |
