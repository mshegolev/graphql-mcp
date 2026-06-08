---
phase: 08-entities-ship-v1.1
plan: 02
subsystem: shipping
tags: [changelog, license, docs, shipping, v1.1]
dependency_graph:
  requires: [08-01]
  provides: [changelog, license, server-manifest, readme-v1.1]
  affects: [CHANGELOG.md, LICENSE, server.json, glama.json, README.md]
tech_stack:
  added: []
  patterns: [keep-a-changelog]
key_files:
  created:
    - CHANGELOG.md
    - LICENSE
  modified:
    - server.json
    - glama.json
    - README.md
decisions:
  - "pyproject.toml version left as dynamic (maturin/Cargo.toml controls it) — no static bump needed"
  - "v1.1.0 date set to 2026-06-08 matching actual ship date"
metrics:
  duration: 4m26s
  completed: "2026-06-08T15:58:13Z"
  tasks: 2/2
  tests_added: 0
  tests_total: 229
---

# Phase 08 Plan 02: Ship v1.1 Artifacts Summary

CHANGELOG.md covering v1.0.0 and v1.1.0 milestones in Keep a Changelog format, MIT LICENSE file, server.json bumped to 1.1.0 with 7 tools, glama.json with entities tag, README.md documenting 7 operations across all faces with async usage and serve/Docker sections.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Create CHANGELOG.md and LICENSE | 5f2fcb9 | CHANGELOG.md, LICENSE |
| 2 | Update server.json, glama.json, README.md, pyproject.toml | 2e8b3c7 | server.json, glama.json, README.md |

## Implementation Details

### CHANGELOG.md

Created with Keep a Changelog format documenting both milestones:

- **v1.1.0 (2026-06-08)**: 11 Added items (entities, async client, serve, MCP-over-HTTP, readiness probe, Dockerfile, benchmarks) + 3 Fixed items (codec wiring, SchemaResolutionError handling, resource lifecycle)
- **v1.0.0 (2026-06-05)**: 10 Added items (GraphQLClient with 6 ops, error typing, mutation guard, schema cascade, federation, Rust codec, REST/MCP/CLI adapters, manifests)

### LICENSE

Standard MIT License with copyright holder "graphql-mcp contributors".

### server.json

- Version: `0.1.0` → `1.1.0`
- Tools: 6 → 7 (added `entities` with federation pass-through description)
- Description: Added "and entity resolution" suffix

### glama.json

- Tags: Added `entities` to the array
- Description: Updated to include "and entity resolution"

### README.md

- Features: `6 operations` → `7 operations` with `entities` in the list
- Added "Async support" feature bullet
- Quick Start: Added entities usage example with federation representations
- New "Async Usage" section with `AsyncGraphQLClient` example
- REST endpoints: Added `POST /graphql/entities` and `GET /ready`
- MCP tools: `6 MCP tools` → `7 MCP tools` with `entities`
- CLI commands: Added `graphql-mcp entities` example
- New "Serve (REST + MCP-over-HTTP)" section with `graphql-mcp serve` docs
- New "Docker" section with build and run example

### pyproject.toml

No changes needed — version is `dynamic = ["version"]` controlled by maturin/Cargo.toml. The plan acknowledged this correctly.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all documentation references actual implemented functionality.

## Self-Check: PASSED

- [x] CHANGELOG.md exists with v1.0.0 and v1.1.0 sections
- [x] LICENSE exists with MIT License text
- [x] server.json has 7 tools, version 1.1.0, entities tool
- [x] glama.json has entities tag and entity resolution description
- [x] README.md has 7 operations, entities in all faces, async usage, serve/Docker
- [x] Commit 5f2fcb9 exists (task 1)
- [x] Commit 2e8b3c7 exists (task 2)
- [x] 229 tests pass, 0 regressions
