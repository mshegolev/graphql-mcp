# Phase 15 Plan: Contract & Property-Based Testing

## Goal
Implement contract testing with schema snapshots and response shape validation, along with property-based testing using Hypothesis to ensure the robustness and reliability of the graphql-mcp library.

## Success Criteria
✅ A stored GraphQL schema snapshot is compared on every test run; when the upstream schema drifts (field added/removed/type changed), the test fails with a clear diff  
✅ Response shape contracts validate that upstream responses match expected structure (field presence, nesting, types)  
✅ Pact consumer-driven contract tests generate contract JSON files defining the brick-upstream interaction  
✅ Hypothesis custom strategies generate valid GraphQL queries, malformed queries (invalid syntax, deeply nested, oversized), and random domain model inputs  
✅ Domain model invariant tests verify that QueryResult.error_class is always in {transport, graphql, ok}, TypeInfo fields are consistent, and Subgraph contracts hold  

## Implementation Tasks

### Task 1: Implement GraphQL Schema Snapshot Testing
**Estimated Effort:** 2 hours

#### Implementation Steps:
1. Create schema snapshot test framework:
   - Implement schema introspection snapshot tests
   - Store baseline schema structure
   - Add comparison logic for schema changes
   
2. Integrate with existing schema service:
   - Use existing SchemaService.introspect() method
   - Store schema snapshots in tests/snapshots/
   - Implement diff reporting for schema changes

3. Configure test execution:
   - Run schema snapshot tests as part of test suite
   - Fail tests when breaking schema changes detected
   - Provide clear error messages for schema drift

#### Files to Modify:
- tests/test_contract_schema.py (new file for schema snapshots)
- src/graphql_mcp/domain/schema_service.py (if needed for introspection)

#### Verification:
- Schema snapshot tests pass with current implementation
- Schema changes are detected and reported clearly
- Breaking changes cause test failures

### Task 2: Implement Response Shape Validation
**Estimated Effort:** 2 hours

#### Implementation Steps:
1. Create response shape validators:
   - Implement validators for QueryResult structure
   - Create validators for introspection responses
   - Add validators for entity resolution responses

2. Integrate with existing tests:
   - Add shape validation to key operation tests
   - Implement contract assertions in test helpers
   - Create reusable validation functions

3. Document validation patterns:
   - Create examples of response shape contracts
   - Document validation failure scenarios
   - Provide guidance for adding new validations

#### Files to Modify:
- tests/test_contract_shapes.py (new file for response shape validation)
- tests/conftest.py (add validation helpers)
- src/graphql_mcp/domain/models.py (if needed for validation methods)

#### Verification:
- Response shape tests pass with current implementation
- Invalid response shapes are detected and reported
- Validation failures provide clear error messages

### Task 3: Implement Pact Consumer-Driven Contract Testing
**Estimated Effort:** 3 hours

#### Implementation Steps:
1. Set up Pact testing framework:
   - Configure pact-python integration
   - Create Pact test fixtures
   - Set up mock provider for contract testing

2. Implement key contract tests:
   - Create contract tests for query operations
   - Implement contracts for introspection endpoints
   - Add contracts for entity resolution

3. Generate and publish contracts:
   - Configure contract JSON generation
   - Set up contract publishing (if Pact broker available)
   - Document contract verification process

#### Files to Modify:
- tests/test_contract_pact.py (new file for Pact tests)
- tests/conftest.py (add Pact fixtures)
- pyproject.toml (already added pact-python dependency)

#### Verification:
- Pact tests pass with current implementation
- Contract JSON files are generated correctly
- Contract verification works as expected

### Task 4: Implement Hypothesis Property-Based Testing
**Estimated Effort:** 4 hours

#### Implementation Steps:
1. Set up Hypothesis framework:
   - Configure hypothesis integration
   - Create custom strategies for GraphQL elements
   - Implement strategy composition patterns

2. Create property tests for core functionality:
   - Implement property tests for query operations
   - Add property tests for error handling paths
   - Create tests for domain model invariants

3. Implement fuzz testing for edge cases:
   - Generate malformed queries to test error paths
   - Create oversized payloads to test limits
   - Test boundary conditions with random inputs

#### Files to Modify:
- tests/test_property_queries.py (new file for query property tests)
- tests/test_property_errors.py (new file for error property tests)
- tests/test_property_invariants.py (new file for invariant tests)
- tests/conftest.py (add Hypothesis strategies)

#### Verification:
- Property tests pass with current implementation
- Edge cases are handled gracefully
- Invariant properties hold under random inputs

### Task 5: Documentation and Examples
**Estimated Effort:** 1 hour

#### Implementation Steps:
1. Update README with contract and property testing documentation:
   - How to run contract tests locally
   - How to interpret contract test failures
   - How to run property-based tests

2. Create developer documentation:
   - Best practices for writing contract tests
   - Guidelines for property-based testing
   - Troubleshooting common issues

3. Add examples to documentation:
   - Sample contract test cases
   - Example property-based test patterns
   - Common testing scenarios

#### Files to Modify:
- README.md (add testing documentation)
- docs/testing.md (update with contract and property testing)

#### Verification:
- Review documentation for accuracy and completeness
- Confirm examples work as described
- Validate documentation is clear and actionable

## Dependencies
- Phase 14 (Coverage & Snapshot Infrastructure) should be complete
- Existing test suite must be stable
- CI infrastructure must be operational

## Risks and Mitigations

### Risk 1: Schema snapshot tests become brittle
**Mitigation:** Focus on stable parts of schema and use appropriate snapshot granularity

### Risk 2: Pact tests require external dependencies
**Mitigation:** Use mock providers and make tests work offline

### Risk 3: Property tests are slow or non-deterministic
**Mitigation:** Set appropriate example counts and use health checks

### Risk 4: Contract tests fail due to upstream changes
**Mitigation:** Provide clear guidance on how to update contracts

## Timeline
**Total Estimated Effort:** 12 hours

- Task 1 (Schema Snapshots): 2 days
- Task 2 (Response Shapes): 2 days
- Task 3 (Pact Contracts): 3 days
- Task 4 (Property Tests): 4 days
- Task 5 (Documentation): 1 day

## Acceptance Tests

### Contract Tests:
1. Run schema snapshot tests and verify:
   - Current schema is captured correctly
   - Schema changes are detected
   - Breaking changes cause test failures

2. Run response shape tests and verify:
   - Response structures are validated
   - Invalid shapes are rejected
   - Error messages are clear

3. Run Pact tests and verify:
   - Contract files are generated
   - Provider verification works
   - Interactions are properly defined

### Property Tests:
1. Run property-based tests and verify:
   - Hypothesis strategies generate valid inputs
   - Properties hold under random testing
   - Edge cases are handled properly

2. Run fuzz tests and verify:
   - Malformed inputs are handled gracefully
   - Error paths are exercised
   - No crashes or unhandled exceptions

3. Run invariant tests and verify:
   - Domain model contracts hold
   - Error class values are valid
   - Data structures remain consistent