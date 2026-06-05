# Phase 2: Operations, Errors & Federation - Research

**Researched:** 2026-06-06
**Domain:** GraphQL operations, mutation detection, federation supergraph parsing
**Confidence:** HIGH

## Summary

Phase 2 adds the six public operations to `GraphQLClient`: `query()`, `raw()`, `introspect()`, `describe_type()`, `list_subgraphs()`, and `refresh_schema()`. The transport layer and 3-class error typing (`ok`/`graphql`/`transport`) already exist in Phase 1's `HttpTransport.execute()` and `HttpTransport.post_raw()`. The primary new work is: (1) mutation guard enforcement using `graphql-core`'s AST parser, (2) schema analysis converting the resolved `SchemaGraph.sdl` into `SchemaSummary` and `TypeInfo` domain objects, and (3) federation ownership mapping by parsing `@join__type` and `@join__graph` directives from supergraph SDL.

All domain models are already defined in Phase 1: `QueryResult`, `SchemaSummary`, `TypeInfo`, `FieldInfo`, `Subgraph`, `ErrorClass`, and `MutationGuardError`. The implementation extends the existing hexagonal architecture — a new `SchemaAnalyzer` adapter module handles graphql-core parsing (keeping `domain/` free of graphql-core imports), and `GraphQLClient` gains the six operation methods that compose transport, schema service, and schema analyzer.

**Primary recommendation:** Create a `schema_analyzer.py` outbound adapter that encapsulates all graphql-core SDL parsing (SchemaSummary extraction, TypeInfo lookup, federation subgraph extraction), plus a `query_guard.py` utility for mutation detection via AST parsing. `GraphQLClient` methods remain thin orchestration, delegating to these modules.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
All implementation choices are at OpenCode's discretion — pure infrastructure phase. Use ROADMAP phase goal, success criteria, and codebase conventions to guide decisions.

Key constraints inherited from project decisions:
- D2: Library-first; MCP/REST/CLI are thin inbound adapters
- D7: Hexagonal architecture — domain has zero I/O or framework imports
- Mutation-guard is always on unless GRAPHQL_ALLOW_MUTATIONS=true; applies to both query and raw
- _entities tool is explicitly deferred to v2

Phase 1 established patterns:
- Frozen dataclasses for domain models
- typing.Protocol for port interfaces
- SchemaService with cascade and TTL cache
- GraphQLClient as the composition root in adapters/inbound/lib.py

### OpenCode's Discretion
All implementation choices — architecture of new modules, placement of parsing logic, config design.

