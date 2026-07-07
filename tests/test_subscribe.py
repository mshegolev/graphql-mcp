"""Tests for AsyncGraphQLClient.subscribe() and the FastAPI WebSocket endpoint.

Group 1 — subscribe() async iterator on AsyncGraphQLClient.
Group 2 — WebSocket endpoint /graphql/subscribe protocol proxy.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any

import pytest
from websockets.asyncio.server import serve as ws_serve

from generic_graphql_mcp.adapters.inbound.async_lib import AsyncGraphQLClient
from generic_graphql_mcp.config import GraphQLConfig
from generic_graphql_mcp.domain.models import ErrorClass
from generic_graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import MockSchemaSource, SAMPLE_SDL


# ---------------------------------------------------------------------------
# Mock WS server handler (shared)
# ---------------------------------------------------------------------------


async def mock_ws_handler(websocket: Any) -> None:
    """Mock graphql-transport-ws upstream: 3 next messages then complete."""
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


def _make_async_client(**config_overrides: Any) -> AsyncGraphQLClient:
    """Build an AsyncGraphQLClient with mock schema and given config."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(**config_overrides)
    return AsyncGraphQLClient(schema_service=service, transport=None, config=config)


# ---------------------------------------------------------------------------
# Group 1: AsyncGraphQLClient.subscribe()
# ---------------------------------------------------------------------------


class TestAsyncClientSubscribe:
    async def test_async_client_subscribe_yields_results(self, ws_server: str) -> None:
        """subscribe() yields 3 QueryResult from mock server."""
        client = _make_async_client(subscription_endpoint=ws_server)

        results = []
        async for result in client.subscribe("subscription { counter }"):
            results.append(result)

        assert len(results) == 3
        for i, r in enumerate(results):
            assert r.data == {"counter": i}
            assert r.error_class == ErrorClass.OK

        await client.close()

    async def test_async_client_subscribe_no_endpoint(self) -> None:
        """subscribe() yields transport error when no endpoint configured."""
        client = _make_async_client()  # no endpoint set

        results = []
        async for result in client.subscribe("subscription { x }"):
            results.append(result)

        assert len(results) == 1
        assert results[0].error_class == ErrorClass.TRANSPORT
        assert "No subscription endpoint" in results[0].errors[0]["message"]

        await client.close()

    async def test_async_client_subscribe_resolves_ws_from_http(self) -> None:
        """_resolve_ws_endpoint converts http→ws and https→wss."""
        client_http = _make_async_client(endpoint="http://localhost:9999/graphql")
        assert client_http._resolve_ws_endpoint() == "ws://localhost:9999/graphql"

        client_https = _make_async_client(endpoint="https://api.example.com/graphql")
        assert client_https._resolve_ws_endpoint() == "wss://api.example.com/graphql"

        await client_http.close()
        await client_https.close()


# ---------------------------------------------------------------------------
# Group 2: WebSocket endpoint
# ---------------------------------------------------------------------------


class TestWSEndpoint:
    def test_ws_endpoint_full_protocol(self, monkeypatch: Any) -> None:
        """Full graphql-transport-ws protocol through the FastAPI WS endpoint."""
        import threading

        # Start a mock WS server in a background thread with its own event loop
        server_ready = threading.Event()
        server_port_holder: list[int] = []

        def _run_server() -> None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _start() -> None:
                server = await ws_serve(mock_ws_handler, "127.0.0.1", 0)
                port = server.sockets[0].getsockname()[1]
                server_port_holder.append(port)
                server_ready.set()
                # Keep server alive until cancelled
                await asyncio.Future()

            try:
                loop.run_until_complete(_start())
            except asyncio.CancelledError:
                pass
            finally:
                loop.close()

        t = threading.Thread(target=_run_server, daemon=True)
        t.start()
        server_ready.wait(timeout=5)
        assert server_port_holder, "Mock WS server failed to start"
        port = server_port_holder[0]

        monkeypatch.setenv("GRAPHQL_SUBSCRIPTION_ENDPOINT", f"ws://127.0.0.1:{port}")

        from starlette.testclient import TestClient
        from generic_graphql_mcp.adapters.inbound.rest import app

        client = TestClient(app)
        with client.websocket_connect(
            "/graphql/subscribe",
            subprotocols=["graphql-transport-ws"],
        ) as ws:
            # Send connection_init
            ws.send_json({"type": "connection_init"})
            ack = ws.receive_json()
            assert ack["type"] == "connection_ack"

            # Send subscribe
            ws.send_json(
                {
                    "type": "subscribe",
                    "id": "sub-1",
                    "payload": {"query": "subscription { counter }"},
                }
            )

            # Receive 3 next messages
            results = []
            for _ in range(3):
                msg = ws.receive_json()
                assert msg["type"] == "next"
                assert msg["id"] == "sub-1"
                results.append(msg["payload"])

            # Receive complete
            complete = ws.receive_json()
            assert complete["type"] == "complete"
            assert complete["id"] == "sub-1"

        assert len(results) == 3
        for i, payload in enumerate(results):
            assert payload["data"] == {"counter": i}

    def test_ws_endpoint_rejects_without_init(self, monkeypatch: Any) -> None:
        """WS endpoint returns error when client skips connection_init."""
        monkeypatch.setenv("GRAPHQL_SUBSCRIPTION_ENDPOINT", "ws://localhost:9999")

        from starlette.testclient import TestClient
        from generic_graphql_mcp.adapters.inbound.rest import app

        client = TestClient(app)
        with client.websocket_connect(
            "/graphql/subscribe",
            subprotocols=["graphql-transport-ws"],
        ) as ws:
            # Send subscribe directly (without connection_init)
            ws.send_json({"type": "subscribe", "id": "1", "payload": {"query": "sub { x }"}})
            error_msg = ws.receive_json()
            assert error_msg["type"] == "error"
            assert "Expected connection_init" in error_msg["payload"][0]["message"]
