from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from generic_graphql_mcp.domain.models import SchemaGraph


@runtime_checkable
class SchemaSource(Protocol):
    """Port: a source that can fetch a GraphQL schema."""

    @property
    def name(self) -> str:
        """Human-readable source name for logging."""
        ...

    def fetch_schema(self) -> SchemaGraph | None:
        """Attempt to fetch schema. Return None on failure (not exception)."""
        ...
