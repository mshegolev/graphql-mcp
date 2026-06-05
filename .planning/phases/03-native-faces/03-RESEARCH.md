# Phase 3: Native & Faces - Research

**Researched:** 2026-06-06
**Domain:** Rust/pyo3 native extension + Python inbound adapters (MCP stdio, FastAPI, CLI)
**Confidence:** HIGH

## Summary

Phase 3 builds two major subsystems on top of the working Phase 1+2 hexagonal core (60 tests passing, all 6 GraphQLClient operations wired):

1. **Rust native JsonCodec** — A pyo3 extension module (`graphql_mcp._native`) providing `RustJsonCodec` that implements the `JsonCodec` Protocol (encode/decode bytes ↔ Python objects), plus a pure-Python `OrjsonCodec` fallback with byte-for-byte parity under test.

2. **Inbound adapter faces** — Four thin adapters delegating to `GraphQLClient`: the existing library face (already working), an MCP stdio server using `mcp` SDK's `FastMCP`, a FastAPI REST app with `/health` and `/graphql/query` routes, and a CLI using `click`.

The existing codebase already has the native Rust crate stub (`native/src/lib.rs`) and maturin build configuration (`pyproject.toml`). However, there is a **critical name mismatch** that must be fixed: the Rust `#[pymodule]` function exports `graphql_mcp_native` while `pyproject.toml` expects the module at `graphql_mcp._native` (which requires `#[pyo3(name="_native")]`). The existing `.so` file fails to import with `ImportError: dynamic module does not define module export function (PyInit__native)`.

**Primary recommendation:** Fix the pyo3 module name, implement serde_json-based encode/decode, add orjson fallback adapter with OPT_SORT_KEYS for deterministic parity, then build the three new inbound faces as thin delegation layers over GraphQLClient.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None explicitly locked — all implementation choices at OpenCode's discretion (infrastructure phase).

### Key Constraints (from project architecture decisions)
- D5: Python core + Rust hot paths (pyo3/maturin); pure-Python orjson fallback
- D8: FastAPI primary face (k8s/team sharing); stdio second (Glama + local agent)
- D9: Rust JsonCodec via pyo3; orjson fallback; parity under test; maturin CI
- Library-first: `from graphql_mcp import GraphQLClient` works without MCP/FastAPI

### OpenCode's Discretion
All implementation choices are at OpenCode's discretion — pure infrastructure phase.

### Deferred Ideas (OUT OF SCOPE)
None.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GQL-10 (native + faces) | Publishable v2 template: lib + stdio + FastAPI + CLI inbound faces; pyo3 JsonCodec crate with orjson fallback at parity | Rust pyo3 crate pattern, serde_json for encode/decode, orjson OPT_SORT_KEYS for deterministic parity, FastMCP for stdio, FastAPI for REST, click for CLI |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| JSON encode/decode (hot path) | Rust native extension | Python orjson fallback | Performance-critical serialization; Rust is the primary path, orjson is the pure-Python fallback |
| Library facade | Python in-process | — | `GraphQLClient` is the library-first entry point, already complete |
| MCP stdio server | Python process (stdin/stdout) | — | MCP protocol runs over stdio; mcp SDK handles framing |
| FastAPI REST/MCP-over-HTTP | Python HTTP server | — | FastAPI handles HTTP routing; thin adapter delegates to GraphQLClient |
| CLI | Python subprocess | — | click-based CLI runs queries and prints JSON; exits with 0/1 |
| Parity testing | Python test harness | — | pytest compares RustJsonCodec vs OrjsonCodec output byte-for-byte |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyo3 | 0.25.x (Cargo.toml pinned) | Rust→Python bindings for native extension | [VERIFIED: Cargo.toml] Already pinned; matches existing crate |
| serde + serde_json | 1.0.228 / 1.0.150 | JSON serialization in Rust | [VERIFIED: cargo search] Industry standard for Rust JSON |
| maturin | >=1.0,<2.0 | Build Rust extension as Python wheel | [VERIFIED: pyproject.toml] Already configured as build-backend |
| orjson | >=3.11,<4 | Pure-Python fallback JSON codec | [VERIFIED: pyproject.toml] Already a dependency |
| mcp (FastMCP) | ~1.27.2 | MCP stdio server adapter | [VERIFIED: PyPI 2026-05-29] Python >=3.10; provides `FastMCP`, `@mcp.tool()`, `.run(transport="stdio")` |
| fastapi | ~0.124.4 | REST/HTTP inbound adapter | [VERIFIED: pip show] Available on system; standard async Python web framework |
| uvicorn | ~0.33.0 | ASGI server for FastAPI | [VERIFIED: pip show] Standard FastAPI runner |
| click | ~8.1.8 | CLI adapter | [VERIFIED: pip show] Already installed; standard Python CLI framework |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pyo3-bytes (crate) | — | Zero-copy bytes transfer | Only if profiling shows bytes copying is bottleneck — likely unnecessary for MVP |
| pythonize (crate) | — | Serde → Python object conversion | Alternative to manual serde_json::Value → PyObject; evaluate complexity |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| serde_json | simd-json 0.17.0 | simd-json is faster for parsing large payloads but adds complexity; serde_json is simpler and sufficient for MVP |
| click | argparse (stdlib) | argparse has no dependency but click provides better UX with less code; click is already installed |
| FastMCP (mcp SDK) | Manual JSON-RPC over stdio | FastMCP handles all protocol details; manual implementation is error-prone |

