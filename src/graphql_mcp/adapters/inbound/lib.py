from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from graphql_mcp.adapters.outbound.file_source import FileSdlSource
from graphql_mcp.adapters.outbound.gitlab_source import GitLabSource
from graphql_mcp.adapters.outbound.http_transport import HttpTransport
from graphql_mcp.adapters.outbound.introspection_source import IntrospectionSource
from graphql_mcp.adapters.outbound.service_sdl_source import ServiceSdlSource
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.models import SchemaGraph
from graphql_mcp.domain.schema_service import SchemaService
from graphql_mcp.ports.schema_source import SchemaSource

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class GraphQLClient:
    """Library-first facade for graphql-mcp.

    Usage::

        from graphql_mcp import GraphQLClient
        client = GraphQLClient.from_env()
        schema = client.schema  # resolves through cascade
    """

    def __init__(
        self,
        schema_service: SchemaService,
        transport: HttpTransport | None = None,
        config: GraphQLConfig | None = None,
    ) -> None:
        self._schema_service = schema_service
        self._transport = transport
        self._config = config

    @classmethod
    def from_env(cls, **overrides: str) -> GraphQLClient:
        """Create a GraphQLClient from environment variables.

        Reads GRAPHQL_* env vars, builds the schema cascade based on
        ``GRAPHQL_SCHEMA_SOURCE`` (default: "auto" = try all in priority order),
        and returns a wired client.

        Args:
            **overrides: Override specific config fields (useful in tests).
        """
        config = GraphQLConfig(**overrides) if overrides else GraphQLConfig()

        # Build transport (needed by introspection and _service{sdl} sources)
        transport: HttpTransport | None = None
        if config.endpoint:
            transport = HttpTransport(
                endpoint=config.endpoint,
                bearer_token=config.bearer_token,
                timeout=float(config.timeout),
                ssl_verify=config.ssl_verify,
            )

        # Build cascade sources in priority order
        sources: list[SchemaSource] = []
        source_mode = config.schema_source.lower()

        if source_mode in ("auto", "gitlab"):
            if config.schema_gitlab_url and config.schema_gitlab_project_id and config.schema_gitlab_file_path:
                sources.append(
                    GitLabSource(
                        gitlab_url=config.schema_gitlab_url,
                        project_id=config.schema_gitlab_project_id,
                        file_path=config.schema_gitlab_file_path,
                        ref=config.schema_gitlab_ref,
                        token=config.gitlab_token,
                        timeout=float(config.timeout),
                        ssl_verify=config.ssl_verify,
                    )
                )

        if source_mode in ("auto", "introspection"):
            if transport is not None:
                sources.append(IntrospectionSource(transport=transport))

        if source_mode in ("auto", "federation"):
            if transport is not None:
                sources.append(ServiceSdlSource(transport=transport))

        if source_mode in ("auto", "sdl_file"):
            if config.schema_sdl:
                sources.append(FileSdlSource(file_path=config.schema_sdl))

        schema_service = SchemaService(
            sources=sources,
            ttl_seconds=float(config.schema_ttl),
        )

        return cls(
            schema_service=schema_service,
            transport=transport,
            config=config,
        )

    @property
    def schema(self) -> SchemaGraph:
        """Resolve and return the current schema (cached within TTL)."""
        return self._schema_service.resolve()

    def refresh_schema(self) -> None:
        """Clear schema cache, forcing next access to re-fetch."""
        self._schema_service.invalidate()

    def introspect(self) -> SchemaGraph:
        """Alias for schema property -- returns the resolved schema."""
        return self._schema_service.resolve()
