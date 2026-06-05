"""Integration tests for all 6 GraphQLClient operations.

Covers: query(), raw(), introspect(), describe_type(), list_subgraphs(),
refresh_schema(). Validates Phase 2 success criteria GQL-01 through GQL-09
(except GQL-06).
"""

from __future__ import annotations

import httpx
import pytest
import respx

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.adapters.outbound.http_transport import HttpTransport
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.errors import MutationGuardError
from graphql_mcp.domain.models import ErrorClass, SchemaSummary, TypeInfo
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, SAMPLE_SUPERGRAPH_SDL, MockSchemaSource

MOCK_ENDPOINT = "https://mock.test/graphql"
# httpx.Client(base_url=...) appends trailing slash on .post("")
MOCK_ENDPOINT_RESOLVED = "https://mock.test/graphql/"


def _make_client(
    *,
    sdl: str = SAMPLE_SDL,
    allow_mutations: bool = False,
    supergraph_source: str = "auto",
    with_transport: bool = True,
) -> GraphQLClient:
    """Build a GraphQLClient wired with a MockSchemaSource and optionally HttpTransport."""
    source = MockSchemaSource("test", sdl=sdl)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(
        endpoint=MOCK_ENDPOINT if with_transport else "",
        allow_mutations=allow_mutations,
        supergraph_source=supergraph_source,
    )
    transport: HttpTransport | None = None
    if with_transport:
        transport = HttpTransport(endpoint=MOCK_ENDPOINT)
    return GraphQLClient(schema_service=service, transport=transport, config=config)


# ---------------------------------------------------------------------------
# Test Group 1: query() — GQL-01, GQL-02, GQL-03
# ---------------------------------------------------------------------------


class TestQuery:
    """Tests for GraphQLClient.query()."""

    @respx.mock
    def test_query_returns_query_result_with_data(self) -> None:
        """GQL-01: query() returns QueryResult with data and errors separated."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"users": [{"id": "1"}]}},
            ),
        )
        client = _make_client()
        result = client.query("{ users { id } }")

        assert result.data == {"users": [{"id": "1"}]}
        assert result.errors == []
        assert result.error_class == ErrorClass.OK

    @respx.mock
    def test_query_error_class_graphql_on_errors(self) -> None:
        """GQL-02: error_class=graphql when response has errors[]."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": None,
                    "errors": [{"message": "Field not found"}],
                },
            ),
        )
        client = _make_client()
        result = client.query("{ nonexistent }")

        assert result.error_class == ErrorClass.GRAPHQL
        assert len(result.errors) == 1

    @respx.mock
    def test_query_error_class_transport_on_http_error(self) -> None:
        """GQL-02: error_class=transport on HTTP != 200."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(500, text="Internal Server Error"),
        )
        client = _make_client()
        result = client.query("{ users { id } }")

        assert result.error_class == ErrorClass.TRANSPORT

    @respx.mock
    def test_query_error_class_transport_on_timeout(self) -> None:
        """GQL-02: error_class=transport on connection error."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(side_effect=httpx.ConnectError("timeout"))
        client = _make_client()
        result = client.query("{ users { id } }")

        assert result.error_class == ErrorClass.TRANSPORT

    def test_query_blocks_mutation(self) -> None:
        """GQL-03: Mutation blocked by default."""
        client = _make_client(with_transport=False)
        with pytest.raises(MutationGuardError):
            client.query("mutation { createUser { id } }")

    @respx.mock
    def test_query_allows_mutation_when_enabled(self) -> None:
        """GQL-03: Mutation allowed when GRAPHQL_ALLOW_MUTATIONS=true."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"createUser": {"id": "1"}}},
            ),
        )
        client = _make_client(allow_mutations=True)
        result = client.query("mutation { createUser { id } }")

        assert result.error_class == ErrorClass.OK

    def test_query_no_transport_returns_transport_error(self) -> None:
        """query() with no endpoint returns error_class=transport."""
        client = _make_client(with_transport=False)
        result = client.query("{ users { id } }")

        assert result.error_class == ErrorClass.TRANSPORT
        assert "No endpoint configured" in result.errors[0]["message"]

    @respx.mock
    def test_query_with_variables(self) -> None:
        """GQL-01: variables are passed through to transport."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"user": {"name": "Alice"}}},
            ),
        )
        client = _make_client()
        result = client.query(
            "query GetUser($id: ID!) { user(id: $id) { name } }",
            {"id": "1"},
        )

        assert result.data == {"user": {"name": "Alice"}}
        assert result.error_class == ErrorClass.OK


# ---------------------------------------------------------------------------
# Test Group 2: raw() — GQL-09, GQL-03
# ---------------------------------------------------------------------------


