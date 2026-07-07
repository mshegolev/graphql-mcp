#!/usr/bin/env python3
"""GraphQL subscription streaming using generic-graphql-mcp.

This example demonstrates real-time subscription support via the async
client's subscribe() method. Events are streamed over WebSocket using
the graphql-transport-ws sub-protocol.

Setup:
    pip install 'generic-graphql-mcp[subscriptions]'

Environment variables:
    GRAPHQL_ENDPOINT             HTTP endpoint (used for schema + ws:// derivation)
    GRAPHQL_SUBSCRIPTION_ENDPOINT  Optional explicit WebSocket endpoint
                                   (defaults to ws:// version of GRAPHQL_ENDPOINT)

Usage:
    export GRAPHQL_ENDPOINT=http://localhost:4000/graphql
    python examples/subscription.py

Note:
    This example requires a GraphQL server that supports subscriptions
    via the graphql-transport-ws WebSocket sub-protocol. The subscribe()
    method automatically handles:
    - WebSocket connection lifecycle (connection_init → subscribe → complete)
    - Backpressure via bounded async queue
    - Clean shutdown on iteration exit or server complete
"""

from __future__ import annotations

import asyncio

from generic_graphql_mcp import AsyncGraphQLClient


async def main() -> None:
    async with AsyncGraphQLClient.from_env() as client:
        print("Subscribing to events (Ctrl+C to stop)...\n")

        # subscribe() returns an AsyncIterator[QueryResult]
        # Each yielded result has .data, .errors, and .error_class
        subscription_query = """
            subscription {
                events {
                    id
                    type
                    payload
                    timestamp
                }
            }
        """

        try:
            event_count = 0
            async for result in client.subscribe(subscription_query):
                event_count += 1

                if result.error_class.value != "ok":
                    print(f"  Error ({result.error_class.value}): {result.errors}")
                    continue

                if result.data:
                    event = result.data.get("events", {})
                    print(f"  Event #{event_count}: {event}")

                # Example: stop after 10 events
                if event_count >= 10:
                    print(f"\nReceived {event_count} events, stopping.")
                    break

        except KeyboardInterrupt:
            print(f"\nStopped after {event_count} events.")

        # ---- Subscription with variables ----
        print("\nSubscription with variables (filtered):")
        try:
            async for result in client.subscribe(
                query="""
                    subscription FilteredEvents($type: String!) {
                        events(type: $type) {
                            id
                            payload
                        }
                    }
                """,
                variables={"type": "user_action"},
            ):
                if result.data:
                    print(f"  Filtered event: {result.data}")
                    break  # Just show one for the example

        except Exception as e:
            print(f"  Subscription error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
