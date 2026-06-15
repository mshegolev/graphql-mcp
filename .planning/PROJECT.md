# graphql-mcp — brick project

> Part of **Investigation MCP Suite** (umbrella: `/opt/develop/aiqa/investigate-suite/`).
> Full design: `/opt/develop/aiqa/docs/superpowers/specs/2026-06-05-investigation-mcp-suite-design.md` (§3).
> This is the **v2 reference brick** — its skeleton is copied by kafka-mcp / ordering-mcp.

## What This Is

Генерик read-only GraphQL MCP-кирпич: discovery схемы + выполнение query + типизация
ошибок, с актуальной схемой из нескольких источников и federation ownership-маппингом
(поле → сабграф → serviceName). Library-first: `from graphql_mcp import GraphQLClient`
работает в pytest без сети/MCP/FastAPI.

## Architecture (hexagonal v2, копируется в остальные кирпичи)

```
src/graphql_mcp/
  domain/    models.py errors.py query_service.py schema_service.py federation.py   # чистое, без I/O
  ports/     transport.py schema_source.py json_codec.py                            # Protocol
  adapters/
    inbound/  rest_api.py(FastAPI) mcp_stdio.py lib.py(GraphQLClient) cli.py
    outbound/ http_transport.py gitlab_source.py introspection_source.py
              service_sdl_source.py file_source.py json_native.py(Rust) json_orjson.py(fallback)
  config.py  server.py(composition root + main()/serve())
native/      Cargo.toml src/lib.rs   # pyo3 крейт graphql_mcp_native
```

Стек: `mcp>=1.27`, `fastapi`+`uvicorn[standard]`, `graphql-core>=3.3`, `gql`+`httpx`/`requests`,
`orjson>=3.10`, `pydantic>=2.8`; build `maturin>=0.15`+`pyo3>=0.22`; CI `cibuildwheel>=2.21`
(Linux manylinux/musllinux x86_64+aarch64, macOS arm64/x86_64, Windows AMD64, py3.10–3.12 + sdist);
dev `pytest`/`responses`/`ruff`/`pytest-benchmark`.

## Requirements (v1) — GQL-01..10

- [ ] **GQL-01**: `query(query, variables)` → `data` и `errors` раздельно
- [ ] **GQL-02**: классификация исхода `transport`/`graphql`/`ok`
- [ ] **GQL-03**: mutation-guard в `query` и `raw`; флаг `GRAPHQL_ALLOW_MUTATIONS`
- [ ] **GQL-04**: `introspect` — сводка Query-полей/типов
- [ ] **GQL-05**: `describe_type` — детали типа + owning subgraph при supergraph SDL
- [ ] **GQL-06**: каскад схемы GitLab→introspection→`_service{sdl}`→файл
- [ ] **GQL-07**: `refresh_schema` — сброс кэша
- [ ] **GQL-08**: `list_subgraphs` (federation)
- [ ] **GQL-09**: `raw` — произвольное тело (под guard)
- [ ] **GQL-10**: v2-шаблон (lib+stdio+FastAPI+CLI), pyo3+orjson паритет, CI-wheels, Glama

Anti/out-of-scope: мутации by default, schema composition.
~~subscriptions~~ → v2.0, ~~`_entities`~~ → shipped v1.1.

## ⭐ Investigator Contract (что обязан отдавать lib-фасад)

`investigator` импортирует этот кирпич как либу (НЕ через MCP) и строит из ответов
нормализованные **Evidence**:

```python
from graphql_mcp import GraphQLClient
c = GraphQLClient.from_env()           # или GraphQLClient(endpoint=..., headers=...)

QueryResult = c.query(query: str, variables: dict | None = None)
# -> QueryResult{ data: dict|None, errors: list[dict]|None, error_class: Literal["transport","graphql","ok"] }
QueryResult = c.raw(body: dict)                 # тот же QueryResult, mutation-guard применяется
SchemaSummary = c.introspect()                  # query-поля + типы (из активного источника схемы)
TypeInfo = c.describe_type(name: str)           # TypeInfo{ name, fields, args, subgraph: str|None }
list[Subgraph] = c.list_subgraphs()             # Subgraph{ name, url: str|None, owned_types: list[str] }
c.refresh_schema()                              # -> None
```

**Зачем investigator'у:**
- `query()` — достать наличие/состояние продуктов в каталоге, подключённые продукты пользователю, спеки.
- `describe_type()`/`list_subgraphs()` — **мостик корреляции**: GQL-поле → owning subgraph → `service_name` (→ Jaeger/OpenSearch). Без supergraph SDL `subgraph=null` (мягкая деградация).

**Обязательно surface для шины улик (Evidence):**
- `error_class` — чтобы investigator отличал «сервис лёг» (transport) от «спросили не то» (graphql).
- owning `subgraph` для маппинга в service_name.
- `keys`: любые id из `data` (order_id, product_id, msisdn, customer_id) — investigator вытащит экстрактором.
- `timestamp_utc`: время запроса (GQL — не time-series, но фиксируем момент сбора).
- `raw`: полный ответ для drill-down.

Evidence-форма (строит адаптер investigator'а, кирпич просто отдаёт сырьё + поля):
`Evidence{ source="graphql", event_type="gql_result", timestamp_utc, keys{...}, payload{...}, raw }`

## Build order (внутри кирпича)

domain → ports → outbound (http/schema sources) → Rust native + orjson fallback (паритет-тест)
→ inbound (lib → mcp_stdio → FastAPI → cli) → tests/bench → CI-wheels → README+Glama.

## Decisions (наследуются от зонтика)
D1 гибрид C · D2 library-first · D5 Python+Rust · D7 hexagonal · D8 FastAPI+stdio · D9 pyo3+fallback.

## Current Milestone: v2.0 Production-Grade Platform

**Goal:** Transform graphql-mcp from a feature-complete brick into a production-grade, observable, secure platform with real-time capabilities and a reusable template for the suite.

**Target features:**
- OpenTelemetry tracing/metrics/logs across all operations and transports
- Security hardening: mTLS, token rotation, RBAC header forwarding, audit logging, rate limiting, input validation
- DX & Ecosystem: PyPI publish pipeline, GitHub Actions CI, better error messages, SDK examples, integration test harness
- GraphQL subscriptions via WebSocket (graphql-ws) + SSE fallback, streaming response support
- Copier template extraction for kafka-mcp/ordering-mcp reuse

## Validated Requirements

### v1.0 MVP (shipped 2026-06-05)
- [x] GQL-01..GQL-10 (all 10 requirements satisfied)

### v1.1 Production Hardening (shipped 2026-06-08)
- [x] HARD-01..03, PERF-01..03, FACE-01..04, ENT-01, SHIP-01..02 (all 13 requirements satisfied)

### v2.0 Production-Grade Platform (active)
- See REQUIREMENTS.md for active requirements

## Key Decisions

| Version | Decision | Rationale |
|---------|----------|-----------|
| v1.0 | D1-D9 from umbrella spec | Foundational architecture |
| v1.1 | Separate AsyncGraphQLClient | Clean API boundary |
| v1.1 | _entities as pass-through | Gateway resolves; client proxies |
| v2.0 | OpenTelemetry (not just structlog) | Industry standard; exports to Jaeger/Prometheus already in the suite |
| v2.0 | WebSocket + SSE for subscriptions | graphql-ws protocol + SSE fallback for simpler consumers |
| v2.0 | Copier for template extraction | Supports reruns/updates unlike cookiecutter |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Brick brief — запускай агента в этой репе и реализуй методы из Investigator Contract.*
*Last updated: 2026-06-16*
