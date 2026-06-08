"""Tests for `graphql-mcp serve` CLI command."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from graphql_mcp.adapters.inbound.cli import main


class TestServeCommand:
    def test_serve_command_exists(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Start the FastAPI server" in result.output

    @patch("uvicorn.run")
    def test_serve_calls_uvicorn_with_defaults(self, mock_run) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == "graphql_mcp.adapters.inbound.rest:app"
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000

    @patch("uvicorn.run")
    def test_serve_respects_host_port_options(self, mock_run) -> None:
        runner = CliRunner()
        result = runner.invoke(main, ["serve", "--host", "127.0.0.1", "--port", "9000"])
        assert result.exit_code == 0
        _, kwargs = mock_run.call_args
        assert kwargs["host"] == "127.0.0.1"
        assert kwargs["port"] == 9000

    @patch("uvicorn.run")
    def test_serve_uses_env_config_when_no_cli_options(self, mock_run) -> None:
        """Without CLI flags, serve reads from GraphQLConfig (env vars)."""
        runner = CliRunner()
        result = runner.invoke(main, ["serve"])
        assert result.exit_code == 0
        _, kwargs = mock_run.call_args
        # Defaults from GraphQLConfig
        assert kwargs["host"] == "0.0.0.0"
        assert kwargs["port"] == 8000