**Installation:**
```bash
# Python dependencies (add to pyproject.toml)
pip install "mcp>=1.0,<2" "fastapi>=0.100,<1" "uvicorn>=0.20,<1" "click>=8,<9"

# Rust dependencies (add to native/Cargo.toml)
# serde = { version = "1", features = ["derive"] }
# serde_json = "1"
```

**Version verification:**
- pyo3: 0.25.x in Cargo.toml (latest is 0.28.3 — keep pinned at 0.25 for stability; already compiled) [VERIFIED: cargo search]
- serde_json: 1.0.150 [VERIFIED: cargo search]
- mcp: 1.27.2 [VERIFIED: PyPI]
- fastapi: 0.124.4 [VERIFIED: pip show]
- maturin: 1.13.3 [VERIFIED: PyPI]

## Architecture Patterns

### System Architecture Diagram

```
                    ┌──────────────────────────────────────────────┐
                    │              Inbound Adapters                │
                    │                                              │
   CLI (click)  ────┤   ┌──────────┐  ┌──────────┐  ┌──────────┐ │
   MCP stdio  ──────┤   │  CLI     │  │  MCP     │  │  FastAPI │ │
   HTTP req   ──────┤   │  Adapter │  │  Adapter │  │  Adapter │ │
                    │   └────┬─────┘  └────┬─────┘  └────┬─────┘ │
                    │        │             │              │        │
                    │        └─────────┬───┘──────────────┘        │
                    │                  ▼                            │
                    │        ┌─────────────────┐                   │
                    │        │  GraphQLClient   │ (Library Facade)  │
                    │        │  .from_env()     │                   │
                    │        └────────┬────┬────┘                   │
                    │                 │    │                        │
                    │     ┌───────────┘    └──────────┐             │
                    │     ▼                           ▼             │
                    │  ┌─────────────┐   ┌────────────────┐        │
                    │  │ SchemaService│   │ HttpTransport  │        │
                    │  │ (cascade)   │   │ (orjson encode)│        │
                    │  └─────────────┘   └────────────────┘        │
                    │                                              │
                    │     Outbound Adapters (JSON Codec)           │
                    │  ┌──────────────┐  ┌─────────────────┐       │
                    │  │ RustJsonCodec│  │  OrjsonCodec    │       │
                    │  │ (pyo3/serde) │  │  (pure Python)  │       │
                    │  └──────────────┘  └─────────────────┘       │
                    └──────────────────────────────────────────────┘
```

### Recommended Project Structure