### Deferred Ideas (OUT OF SCOPE)
- _entities(representations:) tool — deferred to v2 per spec section 3.2
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GQL-01 | `query(query, variables)` returns `data` and `errors` separately as a typed `QueryResult` | Transport already returns `QueryResult`; `GraphQLClient.query()` delegates to `transport.execute()` with mutation guard check |
| GQL-02 | Every result carries `error_class` — one of `transport`/`graphql`/`ok` | Already implemented in `HttpTransport.execute()` and `HttpTransport.post_raw()` — `ErrorClass` enum and classification logic exist |
| GQL-03 | Mutation-guard in `query` and `raw`; mutations blocked unless `GRAPHQL_ALLOW_MUTATIONS=true` | Use `graphql-core` `parse()` + `OperationType.MUTATION` check; `MutationGuardError` already defined; `config.allow_mutations` exists |
| GQL-04 | `introspect()` returns a summary of Query fields and types | `SchemaAnalyzer.build_summary()` converts `SchemaGraph.sdl` → `SchemaSummary` via `build_schema()` |
| GQL-05 | `describe_type(name)` returns field/arg details plus owning subgraph when supergraph SDL is available | `SchemaAnalyzer.describe_type()` uses `build_schema()` for field details + `parse()` for `@join__type` directive lookup |
| GQL-07 | `refresh_schema()` clears schema cache and forces re-fetch | Already implemented in `GraphQLClient.refresh_schema()` → `SchemaService.invalidate()` |
| GQL-08 | `list_subgraphs()` returns `Subgraph{name, url, owned_types}` parsed from supergraph SDL | `SchemaAnalyzer.list_subgraphs()` extracts `join__Graph` enum + `@join__graph` directives + `@join__type` ownership |
| GQL-09 | `raw(body)` accepts arbitrary POST body and returns `QueryResult` (mutation-guard applies) | `GraphQLClient.raw()` extracts `body["query"]` for mutation check, delegates to `transport.post_raw()` |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Query execution (`query`, `raw`) | API / Backend (transport adapter) | Client lib facade | Transport handles HTTP; facade adds mutation guard |
| Mutation detection | Adapter utility | — | Requires graphql-core AST parser (kept out of domain) |
| Error classification | API / Backend (transport adapter) | — | Already in HttpTransport — HTTP status + response parsing |
| Schema introspection (`introspect`) | Adapter utility (schema analyzer) | Domain (models) | Parsing SDL is computation; results are domain models |
| Type description (`describe_type`) | Adapter utility (schema analyzer) | — | SDL parsing + optional federation directive lookup |
| Federation ownership (`list_subgraphs`) | Adapter utility (schema analyzer) | — | Supergraph SDL parsing for @join__* directives |
| Schema cache refresh | Domain (SchemaService) | — | Already implemented: `invalidate()` clears TTL cache |
| Config (allow_mutations, supergraph_source) | Config layer | — | pydantic-settings reads GRAPHQL_* env vars |

## Standard Stack

### Core (already installed — Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| graphql-core | 3.2.11 | SDL parsing, AST analysis, schema building, mutation detection | [VERIFIED: pip show] Reference Python implementation; `parse()`, `build_schema()`, `OperationType` |
| pydantic | 2.13.4 | Domain model validation (frozen BaseModel) | [VERIFIED: pip show] Already used for all domain models |
| pydantic-settings | 2.14.1 | Env-var driven config (`GraphQLConfig`) | [VERIFIED: pip show] Already used for GRAPHQL_* config |
| httpx | 0.28.1 | HTTP transport for query execution | [VERIFIED: pip show] Already in `HttpTransport` |
| orjson | 3.11.8 | Fast JSON serialization | [VERIFIED: pip show] Already in `HttpTransport` |

### Dev (already installed — Phase 1)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.3.4 | Test runner | All tests |
| respx | 0.23.1 | httpx mock transport | Mocking GraphQL endpoint responses |
| ruff | 0.15.13 | Linting | Pre-commit and CI |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| graphql-core `parse()` for mutation detection | Regex on query string | Regex is fragile with edge cases (comments, string literals); AST parse is definitive |
| `build_schema()` for schema analysis | Manual SDL regex parsing | `build_schema()` handles all GraphQL type kinds correctly; manual parsing misses edge cases |

**Installation:** No new packages needed — all dependencies installed in Phase 1.

## Architecture Patterns

### System Architecture Diagram

```
User Code
   │
   ▼
┌─────────────────────────────────────────────────┐
│  GraphQLClient (adapters/inbound/lib.py)        │
│  ┌───────────┐ ┌──────────┐ ┌────────────────┐ │
│  │ query()   │ │ raw()    │ │ introspect()   │ │
│  │ ──guard──►│ │ ──guard──│ │ describe_type()│ │
│  │   ▼       │ │    ▼     │ │ list_subgraphs │ │
│  │ transport │ │ transport│ │ refresh_schema │ │
│  └───────────┘ └──────────┘ └────────────────┘ │
│        │              │              │          │
│        ▼              ▼              ▼          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │QueryGuard│  │QueryGuard│  │SchemaAnalyzer│  │
│  │(mutation │  │(mutation │  │(SDL→Summary, │  │
│  │ detect)  │  │ detect)  │  │ TypeInfo,    │  │
│  └──────────┘  └──────────┘  │ Subgraphs)   │  │
│                              └──────────────┘  │
└────────┬──────────────┬──────────────┬──────────┘
         │              │              │
         ▼              ▼              ▼
   ┌───────────┐  ┌───────────┐  ┌───────────┐
   │ Transport │  │ Transport │  │SchemaServ. │
   │ (port)    │  │ (port)    │  │ (domain)   │
   │  ▼        │  │  ▼        │  │  ▼         │
   │HttpTranspt│  │HttpTranspt│  │ cascade +  │
   │(outbound) │  │(outbound) │  │ TTL cache  │
   └───────────┘  └───────────┘  └───────────┘
         │              │              │
         ▼              ▼              ▼
   GraphQL Endpoint          Schema Sources
                        (GitLab/introspect/
                         _service/file)
```