class TestRaw:
    """Tests for GraphQLClient.raw()."""

    @respx.mock
    def test_raw_returns_query_result(self) -> None:
        """GQL-09: raw(body) returns QueryResult."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": {"users": []}},
            ),
        )
        client = _make_client()
        result = client.raw({"query": "{ users { id } }"})

        assert result.error_class == ErrorClass.OK

    def test_raw_blocks_mutation(self) -> None:
        """GQL-03: raw() mutation guard checks body['query']."""
        client = _make_client(with_transport=False)
        with pytest.raises(MutationGuardError):
            client.raw({"query": "mutation { deleteUser { id } }"})

    @respx.mock
    def test_raw_allows_body_without_query_key(self) -> None:
        """GQL-09: raw() with no 'query' key passes through (no guard)."""
        respx.post(MOCK_ENDPOINT_RESOLVED).mock(
            return_value=httpx.Response(
                200,
                json={"data": None},
            ),
        )
        client = _make_client()
        # body has no "query" key — mutation guard should not fire
        result = client.raw({"operationName": "something"})

        # No MutationGuardError raised — that's the assertion
        assert result is not None

    def test_raw_no_transport_returns_transport_error(self) -> None:
        """raw() with no endpoint returns error_class=transport."""
        client = _make_client(with_transport=False)
        result = client.raw({"query": "{ users { id } }"})

        assert result.error_class == ErrorClass.TRANSPORT


# ---------------------------------------------------------------------------
# Test Group 3: introspect() — GQL-04
# ---------------------------------------------------------------------------


class TestIntrospect:
    """Tests for GraphQLClient.introspect()."""

    def test_introspect_returns_schema_summary(
        self,
        simple_client: GraphQLClient,
    ) -> None:
        """GQL-04: introspect() returns SchemaSummary with query_fields."""
        result = simple_client.introspect()

        assert isinstance(result, SchemaSummary)
        assert "hello" in result.query_fields
        assert "users" in result.query_fields

    def test_introspect_lists_types(
        self,
        simple_client: GraphQLClient,
    ) -> None:
        """GQL-04: introspect() types include user-defined types."""
        result = simple_client.introspect()
        type_names = [t.name for t in result.types]

        assert "User" in type_names
        assert "__Schema" not in type_names


# ---------------------------------------------------------------------------
# Test Group 4: describe_type() — GQL-05
# ---------------------------------------------------------------------------


class TestDescribeType:
    """Tests for GraphQLClient.describe_type()."""

    def test_describe_type_returns_type_info(
        self,
        simple_client: GraphQLClient,
    ) -> None:
        """GQL-05: describe_type returns TypeInfo with fields."""
        info = simple_client.describe_type("User")

        assert info is not None
        assert isinstance(info, TypeInfo)
        assert info.name == "User"
        assert info.kind == "OBJECT"
        assert "id" in [f.name for f in info.fields]
        assert info.subgraph is None  # not supergraph

    def test_describe_type_with_supergraph(self) -> None:
        """GQL-05: describe_type returns subgraph when supergraph SDL loaded."""
        source = MockSchemaSource("test", sdl=SAMPLE_SUPERGRAPH_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(
            schema_service=service,
            transport=None,
            config=config,
        )
        info = client.describe_type("User")

        assert info is not None
        assert info.subgraph == "users"

    def test_describe_type_unknown_returns_none(
        self,
        simple_client: GraphQLClient,
    ) -> None:
        """GQL-05: describe_type returns None for non-existent type."""
        result = simple_client.describe_type("NonExistent")

        assert result is None


# ---------------------------------------------------------------------------
# Test Group 5: list_subgraphs() — GQL-08
# ---------------------------------------------------------------------------


class TestListSubgraphs:
    """Tests for GraphQLClient.list_subgraphs()."""

    def test_list_subgraphs_from_supergraph(self) -> None:
        """GQL-08: list_subgraphs returns Subgraph list from supergraph SDL."""
        source = MockSchemaSource("test", sdl=SAMPLE_SUPERGRAPH_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(
            schema_service=service,
            transport=None,
            config=config,
        )
        subgraphs = client.list_subgraphs()

        assert len(subgraphs) >= 2
        names = [s.name for s in subgraphs]
        assert "users" in names
        assert "products" in names

    def test_list_subgraphs_has_url_and_owned_types(self) -> None:
        """GQL-08: Each Subgraph has url and owned_types."""
        source = MockSchemaSource("test", sdl=SAMPLE_SUPERGRAPH_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(
            schema_service=service,
            transport=None,
            config=config,
        )
        subgraphs = client.list_subgraphs()

        users_sg = next(s for s in subgraphs if s.name == "users")
        assert users_sg.url == "http://users:4001/graphql"
        assert "User" in users_sg.owned_types

    def test_list_subgraphs_empty_for_non_supergraph(
        self,
        simple_client: GraphQLClient,
    ) -> None:
        """GQL-08: Returns empty list (not error) for regular schema."""
        subgraphs = simple_client.list_subgraphs()

        assert subgraphs == []

    def test_list_subgraphs_empty_when_supergraph_source_off(self) -> None:
        """GQL-08: Returns empty list when GRAPHQL_SUPERGRAPH_SOURCE=off."""
        source = MockSchemaSource("test", sdl=SAMPLE_SUPERGRAPH_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(
            allow_mutations=False,
            supergraph_source="off",
        )
        client = GraphQLClient(
            schema_service=service,
            transport=None,
            config=config,
        )
        subgraphs = client.list_subgraphs()

        assert subgraphs == []


# ---------------------------------------------------------------------------
# Test Group 6: refresh_schema() — GQL-07
# ---------------------------------------------------------------------------


class TestRefreshSchema:
    """Tests for GraphQLClient.refresh_schema()."""

    def test_refresh_forces_refetch(self) -> None:
        """GQL-07: refresh_schema() clears cache, next access re-fetches."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=300)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(
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
