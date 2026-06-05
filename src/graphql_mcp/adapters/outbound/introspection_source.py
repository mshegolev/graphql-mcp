from __future__ import annotations

import logging
from typing import Any

from graphql import build_client_schema, get_introspection_query, print_schema
from graphql.error import GraphQLError

from graphql_mcp.domain.models import SchemaGraph

logger = logging.getLogger(__name__)


class IntrospectionSource:
    """Outbound adapter: live introspection query to resolve schema."""

    def __init__(self, transport: Any) -> None:
        """
        Args:
            transport: An object with execute(query, variables) -> QueryResult.
                       Typically HttpTransport.
        """
        self._transport = transport

    @property
    def name(self) -> str:
        return "introspection"

    def fetch_schema(self) -> SchemaGraph | None:
        query = get_introspection_query(descriptions=True)
        result = self._transport.execute(query)

        if result.error_class.value != "ok" or result.data is None:
            logger.debug("Introspection query failed: error_class=%s", result.error_class)
            return None

        try:
            schema = build_client_schema(result.data)
            sdl_text = print_schema(schema)
        except (GraphQLError, TypeError, KeyError) as exc:
            logger.debug("Introspection schema build failed: %s", exc)
            return None

        return SchemaGraph(sdl=sdl_text, source_name="introspection")