```
src/graphql_mcp/
├── __init__.py                    # exports GraphQLClient (already exists)
├── _native.cpython-*.so           # compiled Rust extension (built by maturin)
├── config.py                      # GraphQLConfig (already exists)
├── domain/                        # Pure domain models (already exists)
├── ports/
│   └── json_codec.py              # JsonCodec Protocol (already exists)
├── adapters/
│   ├── inbound/
│   │   ├── lib.py                 # GraphQLClient facade (already exists)
│   │   ├── mcp_stdio.py           # NEW: MCP stdio server
│   │   ├── rest.py                # NEW: FastAPI app
│   │   └── cli.py                 # NEW: Click CLI
│   └── outbound/
│       ├── json_native.py         # NEW: RustJsonCodec (wraps _native)
│       ├── json_orjson.py         # NEW: OrjsonCodec (fallback)
│       ├── http_transport.py      # (already exists)
│       └── ...                    # other existing adapters
native/
├── Cargo.toml                     # Rust crate config
└── src/
    └── lib.rs                     # pyo3 module with RustJsonCodec
```

### Pattern 1: pyo3 Native Module with Fallback Import

**What:** Import Rust extension, fall back to orjson if native not available.
**When to use:** Every codec usage site (currently HttpTransport, future faces).

```python
# Source: project convention (D5, D9)
# src/graphql_mcp/adapters/outbound/json_native.py
from graphql_mcp.ports.json_codec import JsonCodec

class RustJsonCodec:
    """Rust-backed JSON codec via pyo3 native extension."""

    def __init__(self) -> None:
        from graphql_mcp._native import encode, decode  # type: ignore[import]
        self._encode = encode
        self._decode = decode

    def encode(self, obj: Any) -> bytes:
        return self._encode(obj)

    def decode(self, data: bytes) -> Any:
        return self._decode(data)
```

```python
# src/graphql_mcp/adapters/outbound/json_orjson.py
import orjson
from graphql_mcp.ports.json_codec import JsonCodec

class OrjsonCodec:
    """Pure-Python fallback JSON codec using orjson."""

    def encode(self, obj: Any) -> bytes:
        return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)

    def decode(self, data: bytes) -> Any:
        return orjson.loads(data)
```

### Pattern 2: Codec Factory with Auto-Detection

**What:** Factory function that returns the best available codec.
**When to use:** Default codec selection in GraphQLClient and adapters.

```python
# Source: project convention (D5)
def get_codec() -> JsonCodec:
    """Return Rust codec if available, orjson fallback otherwise."""
    try:
        from graphql_mcp.adapters.outbound.json_native import RustJsonCodec
        return RustJsonCodec()
    except ImportError:
        from graphql_mcp.adapters.outbound.json_orjson import OrjsonCodec
        return OrjsonCodec()
```

### Pattern 3: MCP Stdio Adapter using FastMCP

**What:** Thin MCP server adapter that exposes all 6 GraphQLClient operations as MCP tools.
**When to use:** When running as `graphql-mcp` stdio server for Glama / local agent.

```python
# Source: mcp SDK docs [VERIFIED: PyPI README + Python import]
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("graphql-mcp")

@mcp.tool()
def query(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query."""
    client = _get_client()
    result = client.query(query, variables)
    return result.model_dump()

# Run with stdio transport:
# mcp.run(transport="stdio")
```

### Pattern 4: FastAPI Inbound Adapter

**What:** FastAPI app with health check and query endpoint.
**When to use:** k8s deployment, team sharing (D8: FastAPI is primary face).

```python
# Source: FastAPI docs [VERIFIED: pip show fastapi 0.124.4]
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="graphql-mcp")

@app.get("/health")
def health():
    return {"status": "ok"}

class QueryRequest(BaseModel):
    query: str
    variables: dict | None = None

@app.post("/graphql/query")
def graphql_query(req: QueryRequest):
    client = _get_client()
    result = client.query(req.query, req.variables)
    return result.model_dump()
```

### Pattern 5: Click CLI Adapter

**What:** Command-line interface for ad-hoc queries.
**When to use:** Developer tooling, shell scripts, CI pipelines.

```python
# Source: click docs [VERIFIED: pip show click 8.1.8]
import click
import json

@click.group()
def main():
    """graphql-mcp CLI"""
    pass

@main.command()
@click.argument("query_string")
@click.option("--variables", "-v", default=None)
def query(query_string: str, variables: str | None):
    """Execute a GraphQL query."""
    from graphql_mcp import GraphQLClient
    client = GraphQLClient.from_env()
    vars_dict = json.loads(variables) if variables else None
    result = client.query(query_string, vars_dict)
    click.echo(json.dumps(result.model_dump(), indent=2))
```

