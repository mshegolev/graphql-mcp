#!/usr/bin/env python3
"""Basic synchronous GraphQL query using graphql-mcp.

This example demonstrates the library-first approach: import GraphQLClient,
configure via environment variables, and execute queries with typed results.

Setup:
    pip install graphql-mcp

Environment variables:
    GRAPHQL_ENDPOINT    URL of your GraphQL endpoint (required)
    GRAPHQL_BEARER_TOKEN  Optional Bearer token for authentication

Usage:
    export GRAPHQL_ENDPOINT=https://countries.trevorblades.com/graphql
    python examples/basic_query.py
"""

from __future__ import annotations

from graphql_mcp import GraphQLClient


def main() -> None:
    # Create client from environment variables (reads GRAPHQL_* env vars)
    with GraphQLClient.from_env() as client:
        # ---- 1. Execute a simple query ----
        result = client.query("""
            query {
                countries {
                    code
                    name
                    emoji
                }
            }
        """)

        # Check the three-class error typing
        print(f"Error class: {result.error_class.value}")  # ok | graphql | transport

        if result.data:
            countries = result.data.get("countries", [])
            print(f"\nFound {len(countries)} countries. First 5:")
            for country in countries[:5]:
                print(f"  {country['emoji']} {country['name']} ({country['code']})")

        if result.errors:
            print(f"\nGraphQL errors: {result.errors}")

        # ---- 2. Query with variables ----
        result = client.query(
            query="""
                query GetCountry($code: ID!) {
                    country(code: $code) {
                        name
                        capital
                        currency
                        languages { name }
                    }
                }
            """,
            variables={"code": "US"},
        )

        if result.data and result.data.get("country"):
            country = result.data["country"]
            print(f"\n{country['name']}:")
            print(f"  Capital: {country['capital']}")
            print(f"  Currency: {country['currency']}")
            langs = [lang["name"] for lang in country.get("languages", [])]
            print(f"  Languages: {', '.join(langs)}")

        # ---- 3. Schema introspection ----
        try:
            summary = client.introspect()
            print(f"\nSchema has {len(summary.query_fields)} query fields:")
            for field_name in summary.query_fields[:10]:
                print(f"  - {field_name}")
            print(f"\nSchema has {len(summary.types)} types:")
            for t in summary.types[:5]:
                print(f"  - {t.name} ({t.kind})")
        except Exception as e:
            print(f"\nIntrospection not available: {e}")


if __name__ == "__main__":
    main()
