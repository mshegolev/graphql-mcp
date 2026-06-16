---
phase: "13"
plan: "01"
subsystem: template
tags: [copier, jinja2, template, brick-generation, infrastructure]
dependency_graph:
  requires: [pyproject.toml, Dockerfile, src/graphql_mcp/]
  provides: [template/, tests/test_copier_template.py]
  affects: []
tech_stack:
  added: [copier, jinja2]
  patterns: [copier-template, jinja2-parameterization, project-scaffolding]
key_files:
  created:
    - template/copier.yml
    - template/project/pyproject.toml.jinja
    - template/project/Dockerfile.jinja
    - template/project/src/{{module_name}}/config.py.jinja
    - template/project/src/{{module_name}}/__init__.py.jinja
    - template/project/src/{{module_name}}/domain/models.py
    - template/project/src/{{module_name}}/domain/errors.py
    - template/project/src/{{module_name}}/domain/schema_service.py.jinja
    - template/project/src/{{module_name}}/ports/transport.py.jinja
    - template/project/src/{{module_name}}/ports/schema_source.py.jinja
    - template/project/src/{{module_name}}/ports/json_codec.py
    - template/project/src/{{module_name}}/adapters/inbound/lib.py.jinja
    - template/project/src/{{module_name}}/adapters/inbound/cli.py.jinja
    - template/project/src/{{module_name}}/adapters/outbound/http_transport.py.jinja
    - template/project/src/{{module_name}}/adapters/outbound/codec_factory.py.jinja
    - template/project/tests/conftest.py.jinja
    - template/project/tests/test_domain_purity.py.jinja
    - template/project/tests/test_models.py.jinja
    - template/project/tests/test_schema_service.py.jinja
    - tests/test_copier_template.py
  modified: []
decisions:
  - "copier.yml with _subdirectory: project — separates template config from template content"
  - "hatchling as default build backend (maturin only when rust_native=true)"
  - "Domain layer (models, errors) not templatized with .jinja — no module_name references in pure domain"
  - "Ports with TYPE_CHECKING imports get .jinja suffix; framework-free ports stay as plain .py"
  - "9 generated tests covering domain purity, models, and schema service cascade"
  - "env_prefix default derived from module_name via Jinja2 filter (e.g., kafka_mcp → KAFKA)"
metrics:
  duration: "486s"
  completed: "2026-06-16"
---

# Phase 13 Plan 01: Copier Template Extraction Summary

**One-liner:** Copier template with Jinja2-parameterized MCP brick skeleton — module name, env prefix, and optional features (Rust native, subscriptions, OTEL) generate a complete hexagonal-architecture project passing 9 tests out of the box.

## What Was Done

### Task 1: copier.yml and template directory structure
Created `template/copier.yml` with:
- `module_name` — Python snake_case module name (validated via regex)
- `package_name` — PyPI kebab-case name (auto-derived from module_name)
- `env_prefix` — Environment variable prefix (auto-derived from module_name)
- `description` — One-line project description
- `python_version` — Choice of 3.10/3.11/3.12
- `rust_native` — Toggle Rust native extension (maturin vs hatchling)
- `subscriptions` — Toggle WebSocket/SSE subscription support
- `otel` — Toggle OpenTelemetry observability

### Task 2: Jinja2-templatized project skeleton
Created 26 template files under `template/project/`:
- **Build**: `pyproject.toml.jinja` (hatchling or maturin), `Dockerfile.jinja` (Rust or pure-Python build stage)
- **Domain**: models.py, errors.py (plain Python — no module_name refs), schema_service.py.jinja
- **Ports**: transport.py.jinja, schema_source.py.jinja, json_codec.py (plain)
- **Adapters**: lib.py.jinja (GraphQLClient), cli.py.jinja, http_transport.py.jinja, codec_factory.py.jinja
- **Config**: config.py.jinja (parameterized env_prefix, class name)
- **Tests**: conftest.py.jinja, test_domain_purity.py.jinja, test_models.py.jinja, test_schema_service.py.jinja

### Task 3: Copier template test suite
Created `tests/test_copier_template.py` with 20 tests across 5 test classes:
- **TestGeneratedStructure** (9 tests): File existence checks
- **TestNoHardcodedStrings** (1 test): Greps all generated files for `graphql_mcp`/`graphql-mcp`/`GRAPHQL_`
- **TestParameterization** (4 tests): Verifies Jinja2 substitution produces correct values
- **TestGeneratedTestSuite** (1 test): Installs generated project and runs its 9 tests
- **TestOptionalFeatures** (5 tests): Verifies all-features-enabled project has maturin, OTEL, subscriptions, no hardcoded strings

### Task 4: Existing test regression check
All 303 non-OTEL tests pass. 3 pre-existing OTEL instrumentation test failures (FastAPI SERVER span detection) are unrelated to this change — they fail identically on the HEAD commit before template changes.

## Deviations from Plan

None — plan executed exactly as written.

## Decisions Made

1. **copier `_subdirectory: project`** — Separates copier.yml config from template files for clean structure
2. **hatchling as default build backend** — simpler than maturin for non-Rust projects; maturin only when rust_native=true
3. **Domain layer files not .jinja-suffixed** — models.py, errors.py, json_codec.py have no module_name references, so they're plain Python files copied verbatim
4. **Config class name derived from env_prefix** — `{{ env_prefix.title().replace('_', '') }}Config` (e.g., `KafkaConfig`)
5. **9 generated tests** — Domain purity, model construction, schema service cascade — enough to prove the generated project works

## Commits

| Hash | Message |
|------|---------|
| 5fda1d8 | feat(13-01): Copier template extraction with parameterized MCP brick generation |

## Test Results

- 20 new copier template tests: **all pass**
- 303 existing tests (excluding pre-existing OTEL failures): **all pass**
- Generated project tests: **9/9 pass**
- Hardcoded string check: **0 violations** (both minimal and full-features configurations)

## Self-Check: PASSED