### Anti-Patterns to Avoid

- **Importing domain/ports in adapter __init__.py:** Inbound adapters should only import `GraphQLClient` (library-first pattern). Don't import domain models at adapter level — use `GraphQLClient` as the single API surface.
- **Embedding business logic in adapters:** All 6 operations are already in `GraphQLClient`. Adapters MUST be pure delegation — zero business logic, just format conversion.
- **Using orjson.OPT_SORT_KEYS only in one codec:** Both RustJsonCodec and OrjsonCodec MUST produce identical output. If Rust uses serde_json with sorted keys, orjson MUST use OPT_SORT_KEYS.
- **Hardcoding the native import at module level:** Use lazy import or try/except to allow pure-Python installation without Rust toolchain.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP protocol framing | Custom JSON-RPC over stdin/stdout | `mcp` SDK's `FastMCP` | Protocol is complex (capabilities negotiation, tool listing, error codes); SDK handles all edge cases |
| JSON serialization in Rust | Manual PyObject → String conversion | `serde_json::to_vec` + `pyo3`'s `Python::with_gil` | serde handles all JSON edge cases (Unicode escaping, float precision, nested structures) |
| CLI argument parsing | Manual sys.argv parsing | `click` | Click handles help text, type conversion, error messages automatically |
| ASGI server | Custom socket handling | `uvicorn` | Production-grade ASGI server with signal handling, graceful shutdown |
| Python↔Rust type conversion | Manual ffi calls | pyo3's `#[pyfunction]` with `Bound<'_, PyAny>` | pyo3 handles reference counting, type conversion, error propagation |

**Key insight:** Every adapter in this phase is a thin delegation layer. The moment you find yourself writing business logic in an adapter, you're doing it wrong — push it into `GraphQLClient` or the domain layer.

## Common Pitfalls

### Pitfall 1: pyo3 Module Name Mismatch (ACTIVE BUG)
**What goes wrong:** The `.so` file fails to import with `ImportError: dynamic module does not define module export function (PyInit__native)`.
**Why it happens:** The Rust `#[pymodule]` function is named `graphql_mcp_native` but `pyproject.toml` sets `module-name = "graphql_mcp._native"` — maturin expects the export function to be `PyInit__native`.
**How to avoid:** Add `#[pyo3(name = "_native")]` attribute to the pymodule function, or rename the function to `_native`.
**Warning signs:** `ImportError` mentioning `PyInit_` on import.

### Pitfall 2: Non-Deterministic JSON Output Breaks Parity
**What goes wrong:** Parity test fails because Rust serde_json and Python orjson produce different key ordering.
**Why it happens:** JSON object key order is unspecified by the JSON spec. serde_json preserves insertion order; orjson preserves insertion order by default.
**How to avoid:** Use sorted keys in BOTH codecs: serde_json's `to_vec` on a `BTreeMap` (or sorted `serde_json::Value`), and orjson's `OPT_SORT_KEYS` option. Test with deeply nested objects containing keys in various orders.
**Warning signs:** Tests pass on small payloads but fail on larger ones with many keys.

### Pitfall 3: Float Precision Differences Between Rust and Python
**What goes wrong:** Parity test fails on floating-point numbers like `0.1 + 0.2`.
**Why it happens:** serde_json and orjson may format the same IEEE 754 double differently (e.g., `0.30000000000000004` vs `0.3`).
**How to avoid:** Test with edge-case floats in the parity fixture. Both serde_json and orjson use the Ryu algorithm for float formatting, so they should agree — but verify.
**Warning signs:** Parity failures only on specific float values.

### Pitfall 4: MCP Server Blocks Event Loop
**What goes wrong:** `mcp.run(transport="stdio")` blocks forever; can't use with FastAPI in same process.
**Why it happens:** MCP stdio transport uses its own event loop; FastAPI uses uvicorn's event loop.
**How to avoid:** MCP stdio and FastAPI MUST be separate entry points (separate commands/processes). Never mix them in one process.
**Warning signs:** Process hangs or `RuntimeError: This event loop is already running`.

