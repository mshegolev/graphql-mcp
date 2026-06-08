"""Tests for GraphQLClient lifecycle management.

Verifies HARD-03: context manager, close(), atexit handler.
"""

from __future__ import annotations

import atexit
from unittest.mock import MagicMock, patch

import pytest

from graphql_mcp.adapters.inbound.lib import GraphQLClient
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _make_client_with_mock_transport() -> tuple[GraphQLClient, MagicMock]:
    """Create a GraphQLClient with a mock transport for lifecycle testing."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    mock_transport = MagicMock()
    mock_transport.close = MagicMock()
    client = GraphQLClient(schema_service=service, transport=mock_transport, config=config)
    return client, mock_transport


class TestContextManager:
    """GraphQLClient works as a context manager."""

    def test_context_manager_enter_returns_self(self) -> None:
        client, _ = _make_client_with_mock_transport()
        with client as ctx:
            assert ctx is client

    def test_context_manager_exit_closes_transport(self) -> None:
        client, mock_transport = _make_client_with_mock_transport()
        with client:
            pass
        mock_transport.close.assert_called_once()

    def test_context_manager_exit_on_exception(self) -> None:
        """Transport is closed even if exception occurs inside with block."""
        client, mock_transport = _make_client_with_mock_transport()
        with pytest.raises(ValueError, match="test error"), client:
            raise ValueError("test error")
        mock_transport.close.assert_called_once()

    def test_context_manager_no_transport(self) -> None:
        """Context manager works when transport is None (no crash)."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        with client:
            pass
        # No exception = pass


class TestExplicitClose:
    """GraphQLClient.close() works correctly."""

    def test_close_calls_transport_close(self) -> None:
        client, mock_transport = _make_client_with_mock_transport()
        client.close()
        mock_transport.close.assert_called_once()

    def test_close_idempotent(self) -> None:
        """Calling close() multiple times only closes transport once."""
        client, mock_transport = _make_client_with_mock_transport()
        client.close()
        client.close()
        client.close()
        mock_transport.close.assert_called_once()

    def test_close_with_no_transport(self) -> None:
        """close() does not crash when transport is None."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = GraphQLClient(schema_service=service, transport=None, config=config)
        client.close()  # Should not raise


class TestAtexitRegistration:
    """from_env() registers atexit handler."""

    def test_from_env_registers_atexit(self) -> None:
        """from_env() registers client.close with atexit."""
        with patch.object(atexit, "register") as mock_register:
            client = GraphQLClient.from_env(endpoint="https://example.com/graphql")
            mock_register.assert_called_once_with(client.close)

    def test_atexit_and_context_manager_both_safe(self) -> None:
        """If both atexit and context manager fire, transport closes only once."""
        client, mock_transport = _make_client_with_mock_transport()
        # Simulate context manager
        with client:
            pass
        # Simulate atexit firing after context manager
        client.close()
        # Should still be called only once due to _closed flag
        mock_transport.close.assert_called_once()


class TestOperationsAfterClose:
    """Client operations still work logically after close (no crash guarantee)."""

    def test_close_sets_closed_flag(self) -> None:
        client, _ = _make_client_with_mock_transport()
        assert not client._closed
        client.close()
        assert client._closed
