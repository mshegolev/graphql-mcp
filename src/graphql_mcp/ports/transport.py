from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from graphql_mcp.domain.models import QueryResult


@runtime_checkable
class GraphQLTransport(Protocol):
    """Port: executes a GraphQL query against a remote endpoint."""

    def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> QueryResult:
        """Send query + variables, return typed result with error_class."""
        ...

    def post_raw(self, body: dict[str, Any]) -> QueryResult:
        """Send arbitrary POST body, return typed result."""
        ...
