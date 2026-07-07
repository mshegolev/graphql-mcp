"""MCP stdio inbound adapter — exposes GraphQLClient operations as MCP tools.

Run: python -m generic_graphql_mcp.adapters.inbound.mcp_stdio

Every tool is read-only and talks to an external GraphQL service, so each is
annotated with ``readOnlyHint``/``openWorldHint``. Tools return their domain
Pydantic models directly, which lets FastMCP derive an ``outputSchema`` and emit
``structuredContent``. Error conditions (a blocked mutation, an unreachable
schema, a failed subscription) are surfaced as MCP tool errors via ``ToolError``
— an ``isError`` result — rather than a success result carrying an error field.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel

from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient
from generic_graphql_mcp.domain.errors import MutationGuardError, SchemaResolutionError

# Runtime imports (not TYPE_CHECKING): FastMCP resolves these return-type
# annotations at runtime to build each tool's outputSchema, and QueryResult is a
# Pydantic field type on SubscriptionBatch.
from generic_graphql_mcp.domain.models import (  # noqa: TC001
    QueryResult,
    SchemaSummary,
    Subgraph,
    TypeInfo,
)

mcp = FastMCP("generic-graphql-mcp")

# Shared annotation: every tool here is read-only and hits an external service.
_READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=True)

_MUTATION_HINT = (
    "This server is read-only; set GRAPHQL_ALLOW_MUTATIONS=true to enable mutations."
)
_SCHEMA_HINT = (
    "Check the endpoint configuration, or call refresh_schema once the source "
    "becomes reachable."
)

_client: GraphQLClient | None = None


def _get_client() -> GraphQLClient:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = GraphQLClient.from_env()
    return _client


class RefreshResult(BaseModel):
    """Result of clearing the schema cache."""

    status: str


class SubscriptionBatch(BaseModel):
    """A bounded batch of subscription results collected for one tool call."""

    results: list[QueryResult]
    truncated: bool


@mcp.tool(annotations=_READ_ONLY)
def query(query: str, variables: dict | None = None) -> QueryResult:
    """Execute a read-only GraphQL query and return a typed result.

    Mutations are rejected unless the server is started with
    GRAPHQL_ALLOW_MUTATIONS=true. The result carries `data`, `errors`, and an
    `error_class` of ok | graphql | transport.
    """
    client = _get_client()
    try:
        return client.query(query, variables)
    except MutationGuardError as exc:
        raise ToolError(f"{exc} {_MUTATION_HINT}") from exc


@mcp.tool(annotations=_READ_ONLY)
def raw(body: dict) -> QueryResult:
    """Send an arbitrary GraphQL POST body and return a typed result.

    If the body contains a `query` string, the mutation guard applies just as it
    does for `query`. Mutations are rejected unless GRAPHQL_ALLOW_MUTATIONS=true.
    """
    client = _get_client()
    try:
        return client.raw(body)
    except MutationGuardError as exc:
        raise ToolError(f"{exc} {_MUTATION_HINT}") from exc


@mcp.tool(annotations=_READ_ONLY)
def introspect() -> SchemaSummary:
    """Return a summary of Query root fields and types from the active schema."""
    client = _get_client()
    try:
        return client.introspect()
    except SchemaResolutionError as exc:
        raise ToolError(f"Schema unavailable: {exc} {_SCHEMA_HINT}") from exc


@mcp.tool(annotations=_READ_ONLY)
def describe_type(name: str) -> TypeInfo | None:
    """Return field/arg details for a named type, with federation subgraph if available.

    Returns null when the named type does not exist in the active schema.
    """
    client = _get_client()
    try:
        return client.describe_type(name)
    except SchemaResolutionError as exc:
        raise ToolError(f"Schema unavailable: {exc} {_SCHEMA_HINT}") from exc


@mcp.tool(annotations=_READ_ONLY)
def list_subgraphs() -> list[Subgraph]:
    """Return federation subgraph metadata parsed from supergraph SDL.

    Returns an empty list when supergraph ownership data is unavailable.
    """
    client = _get_client()
    try:
        return client.list_subgraphs()
    except SchemaResolutionError as exc:
        raise ToolError(f"Schema unavailable: {exc} {_SCHEMA_HINT}") from exc


@mcp.tool(annotations=_READ_ONLY)
def entities(representations: list[dict]) -> QueryResult:
    """Resolve federation entities via the _entities(representations:) query.

    This is a read-only query, so the mutation guard does not apply.
    """
    return _get_client().entities(representations)


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=True, idempotentHint=True, openWorldHint=True
    )
)
def refresh_schema() -> RefreshResult:
    """Clear the schema cache, forcing the next access to re-fetch.

    Idempotent: clearing an already-empty cache has no additional effect.
    """
    _get_client().refresh_schema()
    return RefreshResult(status="refreshed")


@mcp.tool(annotations=_READ_ONLY)
def subscribe(query: str, variables: dict | None = None) -> SubscriptionBatch:
    """Subscribe to a GraphQL subscription and return a bounded batch of results.

    Collects up to the first 10 emitted results (each with `data`, `errors`, and
    `error_class`) and returns them together; `truncated` is true if more results
    were available. Requires the [subscriptions] extra.
    """
    client = _get_client()
    try:
        results: list[QueryResult] = []
        for result in client.subscribe(query, variables):
            results.append(result)
            if len(results) >= 10:
                return SubscriptionBatch(results=results, truncated=True)
        return SubscriptionBatch(results=results, truncated=False)
    except ImportError as exc:
        raise ToolError(
            "websockets is required for subscription support. Install with: "
            "pip install generic-graphql-mcp[subscriptions]"
        ) from exc
    except ToolError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface any transport/runtime failure
        raise ToolError(f"Subscription failed: {exc}") from exc


if __name__ == "__main__":
    mcp.run(transport="stdio")
