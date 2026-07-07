## Why

GraphQL subscriptions provide a way to receive real-time updates from a GraphQL server when specific events occur. While the current GraphQL MCP implementation supports queries and mutations, it lacks subscription support, which is essential for building real-time applications that need to react to server-side events. Adding subscription support would significantly enhance the capabilities of the GraphQL MCP and make it more competitive with other GraphQL clients.

## What Changes

- Add subscription operation support to the GraphQLClient
- Implement both Server-Sent Events (SSE) and WebSocket transport mechanisms for subscriptions
- Add new REST endpoints for subscription management in the FastAPI adapter
- Extend the MCP stdio adapter with subscription tools
- Add CLI commands for managing subscriptions
- Update documentation to cover subscription usage

## Capabilities

### New Capabilities
- `graphql-subscriptions`: Real-time event streaming via GraphQL subscriptions with support for both SSE and WebSocket transports

### Modified Capabilities
- `generic-graphql-mcp-api`: Extend REST API specification to include subscription endpoints

## Impact

- New code will be added to handle subscription connections and event streaming
- The HttpTransport will need to be extended to support persistent connections
- New dependencies may be required for WebSocket support
- The FastAPI adapter will need new endpoints for subscription handling
- The MCP stdio adapter will need new tools for subscription operations
- CLI commands will need to be added for subscription management
- Documentation will need to be updated to cover subscription usage