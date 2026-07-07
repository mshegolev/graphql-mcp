"""generic-graphql-mcp: Generic read-only GraphQL MCP brick."""

from generic_graphql_mcp.adapters.inbound.async_lib import AsyncGraphQLClient
from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient

__all__ = ["AsyncGraphQLClient", "GraphQLClient"]
