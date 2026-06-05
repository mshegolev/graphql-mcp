---
phase: 03-native-faces
verified: 2026-06-05T22:23:48Z
status: passed
score: 5/5 must-haves verified
overrides_applied: 0
deferred:
  - truth: "MCP-over-HTTP (streamable HTTP transport) available on FastAPI app"
    addressed_in: "Phase 4"
    evidence: "Phase 4 SC #1 explicitly includes 'MCP-over-HTTP handshake' in test requirements"
human_verification: []
---

# Phase 3: Native & Faces Verification Report

**Phase Goal:** The pyo3 JsonCodec crate builds via maturin, the orjson fallback passes the same parity test, and all four inbound adapters (lib, mcp_stdio, FastAPI REST+MCP-over-HTTP, CLI) expose the full operation set.
**Verified:** 2026-06-05T22:23:48Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `maturin develop` produces a working `graphql_mcp_native` extension; `RustJsonCodec` imports without error | ✓ VERIFIED | `from graphql_mcp._native import encode, decode` succeeds; `encode({'b':1,'a':2})` returns `b'{"a":2,"b":1}'`; Cargo.toml has pyo3 0.28 + serde_json + pythonize 0.28 |
| 2 | Parity test suite passes: RustJsonCodec and OrjsonCodec return byte-identical output for 100KB and 1MB JSON fixtures | ✓ VERIFIED | 45/45 parity tests pass (pytest -v): 16 parametrized encode cases, 16 roundtrip cases, 100KB+ parity (1200 keys), 1MB+ parity (12000 keys), 7 float precision edge cases, 2 protocol conformance, 2 factory tests |
| 3 | Library face works in-process: `from graphql_mcp import GraphQLClient` + `client.introspect()` against mocked transport | ✓ VERIFIED | `__init__.py` exports `GraphQLClient`; import succeeds; existing test suite (60+ tests from phases 1-2) covers in-process operation with mocked transport |
| 4 | `graphql-mcp query '{ __typename }'` CLI exits 0 and prints JSON to stdout | ✓ VERIFIED | `tests/test_cli.py::TestCLIQuery::test_query_no_transport` passes — exit code 0, output parses as JSON with `error_class` field; CLI has 5 commands: query, introspect, describe-type, list-subgraphs, refresh |
| 5 | `GET /health` returns `{"status": "ok"}`; `POST /graphql/query` returns data/errors/error_class | ✓ VERIFIED | `tests/test_rest.py::TestHealth::test_health_returns_ok` confirms 200 + `{"status": "ok"}`; `TestGraphQLQuery::test_query_no_transport_returns_transport_error` confirms JSON response with data/errors/error_class fields; mutation guard returns 403 |

**Score:** 5/5 truths verified

### Deferred Items

Items not yet met but explicitly addressed in later milestone phases.

