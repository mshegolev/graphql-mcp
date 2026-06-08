---
phase: 06-async-transport-perf-benchmarks
plan: 03
subsystem: benchmarks
tags: [perf, benchmark, codec, pytest-benchmark]
dependency_graph:
  requires: []
  provides: [codec-benchmarks, perf-evaluation]
  affects: [pyproject.toml, tests/benchmarks/]
tech_stack:
  added: [pytest-benchmark>=4.0]
  patterns: [pytest-benchmark fixture API, session-scoped fixtures]
key_files:
  created:
    - tests/benchmarks/__init__.py
    - tests/benchmarks/conftest.py
    - tests/benchmarks/test_codec_bench.py
    - .planning/phases/06-async-transport-perf-benchmarks/EVALUATION.md
    - .planning/phases/06-async-transport-perf-benchmarks/evaluation.xml
    - EVALUATION.md
    - evaluation.xml
  modified:
    - pyproject.toml
decisions:
  - "Benchmarks disabled by default via --benchmark-disable in pyproject.toml addopts"
  - "Session-scoped fixtures avoid re-generating large payloads per test"
  - "RustJsonCodec benchmarks auto-skip via pytest.mark.skipif when native extension not built"
  - "Transport round-trip benchmarks deferred — codec is the CPU-bound, reproducible comparison"
metrics:
  duration: 11m 2s
  completed: "2026-06-08T12:49:14Z"
  tasks: 2/2
  files_created: 7
  files_modified: 1
  test_count_before: 164
  test_count_after: 172
---

# Phase 06 Plan 03: Codec Perf Benchmark Suite Summary

pytest-benchmark suite measuring OrjsonCodec and RustJsonCodec encode/decode on 100KB and 1MB payloads, with EVALUATION.md documenting thresholds and evaluation.xml for structured output.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Add pytest-benchmark dependency and create benchmark fixtures | `2ff547d` | pyproject.toml, tests/benchmarks/conftest.py |
| 2 | Create codec benchmark tests and EVALUATION.md | `a93a534` | tests/benchmarks/test_codec_bench.py, EVALUATION.md, evaluation.xml |

## What Was Built

### Benchmark Infrastructure (Task 1)
- Added `pytest-benchmark>=4.0` to dev dependencies in `pyproject.toml`
- Set `addopts = "--benchmark-disable"` so benchmarks don't run by default in `pytest`
- Created `tests/benchmarks/conftest.py` with session-scoped fixtures:
  - `payload_100kb`: ~100KB dict (1,200 nested keys)
  - `payload_1mb`: ~1MB dict (12,000 nested keys)
  - `encoded_100kb` / `encoded_1mb`: pre-encoded bytes for decode benchmarks

### Benchmark Test Suite (Task 2)
- 8 benchmark tests in `tests/benchmarks/test_codec_bench.py`:
  - `TestOrjsonBenchmarks` (4 tests, always available): encode/decode on 100KB and 1MB
  - `TestRustBenchmarks` (4 tests, skipped if native not built): encode/decode on 100KB and 1MB
- Each test uses `benchmark(codec.method, payload)` — pytest-benchmark handles warmup, iteration count, and statistics

### Initial Benchmark Results (macOS arm64, Python 3.10)

| Benchmark | Median | Ops/sec |
|-----------|--------|---------|
| orjson encode 100KB | 156us | 6,163 |
| orjson decode 100KB | 429us | 1,415 |
| orjson encode 1MB | 2.5ms | 395 |
| orjson decode 1MB | 5.9ms | 51 |
| rust encode 100KB | 3.5ms | 287 |
| rust decode 100KB | 1.5ms | 523 |
| rust encode 1MB | 43.5ms | 22 |
| rust decode 1MB | 22.2ms | 29 |

**Key finding**: orjson significantly outperforms Rust native codec due to pyo3 marshalling overhead. orjson operates in C on the Python object directly; the Rust codec pays for Python→Rust→Python conversion. This is documented in EVALUATION.md — the Rust codec is architecturally justified for future hot paths where marshalling cost is amortized.

### Evaluation Documentation (Task 2)
- `EVALUATION.md`: methodology, thresholds, interpretation guide, transport round-trip rationale
- `evaluation.xml`: structured XML evaluation for PERF-03 with benchmark names, thresholds, and artifact references

## Verification Results

1. `pytest --benchmark-enable tests/benchmarks/ -v` — 8/8 benchmarks pass
2. `pytest tests/ -q` — 172 tests pass (164 existing + 8 benchmarks with measurement disabled)
3. All artifacts exist at specified paths
4. `pytest-benchmark>=4.0` present in pyproject.toml dev dependencies

## Decisions Made

1. **Benchmarks disabled by default**: `--benchmark-disable` in pyproject.toml addopts prevents slowing normal test runs. Users enable explicitly with `--benchmark-enable`.
2. **Session-scoped fixtures**: 100KB and 1MB payloads are generated once per session, not per test.
3. **Auto-skip pattern**: Rust benchmarks use `pytest.mark.skipif(not HAS_NATIVE)` matching the existing test_codec_parity.py pattern.
4. **Transport benchmarks deferred**: Codec is the CPU-bound component; transport measures httpx + network, not our code.

## Deviations from Plan

### Auto-added (Rule 2)

**1. [Rule 2 - Missing artifact] EVALUATION.md and evaluation.xml at project root**
- **Found during:** task 2
- **Issue:** Success criteria required EVALUATION.md and evaluation.xml at project root in addition to .planning/ directory
- **Fix:** Created copies at project root for visibility
- **Files created:** EVALUATION.md, evaluation.xml (root)
- **Commit:** `a93a534`

## Known Stubs

None — all benchmarks are fully wired and functional.

## Self-Check: PASSED

- [x] tests/benchmarks/__init__.py exists
- [x] tests/benchmarks/conftest.py exists (45 lines)
- [x] tests/benchmarks/test_codec_bench.py exists (67 lines)
- [x] .planning/phases/06-async-transport-perf-benchmarks/EVALUATION.md exists (56 lines)
- [x] .planning/phases/06-async-transport-perf-benchmarks/evaluation.xml exists (31 lines)
- [x] EVALUATION.md exists at root
- [x] evaluation.xml exists at root
- [x] Commit 2ff547d exists
- [x] Commit a93a534 exists
- [x] 172 tests pass (164 original + 8 benchmarks)
