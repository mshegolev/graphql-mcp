# Phase 16 Plan: Mutation Testing & CI Quality Gates

## Goal
Prove that the test suite catches real bugs (not just passes on correct code), and ensure every PR is automatically gated on lint, type check, tests, coverage, and multi-version compatibility to prevent merging broken code.

## Success Criteria
✅ `mutmut run --paths-to-mutate=src/graphql_mcp/domain/` produces a mutation score percentage, and adapters/config modules are excluded  
✅ CI blocks PR merge when mutation score drops below the configured threshold  
✅ GitHub Actions workflow runs ruff lint, type check (mypy or pyright), full test suite, and coverage check on every PR push  
✅ Branch protection rules require all quality gate status checks to pass before merge  
✅ Test matrix runs across Python 3.10, 3.11, 3.12  
✅ Nightly scheduled workflow runs full mutation testing and uploads the report as a CI artifact  

## Implementation Tasks

### Task 1: Configure Mutation Testing
**Estimated Effort:** 3 hours

#### Implementation Steps:
1. Set up mutmut configuration:
   - Configure source paths to target domain/ modules only
   - Exclude adapters/ and config modules from mutation analysis
   - Set up proper test runner configuration

2. Integrate with existing test suite:
   - Ensure mutmut can run against the current test suite
   - Configure mutation score reporting
   - Set up baseline mutation score measurement

3. Document mutation testing practices:
   - Create guidelines for interpreting mutation scores
   - Document common mutation patterns and how to address them
   - Provide examples of improving weak tests

#### Files to Modify:
- mutmut.ini (create new configuration file)
- setup.cfg (update mutmut configuration)
- README.md (add mutation testing documentation)

#### Verification:
- mutmut runs successfully against domain/ modules
- Mutation score is calculated and reported
- Adapters and config modules are excluded from analysis

### Task 2: Implement Mutation Score Threshold Enforcement
**Estimated Effort:** 2 hours

#### Implementation Steps:
1. Set up mutation score threshold:
   - Define minimum acceptable mutation score (e.g., 80%)
   - Configure CI to fail if score drops below threshold
   - Set up reporting of current vs. required scores

2. Integrate threshold checking with CI:
   - Add mutation score check to CI workflow
   - Configure failure conditions
   - Set up clear error messages for threshold violations

3. Document threshold policies:
   - Explain rationale for chosen threshold
   - Document process for adjusting thresholds
   - Provide guidance for addressing threshold failures

#### Files to Modify:
- .github/workflows/ci.yml (add mutation score check)
- mutmut.ini (configure threshold settings)

#### Verification:
- CI fails when mutation score drops below threshold
- Clear error messages are provided for threshold violations
- Threshold can be adjusted through configuration

### Task 3: Enhance CI Quality Gates
**Estimated Effort:** 4 hours

#### Implementation Steps:
1. Add type checking to CI:
   - Integrate mypy or pyright into CI workflow
   - Configure type checking rules and exclusions
   - Set up type check failure handling

2. Configure required status checks:
   - Set up branch protection rules in GitHub
   - Ensure all quality gates are required
   - Document status check requirements

3. Implement test matrix:
   - Configure CI to test across Python 3.10, 3.11, 3.12
   - Ensure all tests pass on all supported versions
   - Set up failure reporting for specific versions

#### Files to Modify:
- .github/workflows/ci.yml (enhance quality gates)
- pyproject.toml (add type checking configuration)
- README.md (document quality gate requirements)

#### Verification:
- Type checking runs successfully in CI
- All quality gates are required status checks
- Test matrix runs across all Python versions

### Task 4: Implement Nightly Mutation Testing
**Estimated Effort:** 2 hours

#### Implementation Steps:
1. Create scheduled workflow:
   - Set up nightly cron schedule for mutation testing
   - Configure full mutation test suite execution
   - Set up artifact storage for mutation reports

2. Configure mutation report generation:
   - Generate detailed mutation testing reports
   - Store reports as CI artifacts
   - Set up report retention policies

3. Set up notifications:
   - Configure notifications for mutation test failures
   - Set up reporting of mutation score trends
   - Document notification procedures

#### Files to Modify:
- .github/workflows/nightly-mutation.yml (create new workflow)
- mutmut.ini (configure report generation)

#### Verification:
- Nightly workflow runs as scheduled
- Mutation reports are generated and stored
- Notifications are sent for failures

### Task 5: Documentation and Examples
**Estimated Effort:** 1 hour

#### Implementation Steps:
1. Update README with quality gate documentation:
   - Document all quality gates and their requirements
   - Explain how to run quality checks locally
   - Provide troubleshooting guidance

2. Create developer documentation:
   - Best practices for maintaining high mutation scores
   - Guidelines for writing effective tests
   - Procedures for addressing quality gate failures

3. Add examples to documentation:
   - Sample mutation testing configurations
   - Example quality gate failure scenarios
   - Common patterns and anti-patterns

#### Files to Modify:
- README.md (add quality gate documentation)
- docs/testing.md (update with mutation testing information)
- docs/development.md (add quality practices)

#### Verification:
- Review documentation for accuracy and completeness
- Confirm examples work as described
- Validate documentation is clear and actionable

## Dependencies
- Phase 15 (Contract & Property-Based Testing) must be complete
- Existing test suite must be stable
- CI infrastructure must be operational

## Risks and Mitigations

### Risk 1: Mutation testing is too slow
**Mitigation:** Start with targeted mutation testing on critical modules only

### Risk 2: Mutation score threshold is too strict
**Mitigation:** Start with lower threshold and gradually increase as scores improve

### Risk 3: CI integration issues
**Mitigation:** Test changes in a separate branch before merging to main

### Risk 4: Nightly workflow consumes too many resources
**Mitigation:** Optimize mutation testing configuration and monitor resource usage

## Timeline
**Total Estimated Effort:** 12 hours

- Task 1 (Mutation Configuration): 3 days
- Task 2 (Threshold Enforcement): 2 days
- Task 3 (CI Quality Gates): 4 days
- Task 4 (Nightly Testing): 2 days
- Task 5 (Documentation): 1 day

## Acceptance Tests

### Mutation Testing Tests:
1. Run `mutmut run` and verify:
   - Only domain/ modules are mutated
   - Adapters and config modules are excluded
   - Mutation score is calculated and reported

2. Run mutation testing with threshold and verify:
   - Process fails when score drops below threshold
   - Clear error messages are provided
   - Threshold can be adjusted through configuration

### CI Quality Gate Tests:
1. Trigger CI workflow and verify:
   - Type checking runs successfully
   - All quality gates pass with good code
   - Quality gates fail appropriately with bad code

2. Check branch protection and verify:
   - All quality gates are required
   - PRs cannot be merged with failing gates
   - Status checks are properly reported

### Nightly Workflow Tests:
1. Verify scheduled workflow:
   - Runs at scheduled time
   - Generates mutation reports
   - Stores reports as artifacts