### Recommended Project Structure (additions to Phase 1)
```
src/graphql_mcp/
├── domain/
│   ├── models.py           # EXISTING — already has all needed models
│   ├── errors.py           # EXISTING — already has MutationGuardError
│   └── schema_service.py   # EXISTING — TTL cache + cascade
├── ports/
│   ├── transport.py        # EXISTING — GraphQLTransport protocol
│   └── schema_source.py    # EXISTING — SchemaSource protocol
├── adapters/
│   ├── inbound/
│   │   └── lib.py          # EXTEND — add query/raw/introspect/describe_type/list_subgraphs
│   └── outbound/
│       ├── http_transport.py    # EXISTING — execute/post_raw with error_class
│       ├── schema_analyzer.py   # NEW — SDL→SchemaSummary, TypeInfo, Subgraph[]
│       └── query_guard.py       # NEW — mutation detection via graphql-core parse()
└── config.py               # EXTEND — add supergraph_source field
```

### Pattern 1: Mutation Guard via AST Parse
**What:** Parse the GraphQL query string into an AST and check for `OperationType.MUTATION` in any operation definition.
**When to use:** Before every `query()` and `raw()` call when `config.allow_mutations` is `False`.
**Example:**
```python
# Source: verified via graphql-core 3.2.11 interactive testing
from graphql import parse
from graphql.language.ast import OperationType

def contains_mutation(query_str: str) -> bool:
    """Check if a GraphQL query string contains a mutation operation."""
    try:
        doc = parse(query_str)
        return any(
            hasattr(defn, "operation") and defn.operation == OperationType.MUTATION
            for defn in doc.definitions
        )
    except Exception:
        return False  # Unparseable → let the server decide
```

**Key behaviors verified:** [VERIFIED: graphql-core 3.2.11 interactive]
- `parse('mutation { ... }')` → `OperationType.MUTATION` ✓
- `parse('mutation CreateUser { ... }')` → `OperationType.MUTATION` ✓
- `parse('{ users { id } }')` → `OperationType.QUERY` ✓
- `parse('query { users { id } }')` → `OperationType.QUERY` ✓
- `parse('{ mutationLog { id } }')` → `OperationType.QUERY` (field named "mutation" is NOT a mutation operation) ✓
- Multi-operation documents: each definition has its own `operation` ✓
- `parse('subscription { ... }')` → `OperationType.SUBSCRIPTION` (not blocked by mutation guard) ✓

