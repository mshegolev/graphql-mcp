# GraphQL MCP OpenAPI Specification

This directory contains the OpenAPI 3.0 specification for the GraphQL MCP service.

## Files

- `openapi.yaml` - The main OpenAPI specification in YAML format
- `openapi.json` - The OpenAPI specification in JSON format (generated)

## Overview

The GraphQL MCP service exposes a REST API for team sharing and Kubernetes deployments. The API provides access to all core GraphQL operations including:

- Query execution
- Schema introspection
- Type description
- Federation entity resolution
- Subscription support (WebSocket and SSE)

## Endpoints

The API includes the following endpoint categories:

1. **Health Checks**
   - `GET /health` - Service health check
   - `GET /ready` - Service readiness check

2. **GraphQL Operations**
   - `POST /graphql/query` - Execute GraphQL queries
   - `POST /graphql/raw` - Execute raw GraphQL operations
   - `POST /graphql/entities` - Resolve federation entities

3. **Schema Management**
   - `GET /graphql/introspect` - Introspect the schema
   - `GET /graphql/type/{typeName}` - Describe a specific type
   - `POST /graphql/refresh` - Refresh the schema cache

4. **Federation**
   - `GET /graphql/subgraphs` - List federation subgraphs

5. **Subscriptions**
   - `GET /graphql/subscribe` - Subscribe via Server-Sent Events
   - `WebSocket /graphql/subscribe` - Subscribe via WebSocket

6. **MCP Transport**
   - `POST /mcp` - MCP-over-HTTP transport

## Usage

You can use this OpenAPI specification with any OpenAPI-compatible tool:

- **Swagger UI** - For interactive API documentation
- **Postman** - For API testing
- **Code generators** - To generate client SDKs
- **API gateways** - For API management and monitoring

## Generating JSON Format

To convert the YAML specification to JSON format:

```bash
# Using yq (install with: npm install -g yq)
yq -o json openapi.yaml > openapi.json

# Using Python PyYAML
python3 -c "import yaml, json; print(json.dumps(yaml.safe_load(open('openapi.yaml'))))"
```