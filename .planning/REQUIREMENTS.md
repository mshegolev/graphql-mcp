# graphql-mcp v2.1 — Requirements

**Milestone:** v2.1 Testing & Quality
**Scope:** Coverage enforcement, contract testing, mutation testing, property-based testing, snapshot testing, CI quality gates.
**Predecessor:** v2.0 Production-Grade Platform (shipped 2026-06-16, 17/17 requirements satisfied, 341 tests)

---

## Requirements

### Coverage

- [ ] **COV-01**: pytest-cov enforces branch coverage with configurable minimum threshold (default 85%); CI fails when coverage drops below threshold — verified by test run with `--cov --cov-branch --cov-fail-under=85`.
- [ ] **COV-02**: Per-module coverage reports break down coverage by package (domain/, adapters/, ports/) with separate configurable targets — verified by coverage report showing per-package percentages.
- [ ] **COV-03**: Coverage badge auto-generated in README from CI results — verified by badge URL rendering current coverage percentage after CI run.

### Contract Testing

- [ ] **CTR-01**: GraphQL schema snapshots are stored and compared on test run; breaking upstream schema changes are detected automatically — verified by test that fails when schema snapshot drifts.
- [ ] **CTR-02**: Response shape contracts validate that upstream responses match expected structure beyond basic type checks — verified by test with response shape assertion failing on unexpected field addition/removal.
- [ ] **CTR-03**: Pact consumer-driven contract tests define brick-upstream contracts and can publish to a Pact broker — verified by running pact tests and generating contract JSON.

### Mutation Testing

- [ ] **MUT-01**: mutmut runs against domain/ and query_service modules; mutation score is reported as a percentage — verified by running mutmut and checking output for score.
- [ ] **MUT-02**: CI blocks merge if mutation score drops below configured threshold — verified by CI workflow configuration with mutation score check step.
- [ ] **MUT-03**: Mutation testing is scoped to domain/ and query_service only; adapters and config modules are excluded from mutation analysis — verified by mutmut configuration showing module exclusions.

### Property-Based Testing

- [ ] **PROP-01**: Hypothesis custom strategies generate valid and edge-case GraphQL queries, variables dicts, and mock response shapes — verified by test using `@given(graphql_query())` that produces syntactically varied inputs.
- [ ] **PROP-02**: Fuzz tests generate malformed queries (invalid syntax, deeply nested, oversized), invalid JSON payloads, and boundary-case variables to exercise error handling paths — verified by test that catches no unhandled exceptions across 100+ generated inputs.
- [ ] **PROP-03**: Domain model invariant tests verify QueryResult, TypeInfo, and Subgraph dataclass contracts hold under random input (e.g., error_class always in {transport, graphql, ok}) — verified by hypothesis test with model strategies.

### Snapshot Testing

- [ ] **SNAP-01**: pytest-syrupy captures response snapshots with auto-update mode (`--snapshot-update`); snapshot mismatches fail tests with clear diffs — verified by test that detects intentional response change.
- [ ] **SNAP-02**: Schema introspection result snapshots detect schema regressions across refactors — verified by snapshot test against mock introspection endpoint.
- [ ] **SNAP-03**: Error response snapshots for all three error classes (transport, graphql, schema_unavailable) verify consistent error shapes — verified by snapshot tests for each error path.

### CI Quality Gates

- [ ] **CI-01**: GitHub Actions workflow runs lint (ruff), type check, test suite, and coverage check on every PR push — verified by workflow YAML and successful CI run.
- [ ] **CI-02**: Required status checks configured so PRs cannot merge without all quality gates passing — verified by branch protection rule configuration.
- [ ] **CI-03**: Test matrix runs across Python 3.10, 3.11, 3.12 in CI — verified by matrix configuration in workflow YAML and passing runs on all versions.
- [ ] **CI-04**: Nightly scheduled workflow runs full mutation testing suite and reports results — verified by cron schedule in workflow YAML and mutation report artifact.

---

## Future Requirements (deferred)

_None — all proposed features selected for v2.1._

## Out of Scope

| Feature | Reason |
|---------|--------|
| Load/stress testing (locust) | Different concern; belongs in a performance milestone |
| Visual test reports (Allure) | Nice-to-have but not core quality infrastructure |
| Fuzzing with AFL/libFuzzer | Overkill for a Python GraphQL client library |
| Test data factories (factory_boy) | Current test fixtures are sufficient |
| End-to-end browser testing | No browser UI in this project |
| Performance regression testing | Benchmarks exist from v1.1; not in quality scope |

---

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| COV-01 | TBD | Pending |
| COV-02 | TBD | Pending |
| COV-03 | TBD | Pending |
| CTR-01 | TBD | Pending |
| CTR-02 | TBD | Pending |
| CTR-03 | TBD | Pending |
| MUT-01 | TBD | Pending |
| MUT-02 | TBD | Pending |
| MUT-03 | TBD | Pending |
| PROP-01 | TBD | Pending |
| PROP-02 | TBD | Pending |
| PROP-03 | TBD | Pending |
| SNAP-01 | TBD | Pending |
| SNAP-02 | TBD | Pending |
| SNAP-03 | TBD | Pending |
| CI-01 | TBD | Pending |
| CI-02 | TBD | Pending |
| CI-03 | TBD | Pending |
| CI-04 | TBD | Pending |

**Coverage:**
- v2.1 requirements: 19 total
- Mapped to phases: 0
- Unmapped: 19

---
*Requirements defined: 2026-06-16*
*Last updated: 2026-06-16 after initial definition*
