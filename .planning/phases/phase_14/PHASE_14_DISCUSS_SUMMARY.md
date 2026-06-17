# Phase 14: Coverage & Snapshot Infrastructure — Discussion Summary

**Status**: Discussion Complete

## Overview

Phase 14 focuses on implementing comprehensive coverage reporting and snapshot testing infrastructure for the graphql-mcp project. This phase addresses requirements COV-01, COV-02, COV-03, SNAP-01, SNAP-02, and SNAP-03 from the REQUIREMENTS.md document.

## Key Requirements

### Coverage Requirements
1. **COV-01**: Enforce branch coverage with 85% minimum threshold via pytest-cov
2. **COV-02**: Per-module coverage reports for domain/, adapters/, and ports/ packages
3. **COV-03**: Automated coverage badge in README updated from CI results

### Snapshot Requirements
1. **SNAP-01**: Response snapshot testing with pytest-syrupy and clear diff output
2. **SNAP-02**: Schema introspection snapshot tests for regression detection
3. **SNAP-03**: Error response snapshots for all three error classes (transport, graphql, schema_unavailable)

## Technical Approach

### Coverage Implementation
- Configure pytest-cov in pyproject.toml for branch coverage and threshold enforcement
- Set up per-module coverage reporting for the hexagonal architecture components
- Integrate coverage reporting into GitHub Actions CI workflow
- Add coverage badge to README.md

### Snapshot Testing Implementation
- Add pytest-syrupy to development dependencies
- Create snapshot tests for schema introspection results
- Implement error response snapshots for all error classes
- Establish snapshot update workflow and storage conventions

## Project Context

The graphql-mcp project follows a hexagonal architecture with:
- **Domain layer** (`src/graphql_mcp/domain/`): Pure business logic with zero I/O dependencies
- **Ports layer** (`src/graphql_mcp/ports/`): Protocol interfaces for transport and schema sources
- **Adapters layer** (`src/graphql_mcp/adapters/`): Implementation of inbound/outbound adapters

The project has an established test suite with 341 tests across 39+ test files that will benefit from coverage measurement and snapshot testing.

## Next Steps

1. Configure pytest-cov for branch coverage and per-module reporting
2. Add pytest-syrupy dependency and implement snapshot testing framework
3. Update CI workflow to include coverage reporting and badge generation
4. Create initial coverage baseline and snapshot tests
5. Verify all success criteria from ROADMAP.md

This phase lays the foundation for comprehensive quality assurance in subsequent phases, particularly Phase 16 which implements mutation testing and CI quality gates.