### Pattern 2: Federation Subgraph Extraction from Supergraph SDL
**What:** Parse supergraph SDL to extract subgraph metadata from `join__Graph` enum with `@join__graph` directives, then map type ownership via `@join__type` directives.
**When to use:** `list_subgraphs()` and `describe_type()` when the resolved schema is a supergraph.
**Example:**
```python
# Source: verified via graphql-core 3.2.11 interactive testing
from graphql import parse
from graphql.language.ast import EnumTypeDefinitionNode

doc = parse(supergraph_sdl)

# Step 1: Extract subgraphs from join__Graph enum
subgraphs = {}  # enum_value → {name, url}
for defn in doc.definitions:
    if isinstance(defn, EnumTypeDefinitionNode) and defn.name.value == "join__Graph":
        for value in defn.values:
            for d in (value.directives or []):
                if d.name.value == "join__graph":
                    args = {a.name.value: a.value.value for a in d.arguments}
                    subgraphs[value.name.value] = {
                        "name": args.get("name", ""),
                        "url": args.get("url", ""),
                    }

# Step 2: Map types to owning subgraphs via @join__type
type_ownership = {}  # type_name → [enum_values]
for defn in doc.definitions:
    if hasattr(defn, "name") and defn.name and hasattr(defn, "directives"):
        for d in (defn.directives or []):
            if d.name.value == "join__type":
                args = {a.name.value: a.value for a in d.arguments}
                graph_val = args.get("graph")
                if graph_val:
                    type_ownership.setdefault(defn.name.value, []).append(graph_val.value)
```

### Pattern 3: Schema Summary Extraction
**What:** Convert resolved `SchemaGraph.sdl` into `SchemaSummary` with query fields and type list.
**When to use:** `introspect()` operation.
**Example:**
```python
# Source: verified via graphql-core 3.2.11 interactive testing
from graphql import build_schema, GraphQLObjectType, GraphQLEnumType, ...

schema = build_schema(sdl)

# Query fields
query_fields = list(schema.query_type.fields.keys()) if schema.query_type else []

# Type summaries (exclude builtins)
type_map = {
    GraphQLObjectType: "OBJECT",
    GraphQLInterfaceType: "INTERFACE",
    GraphQLEnumType: "ENUM",
    GraphQLUnionType: "UNION",
    GraphQLInputObjectType: "INPUT_OBJECT",
    GraphQLScalarType: "SCALAR",
}
types = [
    TypeSummary(name=name, kind=type_map.get(type(obj), ""), description=obj.description or "")
    for name, obj in schema.type_map.items()
    if not name.startswith("__")
]
```

### Pattern 4: Describe Type with Federation Subgraph
**What:** Look up a named type in the built schema for field/arg details, then check the parsed AST for `@join__type` directive to find the owning subgraph.
**When to use:** `describe_type(name)` operation.
**Example:**
```python
# Source: verified via graphql-core 3.2.11 interactive testing
from graphql import build_schema

schema = build_schema(sdl)
type_obj = schema.type_map.get(type_name)

# Fields (for OBJECT/INTERFACE types that have fields)
if hasattr(type_obj, "fields"):
    fields = [
        FieldInfo(
            name=fname,
            type_str=str(fobj.type),
            description=fobj.description or "",
            args=[f"{aname}: {aobj.type}" for aname, aobj in fobj.args.items()],
        )
        for fname, fobj in type_obj.fields.items()
    ]

# Subgraph: found via @join__type directive on the type's ast_node
# build_schema() preserves directives on ast_node
subgraph = None
if type_obj.ast_node and type_obj.ast_node.directives:
    for d in type_obj.ast_node.directives:
        if d.name.value == "join__type":
            args = {a.name.value: a.value for a in d.arguments}
            graph_val = args.get("graph")
            if graph_val:
                subgraph = subgraph_enum_to_name.get(graph_val.value, graph_val.value)
```

