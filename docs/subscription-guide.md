# GraphQL MCP Subscription Guide

This guide explains how to use GraphQL subscriptions with the generic-graphql-mcp library, covering all supported transports and client interfaces.

## Overview

GraphQL MCP now supports real-time subscriptions through two transport mechanisms:

1. **Server-Sent Events (SSE)** - HTTP-based fallback for environments where WebSockets are not available
2. **WebSocket** - Full-duplex communication using the graphql-transport-ws sub-protocol

Both transports are supported across all client interfaces:
- Library (Python)
- REST API
- MCP stdio
- CLI

## Library Usage

### Synchronous Client

```python
from generic_graphql_mcp import GraphQLClient

client = GraphQLClient.from_env()

# Subscribe to events using a for loop
for result in client.subscribe("subscription { events { id type payload } }"):
    if result.error_class.value != "ok":
        print(f"Error: {result.errors}")
        break
    
    if result.data:
        print(f"Event received: {result.data}")
        
    # Process a limited number of events
    # (in a real application, you might have a break condition)
```

### Asynchronous Client

```python
from generic_graphql_mcp import AsyncGraphQLClient

async with AsyncGraphQLClient.from_env() as client:
    # Subscribe to events using async for
    async for result in client.subscribe("subscription { events { id type payload } }"):
        if result.error_class.value != "ok":
            print(f"Error: {result.errors}")
            break
            
        if result.data:
            print(f"Event received: {result.data}")
            
        # Process a limited number of events
```

### With Variables

```python
# Synchronous
for result in client.subscribe(
    "subscription FilteredEvents($eventType: String!) { events(type: $eventType) { id payload } }",
    variables={"eventType": "user_action"}
):
    # Process results...

# Asynchronous
async for result in client.subscribe(
    "subscription FilteredEvents($eventType: String!) { events(type: $eventType) { id payload } }",
    variables={"eventType": "user_action"}
):
    # Process results...
```

## REST API Usage

### Server-Sent Events (SSE)

```bash
# Simple subscription
curl "http://localhost:8000/graphql/subscribe?query=subscription%20%7B%20events%20%7B%20id%20type%20payload%20%7D%20%7D"

# With variables (URL-encoded JSON)
curl "http://localhost:8000/graphql/subscribe?query=subscription%20FilteredEvents(%24eventType%3A%20String!)%20%7B%20events(type%3A%20%24eventType)%20%7B%20id%20payload%20%7D%20%7D&variables=%7B%22eventType%22%3A%20%22user_action%22%7D"
```

### WebSocket

The WebSocket endpoint uses the standard graphql-transport-ws sub-protocol:

1. Connect to `ws://localhost:8000/graphql/subscribe`
2. Send `connection_init` message
3. Receive `connection_ack` message
4. Send `subscribe` message with your subscription query
5. Receive `next` messages with subscription results
6. Receive `complete` message when subscription ends

Example using Python websockets library:

```python
import asyncio
import json
import websockets

async def subscribe_to_events():
    uri = "ws://localhost:8000/graphql/subscribe"
    async with websockets.connect(uri, subprotocols=["graphql-transport-ws"]) as websocket:
        # Initialize connection
        await websocket.send(json.dumps({"type": "connection_init"}))
        response = await websocket.recv()
        print(f"Server: {response}")
        
        # Subscribe to events
        subscribe_message = {
            "type": "subscribe",
            "id": "1",
            "payload": {
                "query": "subscription { events { id type payload } }"
            }
        }
        await websocket.send(json.dumps(subscribe_message))
        
        # Listen for events
        try:
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Event: {data}")
                
                if data.get("type") == "complete":
                    break
        except websockets.exceptions.ConnectionClosed:
            pass

# Run the subscription
asyncio.run(subscribe_to_events())
```

## MCP Usage

### MCP stdio

When using the MCP stdio adapter, the `subscribe` tool is available:

```bash
python -m generic_graphql_mcp.adapters.inbound.mcp_stdio
```

The tool can be called with a subscription query and optional variables.

### MCP-over-HTTP

The same `subscribe` tool is available through the MCP-over-HTTP transport at `/mcp`.

## CLI Usage

The CLI now includes a `subscribe` command:

```bash
# Install with subscription support
pip install generic-graphql-mcp[subscriptions]

# Subscribe to events
generic-graphql-mcp subscribe 'subscription { events { id type payload } }'

# With variables
generic-graphql-mcp subscribe 'subscription FilteredEvents($eventType: String!) { events(type: $eventType) { id payload } }' --variables '{"eventType": "user_action"}'

# With table formatting
generic-graphql-mcp subscribe 'subscription { events { id type payload } }' --format table
```

## Configuration

Several environment variables control subscription behavior:

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAPHQL_SUBSCRIPTION_ENDPOINT` | Derived from `GRAPHQL_ENDPOINT` | WebSocket endpoint for upstream subscription connections |
| `GRAPHQL_SUBSCRIPTION_QUEUE_SIZE` | `128` | Bounded async queue size for subscription backpressure |
| `GRAPHQL_SUBSCRIPTION_RATE_LIMIT` | `"10/minute"` | Rate limit for subscription connections per IP |
| `GRAPHQL_MAX_CONCURRENT_SUBSCRIPTIONS` | `100` | Maximum concurrent subscription connections per IP |

## Error Handling

Subscription results follow the same error handling patterns as other GraphQL operations:

- `error_class: "ok"` - Successful result with data
- `error_class: "graphql"` - GraphQL errors in the response
- `error_class: "transport"` - Network or connection errors

Always check the `error_class` field before processing data:

```python
for result in client.subscribe("subscription { events { id } }"):
    if result.error_class.value == "ok":
        # Process successful result
        print(result.data)
    elif result.error_class.value == "graphql":
        # Handle GraphQL errors
        print(f"GraphQL errors: {result.errors}")
    elif result.error_class.value == "transport":
        # Handle transport errors
        print(f"Transport error: {result.errors}")
```

## Rate Limiting

Subscription connections are rate-limited to prevent resource exhaustion:

- Connection rate: Limited by `GRAPHQL_SUBSCRIPTION_RATE_LIMIT` (default: 10/minute per IP)
- Concurrent connections: Limited by `GRAPHQL_MAX_CONCURRENT_SUBSCRIPTIONS` (default: 100 per IP)

When rate limits are exceeded, clients receive a 429 status code with a `Retry-After` header.

## Best Practices

1. **Handle disconnections gracefully** - Implement reconnection logic for long-running subscriptions
2. **Limit subscription duration** - Avoid indefinite subscriptions that consume server resources
3. **Use specific filters** - Narrow subscription queries to reduce unnecessary event traffic
4. **Implement backpressure** - Handle bursts of events appropriately in your application
5. **Clean up resources** - Ensure subscription connections are properly closed when no longer needed

## Troubleshooting

### "websockets is required" Error

If you encounter an ImportError about websockets, install the subscriptions extra:

```bash
pip install generic-graphql-mcp[subscriptions]
```

### "No subscription endpoint configured" Error

Ensure either `GRAPHQL_SUBSCRIPTION_ENDPOINT` or `GRAPHQL_ENDPOINT` is set. The subscription endpoint is derived from the GraphQL endpoint by converting http:// to ws:// or https:// to wss://.

### Connection Issues

- Verify the upstream GraphQL service supports subscriptions
- Check that the subscription endpoint is accessible
- Ensure proper authentication headers are sent
- Confirm WebSocket connections are not blocked by firewalls or proxies