"""Upstream WebSocket transport using the graphql-transport-ws sub-protocol.

Connects to an upstream GraphQL WS endpoint and yields QueryResult objects
from subscription messages. Manages connection lifecycle, backpressure via
bounded queue, and clean shutdown.

Requires the ``websockets`` library (``pip install generic-graphql-mcp[subscriptions]``).
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator

from generic_graphql_mcp.domain.models import ErrorClass, QueryResult

logger = logging.getLogger(__name__)

try:
    import websockets  # type: ignore[import-untyped]
    from websockets.asyncio.client import connect as ws_connect  # type: ignore[import-untyped]
except ImportError:
    websockets = None  # type: ignore[assignment]
    ws_connect = None  # type: ignore[assignment]

_WS_IMPORT_ERROR = (
    "websockets is required for subscription support. Install it with: pip install generic-graphql-mcp[subscriptions]"
)


class UpstreamWSTransport:
    """Connects to an upstream GraphQL WS endpoint using graphql-transport-ws sub-protocol.

    Yields QueryResult objects from upstream subscription messages.
    Manages connection lifecycle, backpressure via bounded queue, and clean shutdown.
    """

    def __init__(
        self,
        ws_endpoint: str,
        query: str,
        variables: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
        queue_size: int = 128,
        timeout: float = 30.0,
    ) -> None:
        if websockets is None:
            raise ImportError(_WS_IMPORT_ERROR)

        self._ws_endpoint = ws_endpoint
        self._query = query
        self._variables = variables
        self._extra_headers = extra_headers
        self._queue_size = queue_size
        self._timeout = timeout
        self._ws: Any = None
        self._reader_task: asyncio.Task[None] | None = None
        self._queue: asyncio.Queue[QueryResult | None] = asyncio.Queue(maxsize=queue_size)
        self._closed = False

    async def _connect(self) -> None:
        """Establish WS connection, perform graphql-transport-ws handshake, start reader."""
        self._ws = await ws_connect(
            self._ws_endpoint,
            subprotocols=["graphql-transport-ws"],
            additional_headers=self._extra_headers or {},
            open_timeout=self._timeout,
            close_timeout=self._timeout,
        )

        # Send connection_init
        await self._ws.send(json.dumps({"type": "connection_init", "payload": {}}))

        # Wait for connection_ack
        raw = await asyncio.wait_for(self._ws.recv(), timeout=self._timeout)
        ack = json.loads(raw)
        if ack.get("type") != "connection_ack":
            raise ConnectionError(f"Expected connection_ack, got {ack.get('type')}")

        # Send subscribe
        await self._ws.send(
            json.dumps(
                {
                    "type": "subscribe",
                    "id": "1",
                    "payload": {
                        "query": self._query,
                        "variables": self._variables or {},
                    },
                }
            )
        )

        # Start reader task
        self._reader_task = asyncio.create_task(self._reader_loop())

    async def _reader_loop(self) -> None:
        """Read messages from upstream WS and put parsed results on the queue."""
        try:
            async for raw_msg in self._ws:
                msg = json.loads(raw_msg)
                msg_type = msg.get("type")

                if msg_type == "next":
                    payload = msg.get("payload", {})
                    data = payload.get("data")
                    errors = payload.get("errors", [])
                    error_class = ErrorClass.GRAPHQL if errors else ErrorClass.OK
                    result = QueryResult(data=data, errors=errors, error_class=error_class)
                    await self._queue.put(result)

                elif msg_type == "error":
                    payload = msg.get("payload", [])
                    errors = payload if isinstance(payload, list) else [payload]
                    result = QueryResult(
                        data=None,
                        errors=errors,
                        error_class=ErrorClass.GRAPHQL,
                    )
                    await self._queue.put(result)
                    await self._queue.put(None)  # sentinel — end of stream
                    return

                elif msg_type == "complete":
                    await self._queue.put(None)  # sentinel — end of stream
                    return

        except asyncio.CancelledError:
            return
        except Exception as exc:
            logger.warning("Upstream WS disconnected: %s", exc)
            result = QueryResult(
                data=None,
                errors=[{"message": "Upstream WebSocket disconnected"}],
                error_class=ErrorClass.TRANSPORT,
            )
            await self._queue.put(result)
            await self._queue.put(None)  # sentinel — end of stream

    async def __aiter__(self) -> AsyncIterator[QueryResult]:
        """Yield QueryResult objects from the upstream subscription."""
        while True:
            item = await self._queue.get()
            if item is None:
                break
            yield item

    async def close(self) -> None:
        """Cancel reader task and close the WebSocket connection."""
        if self._closed:
            return
        self._closed = True

        if self._reader_task is not None and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._ws is not None:
            try:
                await self._ws.send(json.dumps({"type": "complete", "id": "1"}))
            except Exception:
                pass  # WS may already be closed
            try:
                await self._ws.close()
            except Exception:
                pass

    async def __aenter__(self) -> UpstreamWSTransport:
        await self._connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        await self.close()