### Anti-Patterns to Avoid
- **Importing graphql-core in `domain/`:** Keep `domain/` free of external library imports (only `pydantic` for models). All graphql-core usage goes in `adapters/outbound/`.
- **Regex-based mutation detection:** While it works for simple cases, AST parsing via `graphql.parse()` is definitive and handles all edge cases (comments, string literals, multi-operation documents).
- **Blocking subscriptions in mutation guard:** The mutation guard ONLY blocks `OperationType.MUTATION`, not subscriptions. Subscriptions are out of scope for v1 but should not be erroneously blocked.
- **Raising on unparseable queries in mutation guard:** If `parse()` fails on an invalid query string, the guard should let it through — the server will return a proper GraphQL error. Only block definitively detected mutations.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mutation detection | Regex-based query scanning | `graphql.parse()` + `OperationType.MUTATION` | [VERIFIED: graphql-core] Handles comments, string literals, multi-op docs, named/anonymous mutations |
| SDL type extraction | Manual SDL string parsing | `graphql.build_schema()` + `schema.type_map` | [VERIFIED: graphql-core] Correct type kind mapping, field/arg extraction, description handling |
| Federation directive parsing | Custom directive parser | `graphql.parse()` AST + `EnumTypeDefinitionNode` | [VERIFIED: graphql-core] Handles all Apollo Federation v2 join spec directives |
| Error classification | Custom HTTP response parser | Existing `HttpTransport.execute()` logic | [VERIFIED: codebase] Already classifies transport/graphql/ok based on HTTP status + response body |

**Key insight:** graphql-core 3.2.11 provides everything needed for this phase — AST parsing, schema building, type introspection, and directive access. No additional libraries required.

## Common Pitfalls

### Pitfall 1: Mutation Guard on raw() Missing the Query Field
**What goes wrong:** `raw(body)` receives an arbitrary dict. If the dict has no `"query"` key, the mutation guard cannot detect mutations.
**Why it happens:** The GraphQL-over-HTTP spec allows arbitrary POST bodies.
**How to avoid:** If `body` has a `"query"` key, parse and check it. If no `"query"` key, let it through — the server will handle it. Never raise `MutationGuardError` on a body we can't analyze.
**Warning signs:** Tests that send bodies without `"query"` key and expect them to be blocked.

### Pitfall 2: Supergraph Detection False Positives
**What goes wrong:** A schema that uses `join__Graph` as a type name but isn't actually a supergraph.
**Why it happens:** `join__Graph` is technically a valid user-defined type name.
**How to avoid:** Check for BOTH the `join__Graph` enum AND at least one `@join__graph` directive on an enum value. This combination is extremely unlikely in non-supergraph schemas.
**Warning signs:** `list_subgraphs()` returning malformed data on non-supergraph schemas.

### Pitfall 3: build_schema() Failing on Supergraph SDL
**What goes wrong:** Supergraph SDL may contain directives (`@join__type`, `@join__field`, etc.) that `build_schema()` rejects if their definitions are missing.
**Why it happens:** `build_schema()` validates directive usage against declared directives.
**How to avoid:** Ensure the supergraph SDL includes the directive declarations (which Apollo Gateway always includes). If parsing fails, fall back to SDL-only analysis via `parse()`.
**Warning signs:** `GraphQLError` from `build_schema()` mentioning unknown directives. [VERIFIED: tested that supergraph SDL with directive declarations parses correctly]

### Pitfall 4: Frozen Model Mutation
**What goes wrong:** Attempting to modify a `QueryResult` or `TypeInfo` after creation raises a validation error.
**Why it happens:** All domain models use `ConfigDict(frozen=True)`.
**How to avoid:** Always create new model instances; never try to mutate existing ones.
**Warning signs:** `ValidationError: Instance is frozen` errors.

### Pitfall 5: Missing Transport in GraphQLClient
**What goes wrong:** `query()` or `raw()` called when no endpoint was configured, so `self._transport` is `None`.
**Why it happens:** `GraphQLClient.from_env()` allows creating a client without an endpoint (for schema-only operations).
**How to avoid:** Check `self._transport is not None` before delegating to transport. Raise a clear error if transport is missing for query/raw operations.
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'execute'`.

### Pitfall 6: SchemaAnalyzer Caching
**What goes wrong:** `build_schema()` is called on every `introspect()` or `describe_type()` call, even when the underlying SDL hasn't changed.
**Why it happens:** `SchemaAnalyzer` doesn't cache the built schema.
**How to avoid:** Cache the built schema keyed on the SDL string hash. Since `SchemaService` already caches the `SchemaGraph`, the analyzer should cache its derived objects too. Invalidate when `refresh_schema()` is called.
**Warning signs:** Latency increase on repeated `introspect()` calls.

## Code Examples

### Example 1: GraphQLClient.query() Implementation Pattern
```python
# Source: architecture analysis of existing codebase
def query(self, query: str, variables: dict[str, Any] | None = None) -> QueryResult:
    """Execute a GraphQL query and return typed result."""
    if self._transport is None:
        return QueryResult(
            errors=[{"message": "No endpoint configured"}],
            error_class=ErrorClass.TRANSPORT,
        )
    if not self._allow_mutations:
        _check_mutation_guard(query)  # raises MutationGuardError
    return self._transport.execute(query, variables)
