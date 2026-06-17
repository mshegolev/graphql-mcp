# Phase 16 Discussion: Mutation Testing & CI Quality Gates

## Context

This phase focuses on implementing mutation testing to verify the effectiveness of our test suite and establishing comprehensive CI quality gates to ensure code quality:

1. Mutation testing with mutmut to measure test suite effectiveness
2. CI quality gates to prevent merging of low-quality code

## Requirements Analysis

From REQUIREMENTS.md, the specific requirements for this phase are:

### Mutation Testing Requirements (MUT-01, MUT-02, MUT-03)
- mutmut runs against domain/ and query_service modules; mutation score is reported as a percentage
- CI blocks merge if mutation score drops below configured threshold
- Mutation testing is scoped to domain/ and query_service only; adapters and config modules are excluded from mutation analysis

### CI Quality Gates Requirements (CI-01, CI-02, CI-03, CI-04)
- GitHub Actions workflow runs lint (ruff), type check, test suite, and coverage check on every PR push
- Required status checks configured so PRs cannot merge without all quality gates passing
- Test matrix runs across Python 3.10, 3.11, 3.12 in CI
- Nightly scheduled workflow runs full mutation testing suite and reports results

## Current State Assessment

Based on codebase inspection:
- Project uses pytest for testing with extensive test coverage (341 tests mentioned in PROJECT.md)
- CI workflow exists in .github/workflows/ci.yml
- Ruff linting is already configured
- Coverage testing is already implemented (Phase 14)
- No existing mutation testing infrastructure implemented
- Basic quality gates exist but need enhancement

## Technical Approach

### Mutation Testing Implementation
1. Configure mutmut for the project:
   - Set up mutmut configuration to target domain/ modules
   - Exclude adapters and config modules from mutation analysis
   - Configure mutation score reporting

2. Integrate mutation testing with CI:
   - Add mutation testing to CI workflow
   - Configure threshold enforcement for mutation scores
   - Set up mutation score reporting and visualization

3. Document mutation testing practices:
   - Create guidelines for interpreting mutation scores
   - Document how to improve mutation scores
   - Provide examples of common mutation patterns

### CI Quality Gates Implementation
1. Enhance existing CI workflow:
   - Add type checking (mypy or pyright) to CI
   - Ensure all quality checks are required status checks
   - Configure test matrix for Python 3.10, 3.11, 3.12

2. Implement nightly mutation testing:
   - Create scheduled workflow for full mutation testing
   - Configure mutation report generation and storage
   - Set up notifications for mutation test results

3. Document CI quality gates:
   - Create documentation for all quality gates
   - Provide guidance for developers on meeting quality requirements
   - Document troubleshooting procedures for failing gates

## Dependencies

This phase depends on:
- Completion of Phase 15 (Contract & Property-Based Testing)
- Stable codebase with existing test suite
- CI infrastructure already in place

## Success Criteria

As defined in ROADMAP.md:
1. `mutmut run --paths-to-mutate=src/graphql_mcp/domain/,src/graphql_mcp/domain/query_service.py` produces a mutation score percentage, and adapters/config modules are excluded
2. CI blocks PR merge when mutation score drops below the configured threshold
3. GitHub Actions workflow runs ruff lint, type check (mypy or pyright), full test suite, and coverage check on every PR push
4. Branch protection rules require all quality gate status checks to pass before merge
5. Test matrix runs across Python 3.10, 3.11, 3.12
6. Nightly scheduled workflow runs full mutation testing and uploads the report as a CI artifact