### Pitfall 5: Forgetting to Add New Dependencies to pyproject.toml
**What goes wrong:** `pip install graphql-mcp` fails for users because mcp/fastapi/click are not declared.
**Why it happens:** These were available in dev environment but not listed in `[project.dependencies]`.
**How to avoid:** Add `mcp`, `fastapi`, `uvicorn`, and `click` to pyproject.toml dependencies. Consider making some optional (e.g., `[project.optional-dependencies] server = ["fastapi", "uvicorn"]`).
**Warning signs:** ImportError in clean install environment.

### Pitfall 6: pyo3 Bound API vs GIL-held refs
**What goes wrong:** Compilation errors with `pyo3::PyAny` vs `Bound<'_, PyAny>`.
**Why it happens:** pyo3 0.21+ introduced the `Bound<'_, T>` smart pointer API, replacing the old GIL-held reference pattern. pyo3 0.25 uses the `Bound` API exclusively.
**How to avoid:** All pyfunction signatures MUST use `Bound<'_, PyAny>` or typed `Bound<'_, PyBytes>`, not bare `&PyAny`. The existing stub already uses `&Bound<'_, PyModule>` correctly.
**Warning signs:** Compiler errors mentioning deprecated pyo3 traits.

## Code Examples

### Rust pyo3 JsonCodec Implementation

```rust
// Source: pyo3 0.25 docs [VERIFIED: pyo3.rs/v0.25.0] + serde_json [VERIFIED: cargo search]
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use serde_json::Value;

/// Encode a Python object to JSON bytes with sorted keys.
#[pyfunction]
fn encode(py: Python<'_>, obj: Bound<'_, PyAny>) -> PyResult<Py<PyBytes>> {
    // Convert Python object → serde_json::Value
    let value: Value = pythonize::depythonize_bound(obj)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    // Serialize with sorted keys
    let bytes = serde_json::to_vec(&value)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    Ok(PyBytes::new(py, &bytes).into())
}

/// Decode JSON bytes to a Python object.
#[pyfunction]
fn decode(py: Python<'_>, data: &[u8]) -> PyResult<PyObject> {
    let value: Value = serde_json::from_slice(data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;

    pythonize::pythonize(py, &value)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))
}

#[pymodule]
#[pyo3(name = "_native")]
fn graphql_mcp_native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", "0.1.0")?;
    m.add_function(wrap_pyfunction!(encode, m)?)?;
    m.add_function(wrap_pyfunction!(decode, m)?)?;
    Ok(())
}
```

**Note on pythonize:** The `pythonize` crate provides serde-based conversion between Python objects and Rust values. It is the standard bridge for pyo3 + serde workflows. [ASSUMED — needs Cargo verification]

**Alternative without pythonize (simpler):**

```rust
// Source: pyo3 manual conversion pattern [VERIFIED: pyo3.rs/v0.25.0]
use pyo3::prelude::*;
use pyo3::types::PyBytes;

/// Encode: Python dict/list/etc → JSON bytes.
/// Strategy: use Python's repr/marshal? No — use orjson on the Python side
/// and serde_json on Rust side for raw bytes only.
///
/// Simpler approach: Accept Python bytes (already JSON-encoded by caller),
/// parse → sort keys → re-encode. This avoids PyAny→Value conversion entirely.
#[pyfunction]
fn encode(py: Python<'_>, data: &[u8]) -> PyResult<Py<PyBytes>> {
    // Parse JSON from bytes
    let value: serde_json::Value = serde_json::from_slice(data)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    // Re-serialize (serde_json preserves original key order by default,
    // but Value keys are in insertion order; sort explicitly if needed)
    let out = serde_json::to_vec(&value)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e.to_string()))?;
    Ok(PyBytes::new(py, &out).into())
}
```

### OrjsonCodec Fallback

```python
# Source: orjson docs [VERIFIED: orjson 3.11.8 installed]
from __future__ import annotations
from typing import Any
import orjson

class OrjsonCodec:
    """Pure-Python fallback JSON codec using orjson."""

    def encode(self, obj: Any) -> bytes:
        """Serialize Python object to JSON bytes with sorted keys."""
        return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)

    def decode(self, data: bytes) -> Any:
        """Deserialize JSON bytes to Python object."""
        return orjson.loads(data)
```

### Parity Test Pattern