```

### Example 2: GraphQLClient.raw() Implementation Pattern
```python
# Source: architecture analysis of existing codebase + requirements
def raw(self, body: dict[str, Any]) -> QueryResult:
    """Send arbitrary POST body and return typed result."""
    if self._transport is None:
        return QueryResult(
            errors=[{"message": "No endpoint configured"}],
            error_class=ErrorClass.TRANSPORT,
        )
    if not self._allow_mutations:
        query_str = body.get("query")
        if isinstance(query_str, str):
            _check_mutation_guard(query_str)
    return self._transport.post_raw(body)
```

### Example 3: SchemaAnalyzer Usage Pattern
```python
# Source: architecture analysis
class SchemaAnalyzer:
    """Adapter: parses SDL into domain model objects."""

    def build_summary(self, sdl: str) -> SchemaSummary:
        schema = build_schema(sdl)
        query_fields = list(schema.query_type.fields.keys()) if schema.query_type else []
        types = [...]  # see Pattern 3
        return SchemaSummary(query_fields=query_fields, types=types)

    def describe_type(self, sdl: str, type_name: str) -> TypeInfo | None:
        schema = build_schema(sdl)
        type_obj = schema.type_map.get(type_name)
        if type_obj is None:
            return None
        # ... build FieldInfo list, find subgraph from directives
        return TypeInfo(name=type_name, kind=kind, fields=fields, subgraph=subgraph)

    def list_subgraphs(self, sdl: str) -> list[Subgraph]:
        doc = parse(sdl)
        # ... extract from join__Graph enum + @join__type
        return [Subgraph(name=..., url=..., owned_types=...) for ...]
```

### Example 4: Config Extension
```python
# Source: existing config.py pattern
class GraphQLConfig(BaseSettings):
    # ... existing fields ...
    supergraph_source: str = "auto"  # auto|off
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Federation v1 (`@key`, `@external`) | Federation v2 (`@join__type`, `@join__field`, `@join__graph`) | Apollo Router 1.0 (2022) | Supergraph SDL uses `join__` prefix directives; v1 directives are on subgraph SDL only |
| `graphql-core` 3.1.x | `graphql-core` 3.2.11 (latest) | 2023 | Current and stable; no deprecations affecting our usage |

**Deprecated/outdated:**
- Apollo Federation v1 directives (`@key`, `@external`, `@provides`, `@requires`): These appear in subgraph SDL, NOT in the composed supergraph SDL. The supergraph uses `@join__*` directives. [VERIFIED: tested with sample supergraph SDL]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `supergraph_source` config uses values `auto` or `off` with `auto` as default | Architecture Patterns | Low — easily changed; success criteria references `GRAPHQL_SUPERGRAPH_SOURCE=off` |
| A2 | Unparseable queries in mutation guard should be allowed through (not blocked) | Anti-Patterns | Medium — alternative is to block unparseable queries; depends on security stance |
| A3 | `SchemaAnalyzer` should cache built schema objects keyed on SDL hash | Common Pitfalls | Low — performance optimization; can start without caching |

## Open Questions

