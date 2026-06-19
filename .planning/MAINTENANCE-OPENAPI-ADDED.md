# Maintenance Task: OpenAPI Specification Added

**Date**: 2026-06-18
**Author**: Assistant
**Task**: Add OpenAPI specification to document REST API endpoints

## Summary

Added comprehensive OpenAPI 3.0 specification for the GraphQL MCP service REST API endpoints. This enhancement provides standardized API documentation that can be used with various tools for testing, documentation, and client SDK generation.

## Changes Made

1. **Created `openapi/` directory** with the following files:
   - `openapi.yaml` - Main OpenAPI specification in YAML format
   - `openapi.json` - OpenAPI specification in JSON format
   - `README.md` - Documentation for the OpenAPI specification

2. **Documented all REST API endpoints**:
   - Health checks (`/health`, `/ready`)
   - GraphQL operations (`/graphql/query`, `/graphql/raw`, `/graphql/entities`)
   - Schema management (`/graphql/introspect`, `/graphql/type/{typeName}`, `/graphql/refresh`)
   - Federation operations (`/graphql/subgraphs`)
   - Subscription support (`/graphql/subscribe` via SSE and WebSocket)
   - MCP transport (`/mcp`)

3. **Updated main README.md** to reference the new OpenAPI documentation

## Benefits

- Standardized API documentation using OpenAPI 3.0 specification
- Enables use of Swagger UI, Postman, and other API tools
- Facilitates client SDK generation
- Improves developer experience with comprehensive endpoint documentation
- Provides machine-readable API contract for testing and validation

## Files Created

```
openapi/
├── README.md
├── openapi.yaml
└── openapi.json
```

## Validation

The OpenAPI specification has been validated and includes:
- Complete endpoint definitions with request/response schemas
- Proper HTTP status codes and error responses
- Security scheme definitions
- Comprehensive data models
- Example values for better understanding