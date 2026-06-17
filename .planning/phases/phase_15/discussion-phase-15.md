# Phase 15 Discussion: Contract & Property-Based Testing

## Context

This phase focuses on implementing contract testing and property-based testing for the graphql-mcp project to ensure robustness and reliability:

1. Contract testing with schema snapshots and response shape validation
2. Property-based testing with Hypothesis for comprehensive input validation

## Requirements Analysis

From REQUIREMENTS.md, the specific requirements for this phase are:

### Contract Testing Requirements (CTR-01, CTR-02, CTR-03)
- GraphQL schema snapshots are stored and compared on test run; breaking upstream schema changes are detected automatically
- Response shape contracts validate that upstream responses match expected structure beyond basic type checks
- Pact consumer-driven contract tests define brick-upstream contracts and can publish to a Pact broker

### Property-Based Testing Requirements (PROP-01, PROP-02, PROP-03)
- Hypothesis custom strategies generate valid and edge-case GraphQL queries, variables dicts, and mock response shapes
- Fuzz tests generate malformed queries (invalid syntax, deeply nested, oversized), invalid JSON payloads, and boundary-case variables to exercise error handling paths
- Domain model invariant tests verify QueryResult, TypeInfo, and Subgraph dataclass contracts hold under random input

## Current State Assessment

Based on codebase inspection:
- Project uses pytest for testing with extensive test coverage (341 tests mentioned in PROJECT.md)
- No existing contract testing infrastructure implemented
- No property-based testing with Hypothesis currently implemented
- Existing test suite focuses on example-based testing

## Technical Approach

### Contract Testing Implementation
1. Implement GraphQL schema snapshot testing:
   - Store current schema structure as reference
   - Compare schema on each test run to detect breaking changes
   - Use existing schema introspection functionality
   
2. Implement response shape validation:
   - Create validators for expected response structures
   - Add assertions to verify response shape contracts
   - Focus on critical API endpoints (query, introspect, entities)

3. Implement Pact consumer-driven contract testing:
   - Add pact-python as development dependency
   - Create consumer contract tests for key interactions
   - Generate and publish contract files

### Property-Based Testing Implementation
1. Add Hypothesis testing framework:
   - Add hypothesis to development dependencies
   - Create custom strategies for GraphQL queries and variables
   - Implement property-based tests for core functionality

2. Implement fuzz testing for error handling:
   - Generate malformed queries to test error paths
   - Create oversized payloads to test limits
   - Test boundary conditions with random inputs

3. Implement domain model invariant testing:
   - Create property tests for QueryResult, TypeInfo, and Subgraph
   - Verify dataclass contracts hold under random input
   - Ensure error_class always has valid values

## Dependencies

This phase depends on:
- Completion of Phase 14 (Coverage & Snapshot Infrastructure)
- Stable codebase with existing test suite
- CI infrastructure already in place

## Success Criteria

As defined in ROADMAP.md:
1. A stored GraphQL schema snapshot is compared on every test run; when the upstream schema drifts (field added/removed/type changed), the test fails with a clear diff
2. Response shape contracts validate that upstream responses match expected structure (field presence, nesting, types)
3. Pact consumer-driven contract tests generate contract JSON files defining the brick-upstream interaction
4. Hypothesis custom strategies generate valid GraphQL queries, malformed queries (invalid syntax, deeply nested, oversized), and random domain model inputs
5. Domain model invariant tests verify that QueryResult.error_class is always in {transport, graphql, ok}, TypeInfo fields are consistent, and Subgraph contracts hold