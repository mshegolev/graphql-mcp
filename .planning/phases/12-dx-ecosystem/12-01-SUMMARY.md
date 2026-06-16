---
phase: "12"
plan: "01"
subsystem: dx-ecosystem
tags: [ci-cd, pypi, oidc, examples, github-actions]
dependency_graph:
  requires: []
  provides: [pypi-publish-workflow, sdk-examples]
  affects: [.github/workflows/publish.yml, examples/]
tech_stack:
  added: [pypa/gh-action-pypi-publish, cibuildwheel]
  patterns: [oidc-trusted-publishing, github-environments]
key_files:
  created:
    - .github/workflows/publish.yml
    - examples/basic_query.py
    - examples/async_query.py
    - examples/subscription.py
  modified: []
decisions:
  - "OIDC Trusted Publishing over API tokens — no secrets to rotate, GitHub identity verified by PyPI"
  - "Wheel matrix matches ci.yml exactly — Linux/macOS/Windows, py3.10-3.12"
  - "skip-existing flag for idempotent republishing — safe to re-run failed publish"
  - "pypi environment in GitHub — manual approval gate before publishing"
metrics:
  duration: "5m"
  completed: "2026-06-16"
---

# Phase 12 Plan 01: GitHub Actions Publish Workflow & SDK Examples Summary

**One-liner:** PyPI OIDC Trusted Publishing on v* tags with cibuildwheel matrix plus 3 runnable SDK examples (sync, async, subscription).

## What Was Done

### Task 1: GitHub Actions publish workflow
- Created `.github/workflows/publish.yml` triggered on `v*` tag push
- Three-job pipeline: `wheels` (cibuildwheel matrix) → `sdist` → `publish`
- OIDC Trusted Publishing via `pypa/gh-action-pypi-publish@release/v1`
- `id-token: write` permission for OIDC identity — no API tokens needed
- `pypi` environment for approval gate before publishing
- `skip-existing: true` for idempotent republishing
- Wheel matrix identical to `ci.yml`: Linux/macOS/Windows, py3.10-3.12

### Task 2: SDK examples
- `examples/basic_query.py` — sync client with query, variables, introspection
- `examples/async_query.py` — async client with parallel queries via `asyncio.gather`
- `examples/subscription.py` — WebSocket subscription streaming with `async for`
- All examples include inline docstrings, setup instructions, env var documentation

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed SchemaSummary.query_fields attribute access**
- **Found during:** Task 2
- **Issue:** Example used `f.name` on `query_fields` items, but they are `str` not `FieldInfo`
- **Fix:** Changed to iterate strings directly; added `types` display section
- **Files modified:** `examples/basic_query.py`
- **Commit:** `aa601c7`

## Commits

| Commit | Message |
|--------|---------|
| `eee0b85` | feat(12-01): GitHub Actions publish workflow and SDK examples |
| `aa601c7` | fix(12-01): correct SchemaSummary.query_fields usage in basic_query example |

## Self-Check: PASSED
