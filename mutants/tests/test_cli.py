"""Tests for Click CLI inbound adapter.

Covers: query, introspect, describe-type, list-subgraphs, refresh commands.
"""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from graphql_mcp.adapters.inbound.cli import main
from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _mock_client() -> GraphQLClient:
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    return GraphQLClient(schema_service=service, transport=None, config=config)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock_from_env():
    with patch.object(GraphQLClient, "from_env", return_value=_mock_client()) as m:
        yield m


class TestCLIIntrospect:
    def test_introspect_outputs_json(self, runner: CliRunner, mock_from_env) -> None:
        result = runner.invoke(main, ["introspect"])
        assert result.exit_code == 0
        body = json.loads(result.output)
        assert "query_fields" in body
        assert "hello" in body["query_fields"]


class TestCLIDescribeType:
    def test_describe_type_outputs_json(self, runner: CliRunner, mock_from_env) -> None:
        result = runner.invoke(main, ["describe-type", "User"])
        assert result.exit_code == 0
        body = json.loads(result.output)
        assert body["name"] == "User"

    def test_describe_type_missing_exits_1(self, runner: CliRunner, mock_from_env) -> None:
        result = runner.invoke(main, ["describe-type", "NonExistent"])
        assert result.exit_code == 1


class TestCLIListSubgraphs:
    def test_list_subgraphs_outputs_json(self, runner: CliRunner, mock_from_env) -> None:
        result = runner.invoke(main, ["list-subgraphs"])
        assert result.exit_code == 0
        body = json.loads(result.output)
        assert isinstance(body, list)


class TestCLIRefresh:
    def test_refresh_outputs_ok(self, runner: CliRunner, mock_from_env) -> None:
        result = runner.invoke(main, ["refresh"])
        assert result.exit_code == 0
        body = json.loads(result.output)
        assert body["status"] == "refreshed"


class TestCLIEntities:
    def test_entities_no_transport(self, runner: CliRunner, mock_from_env) -> None:
        result = runner.invoke(
            main,
            ["entities", '[{"__typename": "Product", "id": "123"}]'],
        )
        assert result.exit_code == 0
        body = json.loads(result.output)
        assert body["error_class"] == "transport"


class TestCLIQuery:
    def test_query_no_transport(self, runner: CliRunner, mock_from_env) -> None:
        """query command with no transport returns transport error in JSON."""
        result = runner.invoke(main, ["query", "{ hello }"])
        assert result.exit_code == 0
        body = json.loads(result.output)
        assert body["error_class"] == "transport"
