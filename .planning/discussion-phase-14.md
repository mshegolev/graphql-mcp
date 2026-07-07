# Phase 14 Discussion: Coverage & Snapshot Infrastructure

## Context

This phase focuses on implementing comprehensive testing infrastructure for the generic-graphql-mcp project, specifically:
1. Coverage enforcement with pytest-cov
2. Snapshot testing with pytest-syrupy

The goal is to ensure every test run produces branch-level coverage reports with per-module breakdown and enforced thresholds, and response/schema/error snapshots catch regressions automatically.

## Requirements Analysis

From REQUIREMENTS.md, the specific requirements for this phase are:

### Coverage Requirements (COV-01, COV-02, COV-03)
- pytest-cov enforces branch coverage with configurable minimum threshold (default 85%)
- Per-module coverage reports break down coverage by package (domain/, adapters/, ports/) with separate configurable targets
- Coverage badge auto-generated in README from CI results

### Snapshot Requirements (SNAP-01, SNAP-02, SNAP-03)
- pytest-syrupy captures response snapshots with auto-update mode; snapshot mismatches fail tests with clear diffs
- Schema introspection result snapshots detect schema regressions across refactors
- Error response snapshots for all three error classes (transport, graphql, schema_unavailable) verify consistent error shapes

## Current State Assessment

Based on codebase inspection:
- Project uses pytest for testing with extensive test coverage (341 tests mentioned in PROJECT.md)
- pyproject.toml includes pytest-cov in dev dependencies
- No existing coverage configuration found (.coveragerc, pytest.ini, etc.)
- No snapshot testing infrastructure currently implemented
- CI workflow exists but doesn't include coverage enforcement

## Technical Approach

### Coverage Implementation
1. Configure pytest-cov in pyproject.toml with branch coverage enabled
2. Set up per-package coverage targets using coverage configuration
3. Integrate coverage reporting into CI workflow
4. Add coverage badge to README.md

### Snapshot Implementation
1. Add pytest-syrupy to dev dependencies
2. Create snapshot tests for:
   - Schema introspection results
   - Error response shapes for all error classes
   - Key response payloads
3. Establish snapshot update workflow for legitimate changes

## Dependencies

This phase depends on:
- Completion of Phase 13 (Copier Template Extraction)
- Stable codebase with existing test suite (341 tests)
- CI infrastructure already in place

## Success Criteria

As defined in ROADMAP.md:
1. Running `pytest --cov --cov-branch --cov-fail-under=85` fails the test suite if branch coverage drops below 85%
2. Coverage report breaks down by package with per-package percentages visible in terminal output
3. README displays a coverage badge that updates automatically after CI runs
4. pytest-syrupy snapshot tests capture and compare response payloads; `--snapshot-update` regenerates snapshots
5. Schema introspection snapshots and error response snapshots detect regressions