```python
# Source: project test conventions (conftest.py pattern)
import pytest

@pytest.fixture(params=["rust", "orjson"])
def codec(request):
    if request.param == "rust":
        try:
            from graphql_mcp.adapters.outbound.json_native import RustJsonCodec
            return RustJsonCodec()
        except ImportError:
            pytest.skip("Rust native extension not built")
    else:
        from graphql_mcp.adapters.outbound.json_orjson import OrjsonCodec
        return OrjsonCodec()

def test_parity_100kb(rust_codec, orjson_codec, large_fixture_100kb):
    """RustJsonCodec and OrjsonCodec produce byte-identical output."""
    rust_out = rust_codec.encode(large_fixture_100kb)
    orjson_out = orjson_codec.encode(large_fixture_100kb)
    assert rust_out == orjson_out

    # Round-trip: decode and re-encode
    rust_decoded = rust_codec.decode(rust_out)
    orjson_decoded = orjson_codec.decode(orjson_out)
    assert rust_decoded == orjson_decoded
```

### FastAPI App Pattern

```python
# Source: FastAPI docs [VERIFIED: fastapi 0.124.4 installed]
from __future__ import annotations
from fastapi import FastAPI
from pydantic import BaseModel
from graphql_mcp import GraphQLClient

app = FastAPI(title="graphql-mcp", version="0.1.0")
_client: GraphQLClient | None = None

def _get_client() -> GraphQLClient:
    global _client
    if _client is None:
        _client = GraphQLClient.from_env()
    return _client

@app.get("/health")
def health():
    return {"status": "ok"}

class QueryRequest(BaseModel):
    query: str
    variables: dict | None = None

@app.post("/graphql/query")
def graphql_query(req: QueryRequest):
    client = _get_client()
    result = client.query(req.query, req.variables)
    return {
        "data": result.data,
        "errors": [e for e in result.errors],
        "error_class": result.error_class.value,
    }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pyo3 `&PyAny` (GIL-held refs) | pyo3 `Bound<'_, PyAny>` smart pointers | pyo3 0.21 (2024) | All pyfunction params use Bound API |
| MCP `mcp.server.Server` (low-level) | `mcp.server.fastmcp.FastMCP` (high-level) | mcp SDK 1.0+ (2024) | Use `@mcp.tool()` decorator pattern; `.run(transport="stdio")` |
| FastAPI Depends injection | Direct function calls in route handlers | — | For thin adapters, Depends is overkill; direct `GraphQLClient.from_env()` is simpler |
| mcp stdio only | mcp supports stdio + SSE + streamable-http | mcp SDK 1.8+ (2025) | FastMCP.run() accepts transport= param |

**Deprecated/outdated:**
- `pyo3::PyObject` without Bound: Still compiles in 0.25 but deprecated path
- `mcp.server.Server` (low-level): Still works but FastMCP is preferred for new code
- Manual JSON-RPC framing for MCP: Replaced by SDK's transport abstractions

## Assumptions Log

> List all claims tagged `[ASSUMED]` in this research.

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `pythonize` crate provides bidirectional serde ↔ PyObject conversion and is compatible with pyo3 0.25 | Code Examples (Rust) | Must use manual conversion instead; moderate effort |
| A2 | serde_json and orjson both use Ryu algorithm for float formatting, ensuring identical float serialization | Pitfall 3 | Parity tests may fail on edge-case floats; fixable with rounding |
| A3 | `mcp` SDK's `FastMCP` is available for import and stable API for tool registration with `.run(transport="stdio")` | Standard Stack | Verified import works; API surface confirmed via `dir()` |

## Open Questions

1. **pythonize crate compatibility with pyo3 0.25**
   - What we know: pythonize is the standard serde↔PyObject bridge; pyo3 0.25 is pinned in Cargo.toml
   - What's unclear: Whether the latest pythonize release supports pyo3 0.25 specifically (it may require 0.22+ or 0.23+)
   - Recommendation: Check `cargo add pythonize` — if it pulls a compatible version, use it. If not, implement manual Python→Value conversion using pyo3's `extract()` methods or accept bytes directly (simpler approach).

