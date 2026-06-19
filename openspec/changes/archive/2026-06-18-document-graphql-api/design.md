## Context

The GraphQL MCP service currently exposes a comprehensive REST API for team sharing and Kubernetes deployments but lacks formal API documentation. Developers must reverse-engineer endpoints from the source code, leading to inefficiencies and potential errors. This design addresses the need for structured API documentation to improve developer experience and enable better tooling integration.

The service already implements all required endpoints in the FastAPI framework, making it straightforward to extract and document the API contract.

## Goals / Non-Goals

**Goals:**
- Create comprehensive OpenAPI 3.0 specification for all REST API endpoints
- Enable integration with API documentation tools like Swagger UI and Postman
- Provide machine-readable API contract for testing and validation
- Enable automatic client SDK generation
- Improve developer onboarding experience

**Non-Goals:**
- Modify existing API endpoints or their behavior
- Change authentication or authorization mechanisms
- Add new API endpoints
- Update implementation code

## Decisions

### Decision: Use OpenAPI 3.0 Specification Format
**Rationale**: OpenAPI 3.0 is the industry standard for REST API documentation, offering broad tooling support and comprehensive feature set for describing modern APIs.

**Alternatives Considered**:
- GraphQL Schema Definition Language - Not applicable as we're documenting REST endpoints
- API Blueprint - Less popular and tooling support compared to OpenAPI
- RAML - Limited tooling ecosystem compared to OpenAPI

### Decision: Structure Documentation in Dedicated openapi/ Directory
**Rationale**: Organizing API documentation in a dedicated directory improves project structure and makes it easy to locate and maintain.

**Alternatives Considered**:
- docs/ directory - Too general for specific API specification files
- root directory - Would clutter the project root with multiple files

### Decision: Provide Both YAML and JSON Formats
**Rationale**: Different tools have preferences for either YAML (human-readable) or JSON (machine-readable) formats, so providing both maximizes compatibility.

**Alternatives Considered**:
- Single format only - Would limit tool compatibility

### Decision: Include Validation and Conversion Tools
**Rationale**: Providing validation and conversion tools ensures the specification remains accurate and can be easily maintained.

**Alternatives Considered**:
- Manual validation only - Error-prone and time-consuming

## Risks / Trade-offs

**[Risk] API specification drift** → **Mitigation**: Include validation tools and establish process for updating specification when API changes

**[Risk] Incomplete endpoint coverage** → **Mitigation**: Systematically review all REST endpoints in the source code and verify against specification

**[Risk] Outdated documentation** → **Mitigation**: Include specification validation in CI/CD pipeline and link to specification from main README

## Migration Plan

1. Create openapi/ directory structure
2. Generate initial OpenAPI specification from existing endpoints
3. Validate specification with provided tools
4. Update main README to reference API documentation
5. Document process for maintaining specification accuracy
6. No deployment steps required as this is documentation-only

## Open Questions

- Should the OpenAPI specification be automatically generated from the FastAPI application code?
- How frequently should the specification be validated against the actual implementation?