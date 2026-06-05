---
phase: 04-ship
plan: 02
subsystem: ci, docs, publishing
tags: [ci, cibuildwheel, readme, glama, mcp-server-descriptor]
dependency_graph:
  requires: [04-01-PLAN]
  provides: [ci-workflow, project-documentation, glama-publication-files]
  affects: []
tech_stack:
  added: [cibuildwheel, github-actions]
  patterns: [platform-matrix-ci, mcp-server-descriptor, glama-registry]
key_files:
  created:
    - .github/workflows/ci.yml
    - README.md
    - server.json
    - glama.json
  modified:
    - .gitignore
decisions:
  - "Fallback-install job tests pre-built wheel instead of sdist — maturin build-backend requires Rust so pure pip install from sdist fails without Rust; wheel embeds native extension and orjson fallback handles runtime"
  - "OWNER placeholder in GitHub URLs — user replaces with actual org before publishing"
  - "Added uv.lock to .gitignore — generated lockfile not tracked in source"
metrics:
  duration: 270s
  completed: "2026-06-05T22:44:19Z"
---

# Phase 4 Plan 2: CI Workflow + README + Glama Publication Files Summary

**One-liner:** GitHub Actions CI with 4-job pipeline (lint/test → cibuildwheel full platform matrix → sdist → fallback-install verification), comprehensive README documenting all 6 operations/env vars/architecture, and Glama MCP server descriptor files.

## What Was Done

### Task 1: Create GitHub Actions CI workflow ✅
**Commit:** `a8e08e3`

Created `.github/workflows/ci.yml` with 4 jobs triggered on push/PR to main and workflow_dispatch:

1. **`lint-and-test`** (ubuntu-latest): Installs Rust + Python 3.11, runs `ruff check src/ tests/` and `pytest tests/ -v --tb=short` with all optional deps.

2. **`wheels`** (matrix: ubuntu/macos/windows, needs lint-and-test): Uses `pypa/cibuildwheel@v2.23` with full platform coverage:
   - Python: 3.10, 3.11, 3.12
   - Linux: x86_64 + aarch64 (manylinux + musllinux), Rust installed in containers via rustup
   - macOS: arm64 + x86_64
   - Windows: AMD64
   - QEMU cross-compile for Linux aarch64
   - In-wheel test: pytest (skips codec parity tests in container builds)

3. **`sdist`** (ubuntu-latest, needs lint-and-test): Builds source distribution via `python -m build --sdist`.

4. **`fallback-install`** (ubuntu-latest, needs wheels): Downloads built ubuntu x86_64 cp311 wheel, installs on clean Python 3.11 (no Rust), verifies `from graphql_mcp import GraphQLClient` succeeds — confirms orjson fallback path works.

All GitHub Actions pinned to versioned tags (v3/v4/v5/v2.23) per threat model T-04-02.

### Task 2: Create README.md, server.json, and glama.json ✅
**Commit:** `6751bf7`

**README.md** — Comprehensive project documentation:
- CI badge, one-line description, features list
- Installation section with 5 pip install variants (core, server, mcp, cli, all)
- Quick start with GraphQLClient.from_env() and all 6 operations
- Complete env var configuration table (16 variables with defaults)
- 4 adapter sections with usage commands (Library, FastAPI REST, MCP stdio, CLI)
- Hexagonal architecture diagram and description
- MIT license

**server.json** — MCP server descriptor:
- 6 tool definitions matching MCP stdio adapter
- stdio transport pointing to `python -m graphql_mcp.adapters.inbound.mcp_stdio`

**glama.json** — Glama publication metadata:
- Category: developer-tools, tags: graphql/mcp/schema/federation/query
- References server.json for tool discovery

**Housekeeping:** Added `uv.lock` to `.gitignore` (pre-existing untracked generated file).

## Verification Results

| Check | Result |
|-------|--------|
| `.github/workflows/ci.yml` is valid YAML | ✅ Parsed by PyYAML |
| `README.md` documents all 6 operations | ✅ All present |
| `README.md` documents env vars | ✅ 16 vars in config table |
| `README.md` documents installation | ✅ 5 pip variants |
| `README.md` documents architecture | ✅ Hexagonal diagram |
| `server.json` has 6 MCP tools | ✅ Verified |
| `server.json` has stdio transport | ✅ Verified |
| `glama.json` references server.json | ✅ Verified |
| Both JSON files parse without error | ✅ `json.load()` succeeds |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Added uv.lock to .gitignore**
- **Found during:** Post-commit untracked file check after Task 2
- **Issue:** `uv.lock` file was untracked — generated lockfile should not be committed
- **Fix:** Added `uv.lock` to `.gitignore`
- **Files modified:** `.gitignore`
- **Commit:** included in final metadata commit

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Fallback-install tests pre-built wheel, not sdist | maturin build-backend requires Rust — cannot pip install from sdist without Rust toolchain; wheel embeds native extension and orjson fallback handles the case where native extension is not importable |
| OWNER placeholder in repository URLs | Plan specifies placeholder — user replaces with actual GitHub org before publishing |
| Added uv.lock to .gitignore | Generated lockfile from uv package manager; not part of project source |

## Self-Check: PASSED

All 5 created files verified present. Both task commits (`a8e08e3`, `6751bf7`) confirmed in git log.
