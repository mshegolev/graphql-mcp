from __future__ import annotations

import logging
from typing import Any

from graphql import build_schema
from graphql.error import GraphQLError

from graphql_mcp.domain.models import SchemaGraph

logger = logging.getLogger(__name__)

FEDERATION_SDL_QUERY = "query { _service { sdl } }"


class ServiceSdlSource:
    """Outbound adapter: fetch SDL via federation _service{sdl} query."""

    def __init__(self, transport: Any) -> None:
        """
        Args:
            transport: An object with execute(query) -> QueryResult.
        """
        self._transport = transport

    @property
    def name(self) -> str:
        return "federation_service_sdl"

    def fetch_schema(self) -> SchemaGraph | None:
        result = self._transport.execute(FEDERATION_SDL_QUERY)

        if result.error_class.value != "ok" or result.data is None:
            logger.debug("_service{sdl} query failed: error_class=%s", result.error_class)
            return None

        try:
            sdl_text = result.data["_service"]["sdl"]
        except (KeyError, TypeError) as exc:
            logger.debug("_service{sdl} response missing sdl field: %s", exc)
            return None

        if not sdl_text:
            logger.debug("_service{sdl} returned empty SDL")
            return None

        try:
            build_schema(sdl_text)  # validate
        except GraphQLError as exc:
            logger.debug("_service SDL parse failed: %s", exc)
            return None

        return SchemaGraph(sdl=sdl_text, source_name="federation_service_sdl")