1. **Handling subscriptions in mutation guard**
   - What we know: The guard blocks `OperationType.MUTATION` only. Subscriptions use `OperationType.SUBSCRIPTION`.
   - What's unclear: Should subscriptions also be blocked? They're out of scope for v1.
   - Recommendation: Don't block subscriptions. The mutation guard is specifically about preventing writes. If subscriptions are attempted, the server will reject them if not supported. This matches the requirement text ("mutations blocked").

2. **SchemaAnalyzer caching strategy**
   - What we know: `SchemaService` caches `SchemaGraph` (which contains SDL). `SchemaAnalyzer.build_schema()` is expensive.
   - What's unclear: Should analyzer cache be separate or tied to `SchemaService` TTL?
   - Recommendation: Simple approach — `SchemaAnalyzer` caches per SDL string. When `refresh_schema()` is called, the new `SchemaGraph` has a new SDL, so the analyzer's cache misses naturally. No explicit invalidation needed.

3. **Graceful degradation when transport is None**
   - What we know: `GraphQLClient.from_env()` allows no endpoint. `query()` and `raw()` need transport.
   - What's unclear: Should `query()` without transport return a `QueryResult` with `error_class=transport` or raise an exception?
   - Recommendation: Return a `QueryResult` with `error_class=ErrorClass.TRANSPORT` and an error message. This keeps the API consistent — callers always get a `QueryResult`, never an unexpected exception from query/raw.

## Project Constraints (from codebase conventions)

- `domain/` must never import `httpx`, `requests`, `fastapi`, `pathlib`, or any I/O library — enforced by `ruff` + `test_domain_purity.py`
- `graphql-core` (the `graphql` package) is NOT in the forbidden list, but existing convention keeps it in `adapters/outbound/` only
- All domain models use `ConfigDict(frozen=True)` — immutable
- Ports use `typing.Protocol` with `@runtime_checkable`
- Tests use `PYTHONPATH=src` (maturin build-backend prevents standard `pip install -e`)
- Test runner: `pytest` with `testpaths = ["tests"]`
- Linting: `ruff` with `select = ["E", "F", "I", "UP", "B", "SIM", "TCH"]`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — bearer token passed through, not managed |
| V3 Session Management | No | N/A — stateless client library |
| V4 Access Control | Yes | Mutation guard blocks write operations by default (`GRAPHQL_ALLOW_MUTATIONS=false`) |
| V5 Input Validation | Yes | `graphql.parse()` validates query syntax; `pydantic` validates config and domain models |
| V6 Cryptography | No | N/A — no crypto operations in this phase |

### Known Threat Patterns for GraphQL Client

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Mutation injection via raw() | Tampering | Mutation guard parses query AST before sending; blocks if `OperationType.MUTATION` detected |
| Unparseable query bypass | Tampering | If `parse()` fails, query passes through — server-side validation is the fallback. This is intentional: the client guard is defense-in-depth, not the only control. |
| Config override injection | Elevation | `pydantic-settings` validates types; `allow_mutations` is `bool` — cannot be tricked with string values |

## Sources

### Primary (HIGH confidence)
- [VERIFIED: graphql-core 3.2.11 interactive] — `parse()`, `OperationType`, `build_schema()`, `EnumTypeDefinitionNode`, directive extraction from AST, `ast_node` preservation in `build_schema()`
- [VERIFIED: pip show] — All package versions confirmed installed
- [VERIFIED: pytest] — 13/13 tests pass on current codebase
- [VERIFIED: Context7 /graphql-python/graphql-core] — API reference for `parse()`, `build_schema()`, `build_client_schema()`

### Secondary (MEDIUM confidence)
- Apollo Federation v2 supergraph SDL format — based on Apollo documentation patterns; supergraph SDL structure with `@join__*` directives

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all packages verified installed, versions confirmed, APIs tested interactively
- Architecture: HIGH — all patterns verified with working code; hexagonal boundaries clear
- Pitfalls: HIGH — edge cases tested interactively (mutation detection, supergraph parsing, error handling)

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (stable — graphql-core 3.2.x is mature, no breaking changes expected)
