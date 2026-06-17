"""Tests for SSE (Server-Sent Events) subscription fallback endpoint.

Verifies GET /graphql/subscribe?query=...&variables=... returns text/event-stream
with data: lines containing JSON QueryResult payloads.
"""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any

import pytest
from websockets.asyncio.server import serve as ws_serve

from graphql_mcp.adapters.inbound.rest import app


# ---------------------------------------------------------------------------
# Mock WS server handler
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


_received_headers: dict[str, str] = {}


async def mock_ws_handler_with_auth(websocket: Any) -> None:
    """Mock upstream that records headers for auth verification."""
    global _received_headers
    # Capture request headers from the websocket connection
    _received_headers = dict(websocket.request.headers) if websocket.request else {}

    msg = json.loads(await websocket.recv())
    assert msg["type"] == "connection_init"
    await websocket.send(json.dumps({"type": "connection_ack"}))

    msg = json.loads(await websocket.recv())
    assert msg["type"] == "subscribe"
    sub_id = msg["id"]

    await websocket.send(
        json.dumps(
            {
                "type": "next",
                "id": sub_id,
                "payload": {"data": {"ok": True}},
            }
        )
    )
    await websocket.send(json.dumps({"type": "complete", "id": sub_id}))


# ---------------------------------------------------------------------------
# Helper: start mock WS server in background thread
# ---------------------------------------------------------------------------


def _start_threaded_ws_server(handler: Any = mock_ws_handler) -> tuple[int, threading.Thread]:
    """Start a mock WS server in a daemon thread, return (port, thread)."""
    server_ready = threading.Event()
    port_holder: list[int] = []

    def _run() -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _start() -> None:
            server = await ws_serve(handler, "127.0.0.1", 0)
            port_holder.append(server.sockets[0].getsockname()[1])
            server_ready.set()
            await asyncio.Future()  # keep alive

        try:
            loop.run_until_complete(_start())
        except asyncio.CancelledError:
            pass
        finally:
            loop.close()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    server_ready.wait(timeout=5)
    assert port_holder, "Mock WS server failed to start"
    return port_holder[0], t


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSSEEndpoint:
    def test_sse_endpoint_streams_events(self, monkeypatch: Any) -> None:
        """SSE endpoint streams 3 events from mock upstream."""
        port, _ = _start_threaded_ws_server()
        monkeypatch.setenv("GRAPHQL_SUBSCRIPTION_ENDPOINT", f"ws://127.0.0.1:{port}")

        from starlette.testclient import TestClient

        client = TestClient(app)
        resp = client.get(
            "/graphql/subscribe",
            params={"query": "subscription { counter }"},
        )

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        # Parse SSE data lines
        lines = resp.text.strip().split("\n")
        data_lines = [line for line in lines if line.startswith("data: ")]
        assert len(data_lines) == 3

        for i, data_line in enumerate(data_lines):
            payload = json.loads(data_line[len("data: ") :])
            assert payload["data"] == {"counter": i}
            assert payload["error_class"] == "ok"
            assert payload["errors"] == []

    def test_sse_endpoint_invalid_variables(self) -> None:
        """Invalid JSON in variables returns 400."""
        from starlette.testclient import TestClient

        client = TestClient(app)
        resp = client.get(
            "/graphql/subscribe",
            params={"query": "subscription { x }", "variables": "not-json"},
        )

        assert resp.status_code == 400
        body = resp.json()
        assert "Invalid JSON" in body["error"]

    def test_sse_endpoint_no_endpoint_configured(self, monkeypatch: Any) -> None:
        """No subscription endpoint returns 503."""
        monkeypatch.delenv("GRAPHQL_SUBSCRIPTION_ENDPOINT", raising=False)
        monkeypatch.delenv("GRAPHQL_ENDPOINT", raising=False)

        from starlette.testclient import TestClient

        client = TestClient(app)
        resp = client.get(
            "/graphql/subscribe",
            params={"query": "subscription { x }"},
        )

        assert resp.status_code == 503
        body = resp.json()
        assert "No subscription endpoint" in body["error"]

    def test_sse_endpoint_forwards_auth_headers(self, monkeypatch: Any) -> None:
        """Auth headers from HTTP request are forwarded to upstream WS."""
        global _received_headers
        _received_headers = {}

        port, _ = _start_threaded_ws_server(handler=mock_ws_handler_with_auth)
        monkeypatch.setenv("GRAPHQL_SUBSCRIPTION_ENDPOINT", f"ws://127.0.0.1:{port}")

        from starlette.testclient import TestClient

        client = TestClient(app)
        resp = client.get(
            "/graphql/subscribe",
            params={"query": "subscription { x }"},
            headers={"Authorization": "Bearer test-token-123"},
        )

        assert resp.status_code == 200
        # Verify the auth header reached the mock upstream
        assert "authorization" in _received_headers
        assert _received_headers["authorization"] == "Bearer test-token-123"

    def test_sse_endpoint_cache_control_headers(self, monkeypatch: Any) -> None:
        """SSE response has proper cache-control headers."""
        port, _ = _start_threaded_ws_server()
        monkeypatch.setenv("GRAPHQL_SUBSCRIPTION_ENDPOINT", f"ws://127.0.0.1:{port}")

        from starlette.testclient import TestClient

        client = TestClient(app)
        resp = client.get(
            "/graphql/subscribe",
            params={"query": "subscription { counter }"},
        )

        assert resp.headers.get("cache-control") == "no-cache"
        assert resp.headers.get("x-accel-buffering") == "no"
