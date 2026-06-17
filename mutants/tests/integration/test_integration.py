"""Integration tests for graphql-mcp SDK against a real GraphQL server.

These tests exercise the full stack: SDK → HTTP transport → mock GraphQL server.
They verify that the library works end-to-end as a consumer would use it.
"""

from __future__ import annotations

import os

import pytest

from graphql_mcp import AsyncGraphQLClient, GraphQLClient
from graphql_mcp.domain.models import ErrorClass


class TestSyncClient:
    """Test synchronous GraphQLClient against the mock server."""

    def test_simple_query(self, graphql_endpoint: str):
        """Basic query returns data with ok error class."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            result = client.query("{ hello }")

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            assert result.data["hello"] == "Hello from mock GraphQL server!"

    def test_query_with_variables(self, graphql_endpoint: str):
        """Query with variables resolves correctly."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            result = client.query(
                query="query GetUser($id: String!) { user(id: $id) { id name email } }",
                variables={"id": "1"},
            )

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            user = result.data["user"]
            assert user["id"] == "1"
            assert user["name"] == "Alice"
            assert user["email"] == "alice@example.com"

    def test_list_query(self, graphql_endpoint: str):
        """Query returning a list works correctly."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            result = client.query("{ users { id name } }")

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            users = result.data["users"]
            assert len(users) == 3
            assert users[0]["name"] == "Alice"

    def test_graphql_error(self, graphql_endpoint: str):
        """Invalid query returns graphql error class."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            result = client.query("{ nonexistentField }")

            assert result.error_class == ErrorClass.GRAPHQL
            assert result.errors is not None
            assert len(result.errors) > 0

    def test_schema_introspection(self, graphql_endpoint: str):
        """Schema introspection via the SDK works."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            summary = client.introspect()

            # The mock server has hello, users, user query fields
            # query_fields is list[str] — field names directly
            assert "hello" in summary.query_fields
            assert "users" in summary.query_fields
            assert "user" in summary.query_fields

    def test_describe_type(self, graphql_endpoint: str):
        """describe_type returns field details."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            type_info = client.describe_type("User")

            assert type_info is not None
            assert type_info.name == "User"
            field_names = [f.name for f in type_info.fields]
            assert "id" in field_names
            assert "name" in field_names
            assert "email" in field_names

    def test_raw_query(self, graphql_endpoint: str):
        """Raw query passthrough works."""
        with GraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="introspection",
        ) as client:
            result = client.raw({"query": "{ hello }"})

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            assert result.data["hello"] == "Hello from mock GraphQL server!"


class TestAsyncClient:
    """Test asynchronous AsyncGraphQLClient against the mock server."""

    @pytest.mark.asyncio
    async def test_async_simple_query(self, graphql_endpoint: str):
        """Async basic query returns data with ok error class."""
        async with AsyncGraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="sdl_file",
            schema_sdl="",
        ) as client:
            # Override transport endpoint — schema from introspection not
            # available for async client, so we test query only
            result = await client.query("{ hello }")

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            assert result.data["hello"] == "Hello from mock GraphQL server!"

    @pytest.mark.asyncio
    async def test_async_query_with_variables(self, graphql_endpoint: str):
        """Async query with variables resolves correctly."""
        async with AsyncGraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="sdl_file",
            schema_sdl="",
        ) as client:
            result = await client.query(
                query="query GetUser($id: String!) { user(id: $id) { id name email } }",
                variables={"id": "2"},
            )

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            user = result.data["user"]
            assert user["id"] == "2"
            assert user["name"] == "Bob"

    @pytest.mark.asyncio
    async def test_async_list_query(self, graphql_endpoint: str):
        """Async list query works correctly."""
        async with AsyncGraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="sdl_file",
            schema_sdl="",
        ) as client:
            result = await client.query("{ users { id name email } }")

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            users = result.data["users"]
            assert len(users) == 3

    @pytest.mark.asyncio
    async def test_async_raw_query(self, graphql_endpoint: str):
        """Async raw query passthrough works."""
        async with AsyncGraphQLClient.from_env(
            endpoint=graphql_endpoint,
            schema_source="sdl_file",
            schema_sdl="",
        ) as client:
            result = await client.raw({"query": "{ hello }"})

            assert result.error_class == ErrorClass.OK
            assert result.data is not None
            assert result.data["hello"] == "Hello from mock GraphQL server!"
