# Phase 14 Plan: Coverage & Snapshot Infrastructure

## Goal
Implement comprehensive testing infrastructure including coverage enforcement with pytest-cov and snapshot testing with pytest-syrupy to ensure code quality and prevent regressions.

## Success Criteria
✅ Running `pytest --cov --cov-branch --cov-fail-under=85` fails the test suite if branch coverage drops below 85%  
✅ Coverage report breaks down by package (domain/, adapters/, ports/) with per-package percentages visible in terminal output  
✅ README displays a coverage badge that updates automatically after CI runs  
✅ pytest-syrupy snapshot tests capture and compare response payloads; `--snapshot-update` regenerates snapshots  
✅ Schema introspection snapshots and error response snapshots detect regressions  

## Implementation Tasks

### Task 1: Configure Coverage Infrastructure
**Estimated Effort:** 2 hours

#### Implementation Steps:
1. Add coverage configuration to pyproject.toml:
   - Enable branch coverage
   - Set minimum coverage threshold to 85%
   - Configure per-package coverage targets
   - Exclude test files from coverage calculation

2. Create .coveragerc file with detailed configuration:
   - Specify source directories
   - Define coverage report format
   - Set up HTML and XML report generation

3. Update existing tests to improve coverage where needed:
   - Identify uncovered code paths
   - Add missing test cases for critical functionality

#### Files to Modify:
- pyproject.toml (add coverage configuration)
- .coveragerc (create new configuration file)
- Test files (where coverage improvements are needed)

#### Verification:
- Run `pytest --cov --cov-branch` and verify per-package breakdown
- Confirm coverage meets 85% threshold
- Validate HTML and XML reports are generated correctly

### Task 2: Implement Snapshot Testing Framework
**Estimated Effort:** 3 hours

#### Implementation Steps:
1. Add pytest-syrupy to dev dependencies in pyproject.toml

2. Create snapshot tests for schema introspection:
   - Capture current schema structure
   - Test schema consistency across runs
   - Handle schema evolution with update mechanism

3. Create snapshot tests for error responses:
   - Transport error responses
   - GraphQL error responses
   - Schema unavailable error responses

4. Create snapshot tests for key response payloads:
   - Query results with various data structures
   - Introspection query results
   - Entity resolution responses

5. Establish snapshot update workflow:
   - Document process for legitimate snapshot updates
   - Create scripts for bulk snapshot regeneration when needed

#### Files to Modify:
- pyproject.toml (add pytest-syrupy dependency)
- tests/test_snapshot_responses.py (new file for response snapshots)
- tests/test_snapshot_schema.py (new file for schema snapshots)
- tests/test_snapshot_errors.py (new file for error snapshots)

#### Verification:
- Run snapshot tests and confirm they pass with current implementation
- Test snapshot failure scenarios with intentional changes
- Verify snapshot update process works correctly

### Task 3: Integrate Coverage into CI Pipeline
**Estimated Effort:** 1.5 hours

#### Implementation Steps:
1. Update .github/workflows/ci.yml:
   - Add coverage collection to test step
   - Configure coverage report upload to coverage service
   - Set up coverage threshold enforcement

2. Add coverage badge to README.md:
   - Generate badge URL from coverage service
   - Position badge appropriately in README

3. Configure branch protection rules:
   - Require coverage checks to pass before merge
   - Set up notifications for coverage drops

#### Files to Modify:
- .github/workflows/ci.yml (update CI workflow)
- README.md (add coverage badge)

#### Verification:
- Trigger CI run and confirm coverage is collected
- Verify coverage badge displays correctly
- Test that PRs fail when coverage drops below threshold

### Task 4: Documentation and Examples
**Estimated Effort:** 1 hour

#### Implementation Steps:
1. Update README.md with coverage and snapshot testing documentation:
   - How to run coverage reports locally
   - How to interpret coverage output
   - How to update snapshots

2. Create developer documentation:
   - Best practices for maintaining coverage
   - Guidelines for writing effective snapshot tests
   - Troubleshooting common issues

3. Add examples to documentation:
   - Sample coverage configuration
   - Example snapshot test cases
   - Common patterns and anti-patterns

#### Files to Modify:
- README.md (add testing documentation)
- docs/testing.md (create new documentation file)

#### Verification:
- Review documentation for accuracy and completeness
- Confirm examples work as described
- Validate documentation is clear and actionable

## Dependencies
- Phase 13 (Copier Template Extraction) must be complete
- Existing test suite must be stable
- CI infrastructure must be operational

## Risks and Mitigations

### Risk 1: Coverage requirements too strict
**Mitigation:** Start with lower threshold and gradually increase as coverage improves

### Risk 2: Snapshot tests become brittle
**Mitigation:** Focus on stable parts of API surface and use appropriate snapshot granularity

### Risk 3: CI integration issues
**Mitigation:** Test changes in a separate branch before merging to main

## Timeline
**Total Estimated Effort:** 7.5 hours

- Task 1 (Coverage Configuration): 2 days
- Task 2 (Snapshot Testing): 3 days
- Task 3 (CI Integration): 1 day
- Task 4 (Documentation): 1 day

## Acceptance Tests

### Coverage Tests:
1. Run `pytest --cov --cov-branch` and verify:
   - Overall coverage ≥ 85%
   - Domain package coverage clearly shown
   - Adapters package coverage clearly shown
   - Ports package coverage clearly shown
   - HTML report generated at htmlcov/index.html

2. Run `pytest --cov --cov-branch --cov-fail-under=85` and verify:
   - Command passes with current coverage
   - Command fails when coverage is artificially reduced

### Snapshot Tests:
1. Run all snapshot tests and verify they pass:
   - Response snapshot tests pass
   - Schema snapshot tests pass
   - Error snapshot tests pass

2. Make intentional changes and verify snapshot failures:
   - Modify a response and confirm test failure
   - Update snapshots with --snapshot-update
   - Verify updated snapshots work correctly

### CI Integration Tests:
1. Trigger CI workflow and verify:
   - Coverage collected and reported
   - Coverage badge updates correctly
   - PR blocked when coverage drops