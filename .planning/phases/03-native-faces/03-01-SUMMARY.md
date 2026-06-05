---
phase: 03-native-faces
plan: 01
subsystem: native-codec
tags: [pyo3, rust, json, codec, orjson, serde, parity]
dependency_graph:
  requires: [json_codec_port]
  provides: [rust_json_codec, orjson_codec, codec_factory]
  affects: [graphql_mcp._native, adapters.outbound]
tech_stack:
  added: [pyo3-0.28, pythonize-0.28, serde_json-1, serde-1]
  patterns: [codec-adapter, factory-pattern, protocol-conformance, lazy-import]
key_files:
  created:
    - src/graphql_mcp/adapters/outbound/json_native.py
    - src/graphql_mcp/adapters/outbound/json_orjson.py
    - src/graphql_mcp/adapters/outbound/codec_factory.py
    - tests/test_codec_parity.py
  modified:
    - native/Cargo.toml
    - native/src/lib.rs
    - .gitignore
decisions:
  - "Upgraded pyo3 from 0.25 to 0.28 to match pythonize 0.28 compatibility"
  - "Used pythonize crate for direct Python<->serde_json conversion (not bytes-in/bytes-out fallback)"
  - "Rust encode returns Py<PyBytes> for zero-copy; Python wrapper calls bytes() for immutability"
  - "TYPE_CHECKING block for JsonCodec import in codec_factory to satisfy ruff TCH rule"
metrics:
  duration: "11m"
  completed: "2026-06-05"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 45
  files_changed: 7
---

# Phase 3 Plan 1: Rust pyo3 JsonCodec + OrjsonCodec Fallback + Parity Tests Summary

Rust native JSON codec via pyo3/serde_json with recursive key sorting, OrjsonCodec fallback with OPT_SORT_KEYS, and comprehensive 45-test parity suite verifying byte-identical output across both implementations including 1MB+ payloads.

## What Was Built

### Rust Native Extension (`native/src/lib.rs`)
- Full rewrite from stub to working codec with `encode` and `decode` functions
- `encode`: accepts Python object via pythonize `depythonize`, recursively sorts serde_json `Value` keys, serializes to bytes
- `decode`: parses JSON bytes via serde_json, converts back to Python object via pythonize `pythonize`
- Module correctly named `_native` via `#[pyo3(name = "_native")]` matching maturin config
- All errors map to Python `ValueError` with descriptive messages (T-03-01 mitigation)

### Python Adapters
- **RustJsonCodec** (`json_native.py`): Lazy-imports `_native` extension in `__init__`, wraps encode/decode
- **OrjsonCodec** (`json_orjson.py`): Uses `orjson.dumps(option=OPT_SORT_KEYS)` for deterministic sorted output
- **get_codec()** (`codec_factory.py`): try/except ImportError pattern — returns RustJsonCodec when native available, OrjsonCodec otherwise

### Parity Test Suite (`tests/test_codec_parity.py`)
- 164 lines, 45 test cases across 6 test classes
- Protocol conformance (isinstance checks for both codecs)
- 16 parametrized parity cases: simple types, nested dicts, GraphQL response shapes, unicode, escape chars
- Cross-codec roundtrip: encode with one, decode with the other
- Large payload parity: 100KB+ (1200 keys) and 1MB+ (12000 keys)
- Float precision: 7 edge cases (0.1, 1e-7, -0.0, etc.)
- Factory auto-detection tests
- Graceful skip when native extension not built (`pytest.skip`)

## Verification Results

| Check | Result |
|-------|--------|
| `maturin build --release` | ✅ Compiled successfully (pyo3 0.28 + pythonize 0.28) |
| `from graphql_mcp._native import encode, decode` | ✅ Imports OK |
| `RustJsonCodec.encode({'b':1,'a':2})` → `b'{"a":2,"b":1}'` | ✅ Sorted keys |
| `OrjsonCodec.encode({'b':1,'a':2})` → `b'{"a":2,"b":1}'` | ✅ Sorted keys |
| `isinstance(codec, JsonCodec)` for both | ✅ Protocol conformant |
| `get_codec()` returns `RustJsonCodec` | ✅ Native detected |
| Parity tests (45/45) | ✅ All pass |
| Existing tests (60/60) | ✅ No regressions |
| `ruff check` on new files | ✅ All passed |
| Total test suite: 105 tests | ✅ All pass |

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Upgraded pyo3 0.25 → 0.28 | pythonize 0.28 (latest) requires pyo3 0.28; no compatible pythonize for pyo3 0.25 |
| pythonize for Python↔serde conversion | Direct object conversion avoids double-serialization overhead; maintains type fidelity |
| `Py<PyBytes>` return + `bytes()` wrapper | pyo3 0.28 returns `Bound<'_, PyAny>` from pythonize; `.unbind()` converts to owned |
| TYPE_CHECKING for codec_factory imports | Satisfies ruff TCH001; `JsonCodec` only needed for return type annotation |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed .gitignore missing Cargo.lock entry**
- **Found during:** Task 1
- **Issue:** Phase 1 decision stated "Cargo.lock must not be tracked" but Cargo.lock was not in .gitignore
- **Fix:** Added `Cargo.lock` to .gitignore
- **Files modified:** .gitignore
- **Commit:** e26af9c

**2. [Rule 3 - Blocking] pyo3 version upgrade 0.25 → 0.28**
- **Found during:** Task 1
- **Issue:** No compatible pythonize crate for pyo3 0.25; latest pythonize 0.28 requires pyo3 0.28
- **Fix:** Upgraded pyo3 dependency to 0.28, added pythonize 0.28
- **Files modified:** native/Cargo.toml
- **Commit:** e26af9c

**3. [Rule 1 - Bug] Fixed pyo3 0.28 API differences**
- **Found during:** Task 1 build
- **Issue:** pyo3 0.28 removed `PyObject` type alias (use `Py<PyAny>`); `pythonize()` returns `Bound<'_, PyAny>` not `Py<PyAny>`
- **Fix:** Changed return type to `Py<PyAny>`, added `.unbind()` call
- **Files modified:** native/src/lib.rs
- **Commit:** e26af9c

**4. [Rule 1 - Bug] Fixed large payload test size thresholds**
- **Found during:** Task 2 test run
- **Issue:** Original plan's payload generators (500/5000 keys) produced ~44KB/~469KB, below the 50KB/500KB thresholds
- **Fix:** Increased to 1200/12000 keys for 100KB+/1MB+ actual sizes
- **Files modified:** tests/test_codec_parity.py
- **Commit:** 8a8b860

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 | e26af9c | feat(03-01): implement Rust pyo3 JsonCodec + OrjsonCodec fallback + codec factory |
| 2 | 8a8b860 | test(03-01): add comprehensive parity test suite for RustJsonCodec vs OrjsonCodec |

## Self-Check: PASSED

All 7 files verified present. Both commits (e26af9c, 8a8b860) verified in git log. 105 tests passing.
