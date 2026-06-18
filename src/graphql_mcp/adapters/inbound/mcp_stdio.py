"""MCP stdio inbound adapter — exposes GraphQLClient operations as MCP tools.

Run: python -m graphql_mcp.adapters.inbound.mcp_stdio
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.domain.errors import MutationGuardError, SchemaResolutionError

mcp = FastMCP("graphql-mcp")

_client: GraphQLClient | None = None


def _get_client() -> GraphQLClient:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = GraphQLClient.from_env()
    return _client


@mcp.tool()
def query(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query and return typed result."""
    client = _get_client()
    try:
        result = client.query(query, variables)
    except MutationGuardError as exc:
        return {"error": str(exc), "error_class": "mutation_blocked"}
    return result.model_dump()


@mcp.tool()
def raw(body: dict) -> dict:
    """Send an arbitrary GraphQL POST body and return typed result."""
    client = _get_client()
    try:
        result = client.raw(body)
    except MutationGuardError as exc:
        return {"error": str(exc), "error_class": "mutation_blocked"}
    return result.model_dump()


@mcp.tool()
def introspect() -> dict:
    """Return a summary of Query fields and types from the active schema."""
    client = _get_client()
    try:
        summary = client.introspect()
    except SchemaResolutionError as exc:
        return {"error": str(exc), "error_class": "schema_unavailable"}
    return summary.model_dump()


@mcp.tool()
def describe_type(name: str) -> dict | None:
    """Return field/arg details for a named type, with federation subgraph if available."""
    client = _get_client()
    try:
        info = client.describe_type(name)
    except SchemaResolutionError as exc:
        return {"error": str(exc), "error_class": "schema_unavailable"}
    return info.model_dump() if info else None


@mcp.tool()
def list_subgraphs() -> list[dict] | dict:
    """Return subgraph metadata parsed from supergraph SDL."""
    client = _get_client()
    try:
        return [s.model_dump() for s in client.list_subgraphs()]
    except SchemaResolutionError as exc:
        return {"error": str(exc), "error_class": "schema_unavailable"}


@mcp.tool()
def entities(representations: list[dict]) -> dict:
    """Resolve federation entities via _entities(representations:) pass-through."""
    client = _get_client()
    result = client.entities(representations)
    return result.model_dump()


@mcp.tool()
def refresh_schema() -> dict:
    """Clear schema cache, forcing next access to re-fetch."""
    client = _get_client()
    client.refresh_schema()
    return {"status": "refreshed"}


@mcp.tool()
def subscribe(query: str, variables: dict | None = None) -> dict:
    """Subscribe to a GraphQL subscription and return stream of results.

    Returns a stream of results where each result has data, errors, and error_class.
    """
    try:
        from graphql_mcp import GraphQLClient
    except ImportError:
        return {
            "error": "websockets is required for subscription support. Install with: pip install graphql-mcp[subscriptions]"
        }

    client = _get_client()
    try:
        # For MCP, we'll collect a few results and return them as a list
        # In a real implementation, this would be a streaming response
        results = []
        count = 0
        for result in client.subscribe(query, variables):
            results.append(result.model_dump())
            count += 1
            # Limit to first 10 results for MCP tool call
            if count >= 10:
                break
        return {"results": results, "truncated": count >= 10}
    except Exception as exc:
        return {"error": str(exc), "error_class": "subscription_error"}


if __name__ == "__main__":
    mcp.run(transport="stdio")
