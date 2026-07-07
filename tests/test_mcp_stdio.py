"""Tests for MCP stdio inbound adapter.

Verifies that all 8 GraphQLClient operations are registered as MCP tools and
that tool handlers delegate correctly to GraphQLClient. Tools return their
domain Pydantic models directly (for structured output); error conditions are
raised as MCP ToolErrors.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from mcp.server.fastmcp.exceptions import ToolError

from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient
from generic_graphql_mcp.adapters.inbound.mcp_stdio import RefreshResult
from generic_graphql_mcp.config import GraphQLConfig
from generic_graphql_mcp.domain.models import SchemaSummary, TypeInfo
from generic_graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _mock_client() -> GraphQLClient:
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=None, config=config)


class TestMCPToolRegistration:
    """Verify all 8 operations are registered as MCP tools."""

    def test_mcp_server_exists(self) -> None:
        from generic_graphql_mcp.adapters.inbound.mcp_stdio import mcp

        assert mcp is not None
        assert mcp.name == "generic-graphql-mcp"

    def test_all_tools_registered(self) -> None:
        """All 8 GraphQLClient operations should be registered as MCP tools."""
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        expected_tools = {
            "query",
            "raw",
            "introspect",
            "describe_type",
            "list_subgraphs",
            "refresh_schema",
            "entities",
            "subscribe",
        }
        for tool_name in expected_tools:
            assert hasattr(mod, tool_name), f"Missing MCP tool: {tool_name}"
            assert callable(getattr(mod, tool_name)), f"MCP tool not callable: {tool_name}"


class TestMCPToolDelegation:
    """Verify MCP tools delegate to GraphQLClient correctly."""

    def test_introspect_tool_returns_summary(self) -> None:
        """introspect tool should return a SchemaSummary with query_fields."""
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.introspect()
        assert isinstance(result, SchemaSummary)
        assert "hello" in result.query_fields

    def test_describe_type_tool(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.describe_type("User")
        assert isinstance(result, TypeInfo)
        assert result.name == "User"

    def test_list_subgraphs_tool(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.list_subgraphs()
        assert isinstance(result, list)

    def test_refresh_schema_tool(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.refresh_schema()
        assert isinstance(result, RefreshResult)
        assert result.status == "refreshed"

    def test_query_tool_no_transport(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.query("{ hello }")
        assert result.error_class.value == "transport"

    def test_raw_tool_no_transport(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.raw({"query": "{ hello }"})
        assert result.error_class.value == "transport"

    def test_entities_tool_no_transport(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with patch.object(mod, "_get_client", return_value=_mock_client()):
            result = mod.entities([{"__typename": "Product", "id": "123"}])
        assert result.error_class.value == "transport"


class TestMCPToolErrors:
    """Verify a blocked mutation surfaces as an actionable MCP ToolError."""

    def test_query_mutation_blocked_raises_tool_error(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with (
            patch.object(mod, "_get_client", return_value=_mock_client()),
            pytest.raises(ToolError) as exc_info,
        ):
            mod.query("mutation { doThing }")
        assert "GRAPHQL_ALLOW_MUTATIONS" in str(exc_info.value)
