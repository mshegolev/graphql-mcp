"""Synchronous WebSocket transport wrapper for GraphQL subscriptions.

Wraps the async UpstreamWSTransport in a synchronous interface using
a background thread and queue.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import queue
import threading
from typing import TYPE_CHECKING, Any

from generic_graphql_mcp.domain.models import ErrorClass, QueryResult

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)

try:
    import websockets  # type: ignore[import-untyped]
except ImportError:
    websockets = None  # type: ignore[assignment]


class SyncWSTransport:
    """Synchronous wrapper around async UpstreamWSTransport.

    Runs the async transport in a background thread and exposes a synchronous
    iterator interface.
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
            raise ImportError(
                "websockets is required for subscription support. "
                "Install it with: pip install generic-graphql-mcp[subscriptions]"
            )

        self._ws_endpoint = ws_endpoint
        self._query = query
        self._variables = variables
        self._extra_headers = extra_headers
        self._queue_size = queue_size
        self._timeout = timeout
        self._result_queue: queue.Queue[QueryResult | None] = queue.Queue(maxsize=queue_size)
        self._thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._closed = False

    def _run_async_transport(self) -> None:
        """Run the async transport in a background thread."""
        # Create a new event loop for this thread
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        try:
            self._loop.run_until_complete(self._async_worker())
        except Exception as exc:
            logger.exception("Async transport worker failed: %s", exc)
            # Put an error result on the queue
            error_result = QueryResult(
                data=None,
                errors=[{"message": f"Subscription transport error: {exc}"}],
                error_class=ErrorClass.TRANSPORT,
            )
            with contextlib.suppress(queue.Full):
                self._result_queue.put_nowait(error_result)
        finally:
            # Signal end of stream
            with contextlib.suppress(queue.Full):
                self._result_queue.put_nowait(None)

    async def _async_worker(self) -> None:
        """Async worker that runs the UpstreamWSTransport."""
        from generic_graphql_mcp.adapters.outbound.ws_transport import UpstreamWSTransport

        async with UpstreamWSTransport(
            ws_endpoint=self._ws_endpoint,
            query=self._query,
            variables=self._variables,
            extra_headers=self._extra_headers,
            queue_size=self._queue_size,
            timeout=self._timeout,
        ) as transport:
            async for result in transport:
                # Put result on the sync queue
                try:
                    self._result_queue.put_nowait(result)
                except queue.Full:
                    logger.warning("Subscription result queue full, dropping result")
                    break

    def __iter__(self) -> Iterator[QueryResult]:
        """Start the transport and yield QueryResult objects."""
        if self._closed:
            raise RuntimeError("Transport is closed")

        # Start the background thread
        self._thread = threading.Thread(target=self._run_async_transport, daemon=True)
        self._thread.start()

        # Yield results from the queue
        while True:
            try:
                result = self._result_queue.get(timeout=1.0)
                if result is None:
                    # End of stream
                    break
                yield result
            except queue.Empty:
                # Check if thread is still alive
                if self._thread and not self._thread.is_alive():
                    # Thread died, break out
                    break
                # Continue waiting
                continue

    def close(self) -> None:
        """Close the transport and clean up resources."""
        if self._closed:
            return
        self._closed = True

        # Cancel the async loop if it exists
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        # Wait for thread to finish
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5.0)

    def __enter__(self) -> SyncWSTransport:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.close()
