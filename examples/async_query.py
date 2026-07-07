#!/usr/bin/env python3
"""Async GraphQL queries using generic-graphql-mcp.

This example demonstrates the async client for use with asyncio,
FastAPI, or any async Python application.

Setup:
    pip install generic-graphql-mcp

Environment variables:
    GRAPHQL_ENDPOINT    URL of your GraphQL endpoint (required)
    GRAPHQL_BEARER_TOKEN  Optional Bearer token for authentication

Usage:
    export GRAPHQL_ENDPOINT=https://countries.trevorblades.com/graphql
    python examples/async_query.py
"""

from __future__ import annotations

import asyncio

from generic_graphql_mcp import AsyncGraphQLClient


async def main() -> None:
    # Create async client from environment variables
    async with AsyncGraphQLClient.from_env() as client:
        # ---- 1. Simple async query ----
        result = await client.query("""
            query {
                continents {
                    code
                    name
                }
            }
        """)

        print(f"Error class: {result.error_class.value}")

        if result.data:
            continents = result.data.get("continents", [])
            print(f"\nContinents ({len(continents)}):")
            for continent in continents:
                print(f"  - {continent['name']} ({continent['code']})")

        # ---- 2. Parallel queries with asyncio.gather ----
        # The async client excels at concurrent requests
        queries = [
            client.query(
                "query($code: ID!) { continent(code: $code) { name countries { name } } }",
                variables={"code": code},
            )
            for code in ["EU", "NA", "AS"]
        ]

        results = await asyncio.gather(*queries)

        print("\nParallel query results:")
        for r in results:
            if r.data and r.data.get("continent"):
                continent = r.data["continent"]
                country_count = len(continent.get("countries", []))
                print(f"  {continent['name']}: {country_count} countries")

        # ---- 3. Raw query passthrough ----
        raw_result = await client.raw(
            {
                "query": "{ __typename }",
            }
        )
        print(f"\nRaw query result: {raw_result.data}")
        print(f"Error class: {raw_result.error_class.value}")


if __name__ == "__main__":
    asyncio.run(main())
