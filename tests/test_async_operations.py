"""Integration tests for all 6 AsyncGraphQLClient operations.

Covers: query(), raw(), introspect(), describe_type(), list_subgraphs(),
refresh_schema(). Async counterpart to test_operations.py.
"""

from __future__ import annotations

import httpx
import pytest
import respx

from graphql_mcp.adapters.inbound.async_lib import AsyncGraphQLClient
from graphql_mcp.adapters.outbound.async_http_transport import AsyncHttpTransport
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.errors import MutationGuardError
from graphql_mcp.domain.models import ErrorClass, SchemaSummary, TypeInfo
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, SAMPLE_SUPERGRAPH_SDL, MockSchemaSource

MOCK_ENDPOINT = "https://mock.test/graphql"
# httpx.AsyncClient(base_url=...) appends trailing slash on .post("")
MOCK_ENDPOINT_RESOLVED = "https://mock.test/graphql/"


def _make_async_client(
    *,
    sdl: str = SAMPLE_SDL,
    allow_mutations: bool = False,
    supergraph_source: str = "auto",
    with_transport: bool = True,
) -> AsyncGraphQLClient:
    """Build an AsyncGraphQLClient wired with a MockSchemaSource and optionally AsyncHttpTransport."""
    source = MockSchemaSource("test", sdl=sdl)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(
        endpoint=MOCK_ENDPOINT if with_transport else "",
        allow_mutations=allow_mutations,
        supergraph_source=supergraph_source,
    )
    transport: AsyncHttpTransport | None = None
    if with_transport:
        transport = AsyncHttpTransport(endpoint=MOCK_ENDPOINT)
    return AsyncGraphQLClient(schema_service=service, transport=transport, config=config)


# ---------------------------------------------------------------------------
# Test Group 1: query() — async counterpart
# ---------------------------------------------------------------------------


class TestAsyncQuery:
    """Tests for AsyncGraphQLClient.query()."""

    @respx.mock
    async def test_query_returns_query_result_with_data(self) -> None:
        """query() returns QueryResult with data and errors separated."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"users": [{"id": "1"}]}},
            ),
        )
        client = _make_async_client()
        result = await client.query("{ users { id } }")

        assert result.data == {"users": [{"id": "1"}]}
        assert result.errors == []
        assert result.error_class == ErrorClass.OK

    @respx.mock
    async def test_query_error_class_graphql_on_errors(self) -> None:
        """error_class=graphql when response has errors[]."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": None,
                    "errors": [{"message": "Field not found"}],
                },
            ),
        )
        client = _make_async_client()
        result = await client.query("{ nonexistent }")

        assert result.error_class == ErrorClass.GRAPHQL
        assert len(result.errors) == 1

    @respx.mock
    async def test_query_error_class_transport_on_http_error(self) -> None:
        """error_class=transport on HTTP != 200."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(500, text="Internal Server Error"),
        )
        client = _make_async_client()
        result = await client.query("{ users { id } }")

        assert result.error_class == ErrorClass.TRANSPORT

    @respx.mock
    async def test_query_error_class_transport_on_connect_error(self) -> None:
        """error_class=transport on connection error."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(side_effect=httpx.ConnectError("timeout"))
        client = _make_async_client()
        result = await client.query("{ users { id } }")

        assert result.error_class == ErrorClass.TRANSPORT

    async def test_query_blocks_mutation(self) -> None:
        """Mutation blocked by default."""
        client = _make_async_client(with_transport=False)
        with pytest.raises(MutationGuardError):
            await client.query("mutation { createUser { id } }")

    @respx.mock
    async def test_query_allows_mutation_when_enabled(self) -> None:
        """Mutation allowed when GRAPHQL_ALLOW_MUTATIONS=true."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"createUser": {"id": "1"}}},
            ),
        )
        client = _make_async_client(allow_mutations=True)
        result = await client.query("mutation { createUser { id } }")

        assert result.error_class == ErrorClass.OK

    async def test_query_no_transport_returns_transport_error(self) -> None:
        """query() with no endpoint returns error_class=transport."""
        client = _make_async_client(with_transport=False)
        result = await client.query("{ users { id } }")

        assert result.error_class == ErrorClass.TRANSPORT
        assert "No endpoint configured" in result.errors[0]["message"]

    @respx.mock
    async def test_query_with_variables(self) -> None:
        """variables are passed through to transport."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"user": {"name": "Alice"}}},
            ),
        )
        client = _make_async_client()
        result = await client.query(
            "query GetUser($id: ID!) { user(id: $id) { name } }",
            {"id": "1"},
        )

        assert result.data == {"user": {"name": "Alice"}}
        assert result.error_class == ErrorClass.OK


# ---------------------------------------------------------------------------
# Test Group 2: raw() — async counterpart
# ---------------------------------------------------------------------------


