# Phase 14: Coverage & Snapshot Infrastructure — Discuss

**Goal**: Every test run produces branch-level coverage reports with per-module breakdown and enforced thresholds, and response/schema/error snapshots catch regressions automatically — a developer knows exactly what's uncovered and sees clear diffs when behavior changes.

**Requirements**: COV-01, COV-02, COV-03, SNAP-01, SNAP-02, SNAP-03

---

## Requirements Analysis

### Coverage Requirements (COV-01, COV-02, COV-03)

1. **COV-01**: pytest-cov enforces branch coverage with configurable minimum threshold (default 85%); CI fails when coverage drops below threshold
   - Need to implement pytest-cov configuration with branch coverage
   - Configure coverage threshold in pyproject.toml
   - Ensure CI fails when coverage drops below threshold

2. **COV-02**: Per-module coverage reports break down coverage by package (domain/, adapters/, ports/) with separate configurable targets
   - Need to configure coverage reporting by module
   - Set up separate coverage targets for different packages
   - Generate per-package coverage reports

3. **COV-03**: Coverage badge auto-generated in README from CI results
   - Integrate coverage reporting with CI pipeline
   - Generate coverage badge that updates automatically
   - Update README to include coverage badge

### Snapshot Requirements (SNAP-01, SNAP-02, SNAP-03)

1. **SNAP-01**: pytest-syrupy captures response snapshots with auto-update mode; snapshot mismatches fail tests with clear diffs
   - Integrate pytest-syrupy for snapshot testing
   - Implement auto-update mode for snapshots
   - Ensure clear diff output on snapshot mismatches

2. **SNAP-02**: Schema introspection result snapshots detect schema regressions across refactors
   - Create snapshot tests for schema introspection results
   - Implement schema comparison logic
   - Detect and report schema regression

3. **SNAP-03**: Error response snapshots for all three error classes (transport, graphql, schema_unavailable) verify consistent error shapes
   - Create snapshot tests for transport, graphql, and schema_unavailable error responses
   - Ensure consistent error response shapes
   - Validate error handling across all error classes

---

## Technical Approach

### Coverage Implementation

1. **Pytest Configuration**:
   - pytest-cov is already in dev dependencies (line 26 in pyproject.toml)
   - Configure branch coverage in pyproject.toml
   - Set minimum coverage threshold to 85%
   - Configure per-module coverage reporting for domain/, adapters/, ports/

2. **CI Integration**:
   - Update GitHub Actions workflow (.github/workflows/ci.yml) to include coverage reporting
   - Configure coverage failure thresholds
   - Set up automatic coverage badge generation via Codecov or GitHub Actions

3. **Reporting**:
   - Generate HTML coverage reports for local development
   - Configure terminal output to show per-module coverage
   - Set up coverage badge integration with README

### Snapshot Testing Implementation

1. **Pytest-Syrupy Integration**:
   - Add pytest-syrupy as a development dependency in pyproject.toml
   - Configure syrupy snapshots directory (typically tests/__snapshots__)
   - Implement snapshot update workflow

2. **Schema Snapshot Tests**:
   - Create schema introspection snapshot tests in tests/ directory
   - Implement schema comparison logic
   - Set up schema regression detection

3. **Error Response Snapshots**:
   - Create snapshot tests for all error classes (transport, graphql, schema_unavailable)
   - Validate error response consistency
   - Document error response formats

---

## Project Structure Analysis

Based on examination of the codebase:

- **Module Structure**: 
  - `src/graphql_mcp/domain/` - Core business logic (models, errors, schema_service)
  - `src/graphql_mcp/adapters/` - Inbound/outbound adapters (CLI, REST, MCP, HTTP transport)
  - `src/graphql_mcp/ports/` - Protocol interfaces (transport, schema_source, json_codec)

- **Test Structure**: 
  - `tests/` directory with 39+ test files covering all functionality
  - Existing test suite with 341 tests (from REQUIREMENTS.md)
  - Integration tests in `tests/integration/`

- **CI Pipeline**:
  - GitHub Actions workflow in `.github/workflows/ci.yml`
  - Already runs linting and tests
  - No coverage reporting currently implemented

- **Configuration**:
  - `pyproject.toml` with build system, dependencies, and tool configurations
  - pytest already configured with testpaths and options

---

## Success Criteria Verification Plan

1. **Coverage Verification**:
   - Run `pytest --cov --cov-branch --cov-fail-under=85` to verify threshold enforcement
   - Check coverage report shows per-package percentages for domain/, adapters/, ports/
   - Verify coverage badge displays current percentage in README

2. **Snapshot Verification**:
   - Run snapshot tests to verify response payload capture
   - Test `--snapshot-update` functionality
   - Verify schema introspection snapshot tests
   - Confirm error response snapshot tests for all error classes (transport, graphql, schema_unavailable)

---

## Dependencies and Prerequisites

- Stable codebase with existing test suite (341 tests from v2.0)
- pytest-cov already in dev dependencies (needs configuration)
- pytest configuration already in place in pyproject.toml
- GitHub Actions CI workflow established
- README structure ready for badge integration

---

## Risks and Mitigations

1. **Risk**: Coverage threshold may be too high initially
   **Mitigation**: Start with slightly lower threshold and incrementally increase

2. **Risk**: Snapshot tests may be brittle with frequently changing responses
   **Mitigation**: Focus snapshots on stable interfaces and provide clear update procedures

3. **Risk**: Per-module coverage targets may be difficult to configure
   **Mitigation**: Start with global coverage and gradually implement per-module configuration

---

## Next Steps

1. Configure pytest-cov in pyproject.toml for branch coverage and per-module reporting
2. Add pytest-syrupy to dev dependencies and set up snapshot testing framework
3. Update CI workflow to run coverage and generate badge
4. Create initial coverage report to establish baseline
5. Develop snapshot tests for schema introspection and error responses
6. Update README with coverage badge
7. Verify all success criteria are met