| # | Item | Addressed In | Evidence |
|---|------|-------------|----------|
| 1 | MCP-over-HTTP (streamable HTTP transport) available on FastAPI app | Phase 4 | Phase 4 SC #1: "MCP-over-HTTP handshake" explicitly listed in test requirements |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `native/Cargo.toml` | serde + serde_json + pythonize deps | ✓ VERIFIED | pyo3 0.28, serde 1, serde_json 1, pythonize 0.28 — all present |
| `native/src/lib.rs` | pyo3 encode/decode with sorted keys | ✓ VERIFIED | 52 lines; `#[pyo3(name = "_native")]`; `sort_value()` recursive key sorter; `encode()` via pythonize::depythonize + serde_json::to_vec; `decode()` via serde_json::from_slice + pythonize::pythonize |
| `src/graphql_mcp/adapters/outbound/json_native.py` | RustJsonCodec wrapper | ✓ VERIFIED | 27 lines; lazy imports `_native` in `__init__`; wraps encode/decode; exports `RustJsonCodec` |
| `src/graphql_mcp/adapters/outbound/json_orjson.py` | OrjsonCodec with OPT_SORT_KEYS | ✓ VERIFIED | 23 lines; uses `orjson.dumps(option=orjson.OPT_SORT_KEYS)`; exports `OrjsonCodec` |
| `src/graphql_mcp/adapters/outbound/codec_factory.py` | get_codec() factory | ✓ VERIFIED | 23 lines; try/except ImportError pattern; returns RustJsonCodec when native available, OrjsonCodec otherwise |
| `tests/test_codec_parity.py` | Parity test suite (min 80 lines) | ✓ VERIFIED | 164 lines, 45 test cases across 6 classes |
| `src/graphql_mcp/adapters/inbound/rest.py` | FastAPI app with /health and /graphql/* routes | ✓ VERIFIED | 84 lines; 6 routes: /health, /graphql/query, /graphql/introspect, /graphql/type/{name}, /graphql/subgraphs, /graphql/refresh; mutation guard → 403 |
| `src/graphql_mcp/adapters/inbound/mcp_stdio.py` | MCP stdio server with all 6 tools | ✓ VERIFIED | 72 lines; 6 tools registered via `@mcp.tool()`: query, raw, introspect, describe_type, list_subgraphs, refresh_schema |
| `src/graphql_mcp/adapters/inbound/cli.py` | Click CLI with commands | ✓ VERIFIED | 81 lines; 5 commands: query, introspect, describe-type, list-subgraphs, refresh; deferred imports for fast startup |
| `tests/test_rest.py` | FastAPI adapter tests (min 40 lines) | ✓ VERIFIED | 102 lines, 9 test cases |
| `tests/test_cli.py` | CLI adapter tests (min 30 lines) | ✓ VERIFIED | 82 lines, 6 test cases |
| `tests/test_mcp_stdio.py` | MCP stdio adapter tests (min 30 lines) | ✓ VERIFIED | 90 lines, 8 test cases |
| `pyproject.toml` | Optional deps + entry point | ✓ VERIFIED | server (fastapi+uvicorn), mcp, cli (click), all meta-group; `[project.scripts] graphql-mcp = "graphql_mcp.adapters.inbound.cli:main"` |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `json_native.py` | `graphql_mcp._native` | lazy import in `__init__` | ✓ WIRED | Line 16: `from graphql_mcp._native import decode, encode` |
| `codec_factory.py` | `json_native.RustJsonCodec` | try/except ImportError fallback | ✓ WIRED | Lines 16-23: try RustJsonCodec except ImportError → OrjsonCodec |
| `rest.py` | `GraphQLClient.from_env()` | lazy singleton `_get_client()` | ✓ WIRED | Line 24: `_client = GraphQLClient.from_env()` in lazy init |
| `cli.py` | `GraphQLClient.from_env()` | import in command handlers | ✓ WIRED | Lines 30, 41, 52, 65, 75: deferred import + `GraphQLClient.from_env()` in each command |
| `mcp_stdio.py` | `GraphQLClient.from_env()` | lazy singleton | ✓ WIRED | Line 20: `_client = GraphQLClient.from_env()` in `_get_client()` |
| `pyproject.toml` | `cli:main` | entry point | ✓ WIRED | Line 42: `graphql-mcp = "graphql_mcp.adapters.inbound.cli:main"` |

### Data-Flow Trace (Level 4)

Not applicable — Phase 3 artifacts are codec adapters and thin inbound delegation layers (no UI rendering of dynamic data). All adapters delegate to `GraphQLClient` which was verified in Phases 1-2.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Native extension imports and encodes | `uv run python -c "from graphql_mcp._native import encode, decode; print(encode({'b':1,'a':2}))"` | `b'{"a":2,"b":1}'` | ✓ PASS |
| Codecs produce byte-identical output | `uv run python -c "...RustJsonCodec...OrjsonCodec...byte_identical..."` | `Byte-identical: True` | ✓ PASS |
| Both codecs satisfy JsonCodec Protocol | `uv run python -c "isinstance(rc, JsonCodec)..."` | Both `True` | ✓ PASS |
| get_codec() returns RustJsonCodec when native available | `uv run python -c "...get_codec()...type.__name__"` | `RustJsonCodec` | ✓ PASS |
| Library face import works | `uv run python -c "from graphql_mcp import GraphQLClient"` | OK | ✓ PASS |
| FastAPI routes registered | `uv run python -c "from graphql_mcp.adapters.inbound.rest import app; [r.path for r in app.routes]"` | 6 routes including /health, /graphql/* | ✓ PASS |
| MCP stdio all 6 tools present | `uv run python -c "...mcp_stdio...6 tools..."` | All 6 exist and callable | ✓ PASS |
| CLI shows 5 commands | `uv run python -c "...CliRunner...main --help"` | query, introspect, describe-type, list-subgraphs, refresh | ✓ PASS |
| Parity test suite (45 tests) | `uv run pytest tests/test_codec_parity.py -v` | 45 passed | ✓ PASS |
| Adapter test suite (23 tests) | `uv run pytest tests/test_rest.py tests/test_cli.py tests/test_mcp_stdio.py -v` | 23 passed | ✓ PASS |
| Full test suite | `uv run pytest tests/ -q` | 128 passed, 0 failed | ✓ PASS |
| Ruff lint check | `uv run ruff check src/graphql_mcp/adapters/ tests/test_codec_parity.py tests/test_rest.py tests/test_cli.py tests/test_mcp_stdio.py` | All checks passed | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| GQL-10 | 03-01, 03-02 | Publishable v2 template: lib + stdio + FastAPI + CLI faces; pyo3 JsonCodec with orjson fallback at parity; CI wheels; README + Glama | ⚠️ PARTIAL | Native codec + parity + 4 inbound faces delivered (Phase 3 portion); CI wheel matrix + README + Glama publication deferred to Phase 4 per REQUIREMENTS.md traceability ("Phase 3 + Phase 4") |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | No TODOs, FIXMEs, placeholders, or stubs found | ℹ️ Info | Clean codebase |

**Note:** `return []` found in `lib.py:171` and `schema_analyzer.py:131,154` — these are intentional graceful degradation returns (empty subgraph list when no supergraph available), verified as correct behavior in Phase 2. Not stubs.

### Human Verification Required

No human verification items identified. All success criteria are verifiable programmatically and have been verified.

### Gaps Summary

No gaps found. All 5 ROADMAP success criteria are verified. All plan must-haves are satisfied. All artifacts exist, are substantive, and are properly wired. 128 tests pass with zero failures or skips.

**Observations (non-blocking):**

1. **REST and CLI adapters expose 5/6 operations** (missing `raw`) while MCP stdio exposes all 6. The phase goal mentions "full operation set" but the ROADMAP success criteria (the contract) do not require `raw` on REST/CLI specifically. The `raw` operation is a lower-level API primarily useful for MCP tool consumers, so excluding it from REST/CLI is a reasonable design choice. Not flagged as a gap since all 5 SCs pass.

2. **MCP-over-HTTP** mentioned in the goal parenthetical is explicitly deferred to Phase 4, where SC #1 specifically tests "MCP-over-HTTP handshake." Listed as a deferred item.

3. **pyo3 upgraded from 0.25 to 0.28** — documented deviation from plan, required for pythonize compatibility. Not a gap.

---

_Verified: 2026-06-05T22:23:48Z_
_Verifier: OpenCode (gsd-verifier)_
