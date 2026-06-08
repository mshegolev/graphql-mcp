"""Tests for MCP stdio inbound adapter.

Verifies that all 6 GraphQLClient operations are registered as MCP tools
and that tool handlers delegate correctly to GraphQLClient.
"""

from __future__ import annotations

from unittest.mock import patch

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _mock_client() -> GraphQLClient:
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=None, config=config)


class TestMCPToolRegistration:
    """Verify all 6 operations are registered as MCP tools."""

    def test_mcp_server_exists(self) -> None:
        from graphql_mcp.adapters.inbound.mcp_stdio import mcp

        assert mcp is not None
        assert mcp.name == "graphql-mcp"

    def test_all_tools_registered(self) -> None:
        """All 7 GraphQLClient operations should be registered as MCP tools."""
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        expected_tools = {"query", "raw", "introspect", "describe_type", "list_subgraphs", "refresh_schema", "entities"}
        for tool_name in expected_tools:
            assert hasattr(mod, tool_name), f"Missing MCP tool: {tool_name}"
            assert callable(getattr(mod, tool_name)), f"MCP tool not callable: {tool_name}"


class TestMCPToolDelegation:
    """Verify MCP tools delegate to GraphQLClient correctly."""

    def test_introspect_tool_returns_dict(self) -> None:
        """introspect tool should return a dict with query_fields."""
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.introspect()
        assert isinstance(result, dict)
        assert "query_fields" in result
        assert "hello" in result["query_fields"]

    def test_describe_type_tool(self) -> None:
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.describe_type("User")
        assert result is not None
        assert result["name"] == "User"

    def test_list_subgraphs_tool(self) -> None:
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.list_subgraphs()
        assert isinstance(result, list)

    def test_refresh_schema_tool(self) -> None:
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.refresh_schema()
        assert result == {"status": "refreshed"}

    def test_query_tool_no_transport(self) -> None:
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.query("{ hello }")
        assert result["error_class"] == "transport"

    def test_raw_tool_no_transport(self) -> None:
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.raw({"query": "{ hello }"})
        assert result["error_class"] == "transport"

    def test_entities_tool_no_transport(self) -> None:
        import graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.entities([{"__typename": "Product", "id": "123"}])
        assert result["error_class"] == "transport"