class TestAsyncRaw:
    """Tests for AsyncGraphQLClient.raw()."""

    @respx.mock
    async def test_raw_returns_query_result(self) -> None:
        """raw(body) returns QueryResult."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"users": []}},
            ),
        )
        client = _make_async_client()
        result = await client.raw({"query": "{ users { id } }"})

        assert result.error_class == ErrorClass.OK

    async def test_raw_blocks_mutation(self) -> None:
        """raw() mutation guard checks body['query']."""
        client = _make_async_client(with_transport=False)
        with pytest.raises(MutationGuardError):
            await client.raw({"query": "mutation { deleteUser { id } }"})

    @respx.mock
    async def test_raw_allows_body_without_query_key(self) -> None:
        """raw() with no 'query' key passes through (no guard)."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": None},
            ),
        )
        client = _make_async_client()
        # body has no "query" key — mutation guard should not fire
        result = await client.raw({"operationName": "something"})

        # No MutationGuardError raised — that's the assertion
        assert result is not None

    async def test_raw_no_transport_returns_transport_error(self) -> None:
        """raw() with no endpoint returns error_class=transport."""
        client = _make_async_client(with_transport=False)
        result = await client.raw({"query": "{ users { id } }"})

        assert result.error_class == ErrorClass.TRANSPORT


# ---------------------------------------------------------------------------
# Test Group 3: introspect() — sync method on async client
# ---------------------------------------------------------------------------


class TestAsyncIntrospect:
    """Tests for AsyncGraphQLClient.introspect() (sync method)."""

    def test_introspect_returns_schema_summary(self) -> None:
        """introspect() returns SchemaSummary with query_fields."""
        client = _make_async_client(with_transport=False)
        result = client.introspect()

        assert isinstance(result, SchemaSummary)
        assert "hello" in result.query_fields
        assert "users" in result.query_fields

    def test_introspect_lists_types(self) -> None:
        """introspect() types include user-defined types."""
        client = _make_async_client(with_transport=False)
        result = client.introspect()
        type_names = [t.name for t in result.types]

        assert "User" in type_names
        assert "__Schema" not in type_names


# ---------------------------------------------------------------------------
# Test Group 4: describe_type() — sync method on async client
# ---------------------------------------------------------------------------


class TestAsyncDescribeType:
    """Tests for AsyncGraphQLClient.describe_type() (sync method)."""

    def test_describe_type_returns_type_info(self) -> None:
        """describe_type returns TypeInfo with fields."""
        client = _make_async_client(with_transport=False)
        info = client.describe_type("User")

        assert info is not None
        assert isinstance(info, TypeInfo)
        assert info.name == "User"
        assert info.kind == "OBJECT"
        assert "id" in [f.name for f in info.fields]
        assert info.subgraph is None  # not supergraph

    def test_describe_type_with_supergraph(self) -> None:
        """describe_type returns subgraph when supergraph SDL loaded."""
        client = _make_async_client(sdl=SAMPLE_SUPERGRAPH_SDL, with_transport=False)
        info = client.describe_type("User")

        assert info is not None
        assert info.subgraph == "users"

    def test_describe_type_unknown_returns_none(self) -> None:
        """describe_type returns None for non-existent type."""
        client = _make_async_client(with_transport=False)
        result = client.describe_type("NonExistent")

        assert result is None


# ---------------------------------------------------------------------------
# Test Group 5: list_subgraphs() — sync method on async client
# ---------------------------------------------------------------------------


class TestAsyncListSubgraphs:
    """Tests for AsyncGraphQLClient.list_subgraphs() (sync method)."""

    def test_list_subgraphs_from_supergraph(self) -> None:
        """list_subgraphs returns Subgraph list from supergraph SDL."""
        client = _make_async_client(sdl=SAMPLE_SUPERGRAPH_SDL, with_transport=False)
        subgraphs = client.list_subgraphs()

        assert len(subgraphs) >= 2
        names = [s.name for s in subgraphs]
        assert "users" in names
        assert "products" in names

    def test_list_subgraphs_has_url_and_owned_types(self) -> None:
        """Each Subgraph has url and owned_types."""
        client = _make_async_client(sdl=SAMPLE_SUPERGRAPH_SDL, with_transport=False)
        subgraphs = client.list_subgraphs()

        users_sg = next(s for s in subgraphs if s.name == "users")
        assert users_sg.url == "http://users:4001/graphql"
        assert "User" in users_sg.owned_types

    def test_list_subgraphs_empty_for_non_supergraph(self) -> None:
        """Returns empty list (not error) for regular schema."""
        client = _make_async_client(with_transport=False)
        subgraphs = client.list_subgraphs()

        assert subgraphs == []

    def test_list_subgraphs_empty_when_supergraph_source_off(self) -> None:
        """Returns empty list when GRAPHQL_SUPERGRAPH_SOURCE=off."""
        client = _make_async_client(
            sdl=SAMPLE_SUPERGRAPH_SDL,
            supergraph_source="off",
            with_transport=False,
        )
        subgraphs = client.list_subgraphs()

        assert subgraphs == []


# ---------------------------------------------------------------------------
# Test Group 6: refresh_schema() — sync method on async client
# ---------------------------------------------------------------------------


class TestAsyncRefreshSchema:
    """Tests for AsyncGraphQLClient.refresh_schema() (sync method)."""

    def test_refresh_forces_refetch(self) -> None:
        """refresh_schema() clears cache, next access re-fetches."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=300)
        config = GraphQLConfig(allow_mutations=False)
        client = AsyncGraphQLClient(
            schema_service=service,
            transport=None,
            config=config,
        )

        # First call resolves schema
        client.introspect()
        assert source.call_count == 1

        # refresh_schema clears cache
        client.refresh_schema()

        # Next call should re-fetch
        client.introspect()
        assert source.call_count == 2
