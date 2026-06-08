---
phase: 05-tech-debt-error-hardening
plan: 01
subsystem: transport
tags: [codec, tech-debt, hexagonal, dependency-inversion]
dependency_graph:
  requires: [codec_factory, json_codec_port, orjson_codec]
  provides: [codec_abstracted_transport]
  affects: [http_transport]
tech_stack:
  added: []
  patterns: [dependency-injection, port-adapter-wiring, spy-testing]
key_files:
  created:
    - tests/test_http_transport_codec.py
  modified:
    - src/graphql_mcp/adapters/outbound/http_transport.py
decisions:
  - "Catch ValueError|TypeError instead of orjson.JSONDecodeError — codec-agnostic error handling"
  - "Codec injected as last __init__ param with None default — backward-compatible, testable"
metrics:
  duration_seconds: 432
  completed: "2026-06-08T11:47:23Z"
  tasks_completed: 2
  tasks_total: 2
  tests_added: 5
  tests_total: 133
---

# Phase 05 Plan 01: Wire JsonCodec into HttpTransport Summary

**One-liner:** Replaced direct `orjson.dumps()`/`orjson.loads()` in HttpTransport with `self._codec.encode()`/`self._codec.decode()` via `get_codec()` factory, closing v1.0 tech debt item #1.

## What Was Done

### Task 1: Wire codec into HttpTransport constructor and methods (b395b5e)

Modified `src/graphql_mcp/adapters/outbound/http_transport.py`:

1. **Replaced `import orjson`** with `from graphql_mcp.adapters.outbound.codec_factory import get_codec` — transport no longer has a direct dependency on orjson.
2. **Added `codec: JsonCodec | None = None` parameter** to `__init__` as the last parameter — backward-compatible with all existing call sites.
3. **Added `self._codec = codec or get_codec()`** — defaults to factory-selected codec (Rust native when available, orjson fallback otherwise). Supports dependency injection for testing.
4. **Replaced `orjson.dumps(body)`** with `self._codec.encode(body)` in `post_raw()`.
5. **Replaced `orjson.loads(response.content)`** with `self._codec.decode(response.content)` in `post_raw()`.
6. **Changed exception handling** from `(orjson.JSONDecodeError, ValueError)` to `(ValueError, TypeError)` — codec-agnostic since `orjson.JSONDecodeError` is a `ValueError` subclass.

Net change: +11 lines, -5 lines. Zero `orjson` references remain in the file.

### Task 2: Add tests proving codec wiring and regression-free (af1b59f)

Created `tests/test_http_transport_codec.py` with 5 tests:

| Test | Purpose |
|------|---------|
| `test_execute_uses_codec_encode_and_decode` | SpyCodec confirms encode/decode delegation during execute() |
| `test_post_raw_uses_codec` | SpyCodec confirms codec usage in post_raw() path |
| `test_default_codec_from_factory` | Verifies `transport._codec` satisfies `JsonCodec` protocol |
| `test_codec_decode_error_returns_transport_error` | MagicMock codec raising ValueError → TRANSPORT error result |
| `test_no_orjson_in_module_dict` | Source-level assertion that no `import orjson` / `orjson.dumps` / `orjson.loads` exist |

**Full suite result:** 133 tests passed (128 existing + 5 new), zero failures, zero regressions.

## Verification Results

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| `grep -c 'orjson' http_transport.py` | 0 | 0 | PASS |
| `grep -c 'self._codec' http_transport.py` | 3 | 3 | PASS |
| `grep -c 'get_codec' http_transport.py` | ≥1 | 2 | PASS |
| New tests pass | 5/5 | 5/5 | PASS |
| Full suite | 128+ pass | 133 pass | PASS |

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

1. **Catch `ValueError | TypeError` instead of `orjson.JSONDecodeError`** — Since the transport no longer imports orjson, it can't reference `orjson.JSONDecodeError`. Both `orjson.JSONDecodeError` (subclass of `ValueError`) and stdlib `json.JSONDecodeError` (subclass of `ValueError`) are caught by `ValueError`. `TypeError` covers edge cases like `None` input to decode.

2. **Codec as last `__init__` parameter with `None` default** — This preserves backward compatibility with all 128 existing tests and call sites (none pass `codec=`), while enabling dependency injection for new test code.

## Commits

| Hash | Type | Description |
|------|------|-------------|
| b395b5e | refactor | Wire JsonCodec into HttpTransport via get_codec() factory |
| af1b59f | test | Prove HttpTransport codec wiring with spy-based tests |

## Self-Check: PASSED

- [x] `tests/test_http_transport_codec.py` — FOUND
- [x] `05-01-SUMMARY.md` — FOUND
- [x] `src/graphql_mcp/adapters/outbound/http_transport.py` — FOUND
- [x] Commit b395b5e — FOUND
- [x] Commit af1b59f — FOUND
