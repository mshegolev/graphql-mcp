from __future__ import annotations

import logging
from pathlib import Path

from graphql import build_schema
from graphql.error import GraphQLError

from graphql_mcp.domain.models import SchemaGraph

logger = logging.getLogger(__name__)


class FileSdlSource:
    """Outbound adapter: read SDL from a local file."""

    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)

    @property
    def name(self) -> str:
        return "sdl_file"

    def fetch_schema(self) -> SchemaGraph | None:
        if not self._path.is_file():
            logger.debug("SDL file not found: %s", self._path)
            return None

        try:
            sdl_text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.debug("SDL file read failed: %s", exc)
            return None

        if not sdl_text.strip():
            logger.debug("SDL file is empty: %s", self._path)
            return None

        try:
            build_schema(sdl_text)  # validate
        except GraphQLError as exc:
            logger.debug("SDL file parse failed: %s", exc)
            return None

        return SchemaGraph(sdl=sdl_text, source_name="sdl_file")
