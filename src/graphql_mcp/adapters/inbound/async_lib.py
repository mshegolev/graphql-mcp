from __future__ import annotations

import atexit
import contextlib
import logging
import time
from typing import TYPE_CHECKING, Any

from graphql_mcp.adapters.outbound.async_http_transport import AsyncHttpTransport
from graphql_mcp.adapters.outbound.file_source import FileSdlSource
from graphql_mcp.adapters.outbound.gitlab_source import GitLabSource
from graphql_mcp.adapters.outbound.query_guard import check_mutation_guard
from graphql_mcp.adapters.outbound.schema_analyzer import SchemaAnalyzer
from graphql_mcp.adapters.outbound.otel_metrics import record_query_metrics
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.models import ErrorClass, QueryResult
from graphql_mcp.domain.schema_service import SchemaService

if TYPE_CHECKING:
    from graphql_mcp.domain.models import (
        SchemaGraph,
        SchemaSummary,
        Subgraph,
        TypeInfo,
    )
    from graphql_mcp.ports.schema_source import SchemaSource

logger = logging.getLogger(__name__)

_ENTITIES_QUERY = """\
query ($representations: [_Any!]!) {
  _entities(representations: $representations) {
    __typename
  }
}"""


class AsyncGraphQLClient:
    """Async library-first facade for graphql-mcp.

    Async counterpart to :class:`GraphQLClient`. All transport-bound
    operations (``query``, ``raw``, ``close``) are ``async``.
    Schema-local operations (``introspect``, ``describe_type``,
    ``list_subgraphs``, ``refresh_schema``) remain synchronous because
    they use in-process schema resolution without network I/O.

    Usage::

        from graphql_mcp import AsyncGraphQLClient

        async with AsyncGraphQLClient.from_env() as client:
            result = await client.query("{ users { id } }")
    """

    def __init__(
        self,
        schema_service: SchemaService,
        transport: AsyncHttpTransport | None = None,
        config: GraphQLConfig | None = None,
    ) -> None:
        self._schema_service = schema_service
        self._transport = transport
        self._config = config
        self._allow_mutations = config.allow_mutations if config else False
        self._supergraph_source = config.supergraph_source if config else "auto"
        self._analyzer = SchemaAnalyzer()
        self._closed = False

    @classmethod
    def from_env(cls, **overrides: Any) -> AsyncGraphQLClient:
        """Create an AsyncGraphQLClient from environment variables.

        Reads GRAPHQL_* env vars, builds the schema cascade based on
        ``GRAPHQL_SCHEMA_SOURCE`` (default: "auto" = try all in priority order),
        and returns a wired client.

        Note: Schema cascade sources that require a sync transport
        (IntrospectionSource, ServiceSdlSource) are skipped because they
        need a sync HttpTransport. The async client relies on GitLab and
        file sources for schema resolution. If introspection is required,
        construct manually with appropriate sources.

        Args:
            **overrides: Override specific config fields (useful in tests).
        """
        config = GraphQLConfig(**overrides) if overrides else GraphQLConfig()

        # Build async transport
        transport: AsyncHttpTransport | None = None
        if config.endpoint:
            transport = AsyncHttpTransport(
                endpoint=config.endpoint,
                bearer_token=config.bearer_token,
                timeout=float(config.timeout),
                ssl_verify=config.ssl_verify,
            )

        # Build cascade sources in priority order
        sources: list[SchemaSource] = []
        source_mode = config.schema_source.lower()

        if (
            source_mode in ("auto", "gitlab")
            and config.schema_gitlab_url
            and config.schema_gitlab_project_id
            and config.schema_gitlab_file_path
        ):
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

        if source_mode in ("auto", "sdl_file") and config.schema_sdl:
            sources.append(FileSdlSource(file_path=config.schema_sdl))

        schema_service = SchemaService(
            sources=sources,
            ttl_seconds=float(config.schema_ttl),
        )

        instance = cls(
            schema_service=schema_service,
            transport=transport,
            config=config,
        )

        # atexit cannot await async close; use sync cleanup path.
        # httpx.AsyncClient exposes a sync-safe close() via __del__,
        # so we directly close the underlying client for cleanup.
        def _sync_cleanup() -> None:
            if not instance._closed:
                instance._closed = True
                if instance._transport is not None:
                    with contextlib.suppress(Exception):
                        instance._transport._client.close()
                    logger.debug("Async transport cleaned up via atexit")

        atexit.register(_sync_cleanup)
        return instance

    @property
    def schema(self) -> SchemaGraph:
        """Resolve and return the current schema (cached within TTL)."""
        return self._schema_service.resolve()

    async def query(self, query: str, variables: dict[str, Any] | None = None) -> QueryResult:
        """Execute a GraphQL query and return typed result.

        Raises MutationGuardError if query contains a mutation and
        allow_mutations is False.
        """
        if not self._allow_mutations:
            check_mutation_guard(query)
        if self._transport is None:
            return QueryResult(
                errors=[{"message": "No endpoint configured"}],
                error_class=ErrorClass.TRANSPORT,
            )
        start = time.monotonic()
        result = await self._transport.execute(query, variables)
        record_query_metrics(result, time.monotonic() - start, operation="query")
        return result

    async def raw(self, body: dict[str, Any]) -> QueryResult:
        """Send arbitrary POST body and return typed result.

        If body contains a 'query' key, mutation guard applies.
        If no 'query' key, the body passes through — server decides.
        """
        if not self._allow_mutations:
            query_str = body.get("query")
            if isinstance(query_str, str):
                check_mutation_guard(query_str)
        if self._transport is None:
            return QueryResult(
                errors=[{"message": "No endpoint configured"}],
                error_class=ErrorClass.TRANSPORT,
            )
        start = time.monotonic()
        result = await self._transport.post_raw(body)
        record_query_metrics(result, time.monotonic() - start, operation="raw")
        return result

    async def entities(self, representations: list[dict[str, Any]]) -> QueryResult:
        """Resolve federation entities via _entities(representations:) pass-through.

        Sends the representations to the federation gateway's _entities query
        and returns the raw result. This is a query (not a mutation), so the
        mutation guard does not apply.
        """
        if self._transport is None:
            return QueryResult(
                errors=[{"message": "No endpoint configured"}],
                error_class=ErrorClass.TRANSPORT,
            )
        start = time.monotonic()
        result = await self._transport.execute(
            _ENTITIES_QUERY,
            {"representations": representations},
        )
        record_query_metrics(result, time.monotonic() - start, operation="entities")
        return result

    def introspect(self) -> SchemaSummary:
        """Return a summary of Query fields and types from the active schema."""
        schema = self._schema_service.resolve()
        return self._analyzer.build_summary(schema.sdl)

    def describe_type(self, name: str) -> TypeInfo | None:
        """Return field/arg details for a named type, with federation subgraph if available."""
        schema = self._schema_service.resolve()
        return self._analyzer.describe_type(schema.sdl, name)

    def list_subgraphs(self) -> list[Subgraph]:
        """Return subgraph metadata parsed from supergraph SDL.

        Returns empty list (not error) when supergraph_source=off or
        when the resolved schema is not a supergraph.
        """
        if self._supergraph_source == "off":
            return []
        schema = self._schema_service.resolve()
        return self._analyzer.list_subgraphs(schema.sdl)

    def refresh_schema(self) -> None:
        """Clear schema cache, forcing next access to re-fetch."""
        self._schema_service.invalidate()

    async def close(self) -> None:
        """Release transport resources. Safe to call multiple times."""
        if self._closed:
            return
        self._closed = True
        if self._transport is not None:
            await self._transport.close()
            logger.debug("Async transport closed")

    async def __aenter__(self) -> AsyncGraphQLClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()
