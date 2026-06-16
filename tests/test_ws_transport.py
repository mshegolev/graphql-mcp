"""Tests for upstream WebSocket transport (graphql-transport-ws sub-protocol).

Uses a real in-process websockets server to validate the full protocol lifecycle.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any
from unittest.mock import patch

import pytest
from websockets.asyncio.server import serve as ws_serve

from graphql_mcp.domain.models import ErrorClass


# ---------------------------------------------------------------------------
# Mock WS server handlers
# ---------------------------------------------------------------------------


async def mock_ws_handler(websocket: Any) -> None:
    """Mock graphql-transport-ws upstream server: sends 3 next messages then complete."""
    msg = json.loads(await websocket.recv())
    assert msg["type"] == "connection_init"
    await websocket.send(json.dumps({"type": "connection_ack"}))

    msg = json.loads(await websocket.recv())
    assert msg["type"] == "subscribe"
    sub_id = msg["id"]

    for i in range(3):
        await websocket.send(
            json.dumps(
                {
                    "type": "next",
                    "id": sub_id,
                    "payload": {"data": {"counter": i}},
                }
            )
        )
    await websocket.send(json.dumps({"type": "complete", "id": sub_id}))


async def mock_ws_error_handler(websocket: Any) -> None:
    """Mock server that sends an error message."""
    msg = json.loads(await websocket.recv())
    assert msg["type"] == "connection_init"
    await websocket.send(json.dumps({"type": "connection_ack"}))

    msg = json.loads(await websocket.recv())
    assert msg["type"] == "subscribe"
    sub_id = msg["id"]

    await websocket.send(
        json.dumps(
            {
                "type": "error",
                "id": sub_id,
                "payload": [{"message": "Subscription field not found"}],
            }
        )
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
async def ws_server():
    """Start a mock WS server and return its URI."""
    server = await ws_serve(mock_ws_handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    uri = f"ws://127.0.0.1:{port}"
    yield uri
    server.close()
    await server.wait_closed()


@pytest.fixture()
async def ws_error_server():
    """Start a mock WS server that sends error messages."""
    server = await ws_serve(mock_ws_error_handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    uri = f"ws://127.0.0.1:{port}"
    yield uri
    server.close()
    await server.wait_closed()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWSTransportReceive:
    async def test_ws_transport_receives_subscription_results(self, ws_server: str) -> None:
        """UpstreamWSTransport receives 3 QueryResult from mock server."""
        from graphql_mcp.adapters.outbound.ws_transport import UpstreamWSTransport

        results = []
        async with UpstreamWSTransport(
            ws_endpoint=ws_server,
            query="subscription { counter }",
        ) as transport:
            async for result in transport:
                results.append(result)

        assert len(results) == 3
        for i, r in enumerate(results):
            assert r.data == {"counter": i}
            assert r.error_class == ErrorClass.OK
            assert r.errors == []


class TestWSTransportError:
    async def test_ws_transport_handles_error_message(self, ws_error_server: str) -> None:
        """UpstreamWSTransport yields error QueryResult when upstream sends type:error."""
        from graphql_mcp.adapters.outbound.ws_transport import UpstreamWSTransport

        results = []
        async with UpstreamWSTransport(
            ws_endpoint=ws_error_server,
            query="subscription { invalid }",
        ) as transport:
            async for result in transport:
                results.append(result)

        assert len(results) == 1
        assert results[0].error_class == ErrorClass.GRAPHQL
        assert results[0].errors[0]["message"] == "Subscription field not found"


class TestWSTransportClose:
    async def test_ws_transport_clean_close(self, ws_server: str) -> None:
        """WS connection is properly closed after complete."""
        from graphql_mcp.adapters.outbound.ws_transport import UpstreamWSTransport

        transport = UpstreamWSTransport(
            ws_endpoint=ws_server,
            query="subscription { counter }",
        )
        async with transport:
            async for _ in transport:
                pass

        assert transport._closed is True


class TestWSTransportImportGuard:
    def test_ws_transport_import_guard(self) -> None:
        """ImportError raised with install instructions when websockets is missing."""
        import graphql_mcp.adapters.outbound.ws_transport as ws_mod

        original_ws = ws_mod.websockets
        try:
            ws_mod.websockets = None
            with pytest.raises(ImportError, match="pip install graphql-mcp\\[subscriptions\\]"):
                ws_mod.UpstreamWSTransport(
                    ws_endpoint="ws://localhost:9999",
                    query="subscription { x }",
                )
        finally:
            ws_mod.websockets = original_ws
