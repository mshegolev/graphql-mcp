# generic-graphql-mcp-api Specification

## Purpose
This specification defines the requirements for documenting the GraphQL MCP REST API. The GraphQL MCP service exposes a comprehensive REST API for team sharing and Kubernetes deployments. This specification ensures that all endpoints are properly documented with OpenAPI 3.0 to improve developer experience and enable better tooling integration.
## Requirements
### Requirement: GraphQL MCP REST API Specification
The system SHALL provide a complete OpenAPI 3.0 specification documenting all REST API endpoints exposed by the GraphQL MCP service.

#### Scenario: API specification available
- **WHEN** developer accesses the OpenAPI specification
- **THEN** complete documentation for all REST endpoints is provided including health checks, GraphQL operations, schema management, federation support, and subscription capabilities

### Requirement: Health Check Endpoint Documentation
The system SHALL document the health check endpoints including /health and /ready with their request/response schemas.

#### Scenario: Health endpoint documented
- **WHEN** developer views API documentation for health endpoints
- **THEN** complete specification including request methods, response codes, and response schemas is provided

#### Scenario: Readiness endpoint documented
- **WHEN** developer views API documentation for readiness endpoint
- **THEN** complete specification including request methods, response codes, and response schemas is provided

### Requirement: GraphQL Operations Documentation
The system SHALL document all GraphQL operation endpoints including query, raw, and entities operations with their request/response schemas.

#### Scenario: Query endpoint documented
- **WHEN** developer views API documentation for GraphQL query endpoint
- **THEN** complete specification including request body schema, response schema, and error responses is provided

#### Scenario: Raw endpoint documented
- **WHEN** developer views API documentation for GraphQL raw endpoint
- **THEN** complete specification including request body schema, response schema, and error responses is provided

#### Scenario: Entities endpoint documented
- **WHEN** developer views API documentation for GraphQL entities endpoint
- **THEN** complete specification including request body schema, response schema, and error responses is provided

### Requirement: Schema Management Documentation
The system SHALL document all schema management endpoints including introspect, type description, and refresh operations.

#### Scenario: Introspect endpoint documented
- **WHEN** developer views API documentation for schema introspect endpoint
- **THEN** complete specification including response schema is provided

#### Scenario: Type description endpoint documented
- **WHEN** developer views API documentation for type description endpoint
- **THEN** complete specification including path parameters, response schema, and error responses is provided

#### Scenario: Refresh endpoint documented
- **WHEN** developer views API documentation for schema refresh endpoint
- **THEN** complete specification including response schema is provided

### Requirement: Federation Operations Documentation
The system SHALL document all federation-related endpoints including subgraphs listing.

#### Scenario: Subgraphs endpoint documented
- **WHEN** developer views API documentation for subgraphs endpoint
- **THEN** complete specification including response schema is provided

### Requirement: Subscription Documentation
The system SHALL document all subscription endpoints including both SSE and WebSocket implementations.

#### Scenario: SSE subscription endpoint documented
- **WHEN** developer views API documentation for SSE subscription endpoint
- **THEN** complete specification including query parameters, response format, and error responses is provided

#### Scenario: WebSocket subscription endpoint documented
- **WHEN** developer views API documentation for WebSocket subscription endpoint
- **THEN** complete specification including connection protocol and message formats is provided

### Requirement: MCP Transport Documentation
The system SHALL document the MCP-over-HTTP transport endpoint.

#### Scenario: MCP endpoint documented
- **WHEN** developer views API documentation for MCP transport endpoint
- **THEN** complete specification including request/response schemas is provided

### Requirement: Security Documentation
The system SHALL document the security requirements including authentication and authorization mechanisms.

#### Scenario: Security requirements documented
- **WHEN** developer views API documentation
- **THEN** complete specification of security schemes and authentication requirements is provided

### Requirement: Error Response Documentation
The system SHALL document all standard error response formats used by the API.

#### Scenario: Error responses documented
- **WHEN** developer views API documentation
- **THEN** complete specification of error response schemas and status codes is provided

