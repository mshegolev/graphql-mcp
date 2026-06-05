from __future__ import annotations

from typing import Protocol, runtime_checkable

from graphql_mcp.domain.models import SchemaGraph


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
