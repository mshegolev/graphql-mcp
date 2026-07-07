"""Tests for SchemaResolutionError handling in all inbound adapters.

Verifies HARD-02: no unhandled tracebacks when all schema sources fail.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient
from mcp.server.fastmcp.exceptions import ToolError

from generic_graphql_mcp.adapters.inbound.cli import main
from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient
from generic_graphql_mcp.adapters.inbound.rest import app, set_client
from generic_graphql_mcp.config import GraphQLConfig
from generic_graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import MockSchemaSource


def _failing_client() -> GraphQLClient:
    """Client where ALL schema sources fail → SchemaResolutionError on any schema op."""
    failing = MockSchemaSource("failing", should_raise=True)
    service = SchemaService(sources=[failing], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=None, config=config)


# --- REST adapter ---


class TestRESTSchemaError:
    """REST adapter returns 503 with structured JSON when schema unavailable."""

    @pytest.fixture()
    def failing_test_client(self) -> TestClient:
        set_client(_failing_client())
        return TestClient(app)

    def test_introspect_returns_503(self, failing_test_client: TestClient) -> None:
        resp = failing_test_client.get("/graphql/introspect")
        assert resp.status_code == 503
        body = resp.json()
        assert body["error"] == "schema unavailable"
        assert "detail" in body

    def test_describe_type_returns_503(self, failing_test_client: TestClient) -> None:
        resp = failing_test_client.get("/graphql/type/User")
        assert resp.status_code == 503
        body = resp.json()
        assert body["error"] == "schema unavailable"

    def test_list_subgraphs_returns_503(self, failing_test_client: TestClient) -> None:
        resp = failing_test_client.get("/graphql/subgraphs")
        assert resp.status_code == 503
        body = resp.json()
        assert body["error"] == "schema unavailable"

    def test_health_still_200(self, failing_test_client: TestClient) -> None:
        """Health endpoint is not affected by schema errors."""
        resp = failing_test_client.get("/health")
        assert resp.status_code == 200


# --- MCP adapter ---


class TestMCPSchemaError:
    """MCP adapter raises an actionable ToolError (isError) when schema unavailable."""

    def test_introspect_raises_tool_error(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with (
            patch.object(mod, "_get_client", return_value=_failing_client()),
            pytest.raises(ToolError) as exc_info,
        ):
            mod.introspect()
        assert "Schema unavailable" in str(exc_info.value)

    def test_describe_type_raises_tool_error(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with (
            patch.object(mod, "_get_client", return_value=_failing_client()),
            pytest.raises(ToolError) as exc_info,
        ):
            mod.describe_type("User")
        assert "Schema unavailable" in str(exc_info.value)

    def test_list_subgraphs_raises_tool_error(self) -> None:
        import generic_graphql_mcp.adapters.inbound.mcp_stdio as mod

        with (
            patch.object(mod, "_get_client", return_value=_failing_client()),
            pytest.raises(ToolError) as exc_info,
        ):
            mod.list_subgraphs()
        assert "Schema unavailable" in str(exc_info.value)


# --- CLI adapter ---


class TestCLISchemaError:
    """CLI adapter prints clean error message and exits 1."""

    @pytest.fixture()
    def runner(self) -> CliRunner:
        return CliRunner()

    def test_introspect_exits_1(self, runner: CliRunner) -> None:
        with patch.object(GraphQLClient, "from_env", return_value=_failing_client()):
            result = runner.invoke(main, ["introspect"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_describe_type_exits_1(self, runner: CliRunner) -> None:
        with patch.object(GraphQLClient, "from_env", return_value=_failing_client()):
            result = runner.invoke(main, ["describe-type", "User"])
        assert result.exit_code == 1

    def test_list_subgraphs_exits_1(self, runner: CliRunner) -> None:
        with patch.object(GraphQLClient, "from_env", return_value=_failing_client()):
            result = runner.invoke(main, ["list-subgraphs"])
        assert result.exit_code == 1

    def test_no_traceback_in_output(self, runner: CliRunner) -> None:
        """Error output should not contain Python traceback."""
        with patch.object(GraphQLClient, "from_env", return_value=_failing_client()):
            result = runner.invoke(main, ["introspect"])
        assert "Traceback" not in result.output
