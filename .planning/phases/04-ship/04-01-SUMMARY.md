---
phase: 04-ship
plan: 01
subsystem: domain, ports
tags: [lint, ruff, type-checking, compliance]
dependency_graph:
  requires: [03-02-PLAN]
  provides: [ruff-clean-codebase, green-test-suite]
  affects: [04-02-PLAN]
tech_stack:
  added: []
  patterns: [TYPE_CHECKING-guard, from-future-annotations]
key_files:
  created: []
  modified:
    - src/graphql_mcp/domain/schema_service.py
    - src/graphql_mcp/ports/schema_source.py
    - src/graphql_mcp/ports/transport.py
decisions:
  - "TC003 Sequence also needs TYPE_CHECKING guard — collections.abc.Sequence is annotation-only in schema_service.py"
metrics:
  duration: 89s
  completed: "2026-06-05T22:36:10Z"
---

# Phase 4 Plan 1: Fix Ruff Violations + Verify Test Suite Summary

**One-liner:** Resolved all 5 ruff violations (4×TC001 + 1×UP035, plus 1 emergent TC003) via TYPE_CHECKING guards and collections.abc migration; 128 tests pass green.

## What Was Done

### Task 1: Fix ruff TC001 + UP035 violations across ports and domain ✅
**Commit:** `6cf2190`

Fixed 6 total ruff violations across 3 files (5 original + 1 emergent TC003):

1. **`src/graphql_mcp/domain/schema_service.py`** (3 violations fixed):
   - UP035: Changed `from typing import Sequence` → `from collections.abc import Sequence`
   - TC003: Moved `collections.abc.Sequence` into `TYPE_CHECKING` block (emergent — ruff flagged stdlib import too)
   - TC001: Moved `SchemaGraph` and `SchemaSource` imports into `TYPE_CHECKING` block
   - Added `from typing import TYPE_CHECKING`

2. **`src/graphql_mcp/ports/schema_source.py`** (1 violation fixed):
   - TC001: Moved `SchemaGraph` import into `TYPE_CHECKING` block
   - Added `TYPE_CHECKING` to existing typing import

3. **`src/graphql_mcp/ports/transport.py`** (1 violation fixed):
   - TC001: Moved `QueryResult` import into `TYPE_CHECKING` block
   - Added `TYPE_CHECKING` to existing typing import

**Key insight:** The `TYPE_CHECKING` pattern is safe for `runtime_checkable Protocol` classes because `from __future__ import annotations` is active in all files — annotations are strings at runtime, and `isinstance()` checks use structural subtyping which doesn't need the actual type objects.

### Task 2: Verify full test suite passes green with zero skips ✅
**Commit:** N/A (verification-only task, no files changed)

- All 128 tests pass green in 0.72s
- Zero skips, zero failures
- No broken imports from TYPE_CHECKING refactoring
- Tests cover: error paths, mutation guard, cascade, federation, parity, FastAPI routes, MCP tools, CLI, domain purity

## Verification Results

| Check | Result |
|-------|--------|
| `ruff check src/ tests/` | ✅ All checks passed (0 violations) |
| `pytest tests/ -v` | ✅ 128 passed in 0.72s |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed emergent TC003 violation for Sequence import**
- **Found during:** Task 1
- **Issue:** After fixing UP035 (`typing.Sequence` → `collections.abc.Sequence`), ruff flagged the new `collections.abc.Sequence` import as TC003 (stdlib import used only in annotations should be in TYPE_CHECKING block)
- **Fix:** Moved `from collections.abc import Sequence` inside the `if TYPE_CHECKING:` block
- **Files modified:** `src/graphql_mcp/domain/schema_service.py`
- **Commit:** `6cf2190` (same commit as the other fixes)

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| TC003 Sequence also needs TYPE_CHECKING guard | `Sequence` is only used in type annotations; `from __future__ import annotations` makes it annotation-only at runtime |

## Self-Check: PASSED

All files verified present. Commit `6cf2190` confirmed in git log.