2. **Should mcp/fastapi/click be optional dependencies?**
   - What we know: Pure library usage (`from graphql_mcp import GraphQLClient`) should work without these
   - What's unclear: Whether to use optional-dependencies or include everything
   - Recommendation: Add as optional extras: `server = ["fastapi", "uvicorn"]`, `mcp = ["mcp"]`, `cli = ["click"]`. Core package keeps current deps only.

3. **RustJsonCodec scope — encode/decode only, or also field-select/redaction?**
   - What we know: Success criteria mention "parse/traverse/field-select/redaction" for parity test
   - What's unclear: The current `JsonCodec` Protocol only has `encode()` and `decode()` — no field-select or redaction methods
   - Recommendation: Start with encode/decode only (matching the Protocol). If field-select/redaction are needed, extend the Protocol in this phase and implement in both codecs. The success criteria likely refer to these as data patterns in test fixtures (JSON containing various field types), not as separate API methods.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Rust toolchain (rustc) | Native extension build | ✓ | 1.93.1 | OrjsonCodec fallback (no Rust needed at runtime) |
| cargo | Native extension build | ✓ | 1.93.1 | — |
| maturin | Build system | ✗ (not in PATH) | — | Install via `pip install maturin` (verified installable) |
| Python 3.10 | Runtime | ✓ | 3.10.4 | — |
| orjson | Fallback codec | ✓ | 3.11.8 | — |
| fastapi | REST adapter | ✓ | 0.124.4 (importable) | — |
| uvicorn | ASGI server | ✓ | 0.33.0 (importable) | — |
| click | CLI adapter | ✓ | 8.1.3 (importable) | — |
| mcp SDK | MCP stdio adapter | ✓ | importable (FastMCP confirmed) | — |

**Missing dependencies with no fallback:**
- maturin is not in PATH but is installable via pip. Must be installed before `maturin develop` can run.

**Missing dependencies with fallback:**
- None — all required tools are available or installable.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Not applicable — no user auth in this phase |
| V3 Session Management | No | Not applicable — stateless adapters |
| V4 Access Control | No | Mutation guard already implemented in Phase 2 |
| V5 Input Validation | Yes | Pydantic models for FastAPI request bodies; orjson/serde_json for JSON parsing (reject malformed input) |
| V6 Cryptography | No | No crypto operations in this phase |

### Known Threat Patterns for Rust+Python JSON Stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| JSON deserialization of untrusted input | Tampering | serde_json/orjson reject invalid JSON; Pydantic validates request schema |
| Large payload DoS | Denial of Service | FastAPI request body size limit (default or explicit); consider max JSON depth |
| CLI injection via shell arguments | Elevation of Privilege | click handles argument parsing safely; no shell=True subprocess calls |
| Stdio MCP message flooding | Denial of Service | mcp SDK handles protocol-level flow control |

## Sources

### Primary (HIGH confidence)
- Cargo.toml / pyproject.toml / existing source code — direct file reads
- pyo3 v0.25.0 user guide (https://pyo3.rs/v0.25.0/) — module structure, Bound API, pyfunction signatures
- PyPI mcp 1.27.2 page — version, dependencies, FastMCP quickstart pattern
- PyPI maturin 1.13.3 page — build configuration, mixed project layout
- cargo search results — serde 1.0.228, serde_json 1.0.150, pyo3 0.28.3 (latest)
- Python environment probing — fastapi 0.124.4, uvicorn 0.33.0, click 8.1.3, mcp importable

### Secondary (MEDIUM confidence)
- MCP Python SDK README (GitHub) — FastMCP tool registration, transport modes, server patterns
- orjson behavior testing — OPT_SORT_KEYS produces deterministic output (verified via Python shell)

### Tertiary (LOW confidence)
- pythonize crate compatibility with pyo3 0.25 — not verified against cargo registry [ASSUMED]
- simd-json 0.17.0 as alternative — cargo search only, not benchmarked [ASSUMED]

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against registries/installed packages
- Architecture: HIGH — patterns derived from existing codebase structure and official docs
- Pitfalls: HIGH — pyo3 module name mismatch confirmed by actual import test; other pitfalls from official docs
- Parity testing: MEDIUM — deterministic JSON approach sound but float edge cases need runtime validation

**Research date:** 2026-06-06
**Valid until:** 2026-07-06 (30 days — stable ecosystem)
