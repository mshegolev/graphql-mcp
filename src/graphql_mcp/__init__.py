"""graphql-mcp: Generic read-only GraphQL MCP brick."""

from graphql_mcp.adapters.inbound.async_lib import AsyncGraphQLClient
from graphql_mcp.adapters.inbound.lib import GraphQLClient

__all__ = ["AsyncGraphQLClient", "GraphQLClient"]
