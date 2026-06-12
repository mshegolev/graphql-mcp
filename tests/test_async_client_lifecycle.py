"""Tests for AsyncGraphQLClient lifecycle management.

Verifies: async context manager, close(), atexit handler.
Async counterpart to test_client_lifecycle.py.
"""

from __future__ import annotations

import atexit
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from graphql_mcp.adapters.inbound.async_lib import AsyncGraphQLClient
from graphql_mcp.config import GraphQLConfig
from graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _make_async_client_with_mock_transport() -> tuple[AsyncGraphQLClient, MagicMock]:
    """Create an AsyncGraphQLClient with a mock transport for lifecycle testing."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    mock_transport = MagicMock()
    mock_transport.close = AsyncMock()
    mock_transport._client = MagicMock()
    mock_transport._client.is_closed = False
    client = AsyncGraphQLClient(schema_service=service, transport=mock_transport, config=config)
    return client, mock_transport


class TestAsyncContextManager:
    """AsyncGraphQLClient works as an async context manager."""

    async def test_context_manager_enter_returns_self(self) -> None:
        client, _ = _make_async_client_with_mock_transport()
        async with client as ctx:
            assert ctx is client

    async def test_context_manager_exit_closes_transport(self) -> None:
        client, mock_transport = _make_async_client_with_mock_transport()
        async with client:
            pass
        mock_transport.close.assert_awaited_once()

    async def test_context_manager_exit_on_exception(self) -> None:
        """Transport is closed even if exception occurs inside async with block."""
        client, mock_transport = _make_async_client_with_mock_transport()
        with pytest.raises(ValueError, match="test error"):
            async with client:
                raise ValueError("test error")
        mock_transport.close.assert_awaited_once()

    async def test_context_manager_no_transport(self) -> None:
        """Context manager works when transport is None (no crash)."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = AsyncGraphQLClient(schema_service=service, transport=None, config=config)
        async with client:
            pass
        # No exception = pass


class TestAsyncExplicitClose:
    """AsyncGraphQLClient.close() works correctly."""

    async def test_close_calls_transport_close(self) -> None:
        client, mock_transport = _make_async_client_with_mock_transport()
        await client.close()
        mock_transport.close.assert_awaited_once()

    async def test_close_idempotent(self) -> None:
        """Calling close() multiple times only closes transport once."""
        client, mock_transport = _make_async_client_with_mock_transport()
        await client.close()
        await client.close()
        await client.close()
        mock_transport.close.assert_awaited_once()

    async def test_close_with_no_transport(self) -> None:
        """close() does not crash when transport is None."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=0)
        config = GraphQLConfig(allow_mutations=False)
        client = AsyncGraphQLClient(schema_service=service, transport=None, config=config)
        await client.close()  # Should not raise

    async def test_close_sets_closed_flag(self) -> None:
        client, _ = _make_async_client_with_mock_transport()
        assert not client._closed
        await client.close()
        assert client._closed


class TestAsyncAtexitRegistration:
    """from_env() registers atexit handler."""

    def test_from_env_registers_atexit(self) -> None:
        """from_env() registers a cleanup function with atexit.

        Asserts on the registered function's identity rather than the call
        count: unrelated import-time registrations (e.g. certifi's
        exit_cacert_ctx in CI) can also fire inside the patch window.
        """
        with patch.object(atexit, "register") as mock_register:
            AsyncGraphQLClient.from_env(endpoint="https://example.com/graphql")
            registered = [
                getattr(call.args[0], "__qualname__", repr(call.args[0]))
                for call in mock_register.call_args_list
                if call.args
            ]
            assert any("_sync_cleanup" in name for name in registered), (
                f"from_env did not register _sync_cleanup; got: {registered}"
            )

    async def test_atexit_and_context_manager_both_safe(self) -> None:
        """If both atexit and context manager fire, transport closes only once."""
        client, mock_transport = _make_async_client_with_mock_transport()
        # Simulate context manager
        async with client:
            pass
        # Simulate atexit firing after context manager (close already called)
        await client.close()
        # Should still be called only once due to _closed flag
        mock_transport.close.assert_awaited_once()
