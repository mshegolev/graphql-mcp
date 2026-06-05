"""Tests for FastAPI REST inbound adapter.

Covers: /health, /graphql/query, /graphql/introspect, /graphql/type/{name},
/graphql/subgraphs, /graphql/refresh, mutation guard via HTTP.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.adapters.inbound.rest import app, set_client
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, SAMPLE_SUPERGRAPH_SDL, MockSchemaSource


@pytest.fixture()
def test_client() -> TestClient:
    """FastAPI TestClient with a mock GraphQLClient (no transport, schema-only)."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    client = GraphQLClient(schema_service=service, transport=None, config=config)
    set_client(client)
    return TestClient(app)


@pytest.fixture()
def supergraph_test_client() -> TestClient:
    """FastAPI TestClient with supergraph SDL."""
    source = MockSchemaSource("test", sdl=SAMPLE_SUPERGRAPH_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    client = GraphQLClient(schema_service=service, transport=None, config=config)
    set_client(client)
    return TestClient(app)


class TestHealth:
    def test_health_returns_ok(self, test_client: TestClient) -> None:
        resp = test_client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestGraphQLQuery:
    def test_query_no_transport_returns_transport_error(self, test_client: TestClient) -> None:
        resp = test_client.post("/graphql/query", json={"query": "{ hello }"})
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "errors" in body
        assert "error_class" in body
        assert body["error_class"] == "transport"

    def test_query_mutation_blocked_returns_403(self, test_client: TestClient) -> None:
        resp = test_client.post("/graphql/query", json={"query": "mutation { foo }"})
        assert resp.status_code == 403


class TestIntrospect:
    def test_introspect_returns_summary(self, test_client: TestClient) -> None:
        resp = test_client.get("/graphql/introspect")
        assert resp.status_code == 200
        body = resp.json()
        assert "query_fields" in body
        assert "hello" in body["query_fields"]


class TestDescribeType:
    def test_describe_existing_type(self, test_client: TestClient) -> None:
        resp = test_client.get("/graphql/type/User")
        assert resp.status_code == 200
        body = resp.json()
        assert body["name"] == "User"

    def test_describe_missing_type_returns_404(self, test_client: TestClient) -> None:
        resp = test_client.get("/graphql/type/NonExistent")
        assert resp.status_code == 404


class TestListSubgraphs:
    def test_list_subgraphs_from_supergraph(self, supergraph_test_client: TestClient) -> None:
        resp = supergraph_test_client.get("/graphql/subgraphs")
        assert resp.status_code == 200
        body = resp.json()
        names = [s["name"] for s in body]
        assert "users" in names

    def test_list_subgraphs_empty_for_regular_schema(self, test_client: TestClient) -> None:
        resp = test_client.get("/graphql/subgraphs")
        assert resp.status_code == 200
        assert resp.json() == []


class TestRefresh:
    def test_refresh_returns_ok(self, test_client: TestClient) -> None:
        resp = test_client.post("/graphql/refresh")
        assert resp.status_code == 200
        assert resp.json() == {"status": "refreshed"}
