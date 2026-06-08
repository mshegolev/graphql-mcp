"""Tests proving AsyncHttpTransport mirrors sync HttpTransport behavior.

Verifies PERF-01: async transport with 3-class error classification (ok/graphql/transport),
codec injection, lifecycle management, and protocol conformance.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
import respx

from graphql_mcp.adapters.outbound.async_http_transport import AsyncHttpTransport
from graphql_mcp.domain.models import ErrorClass


class SpyCodec:
    """A codec that records calls for assertion."""

    def __init__(self) -> None:
        self.encode_calls: list[Any] = []
        self.decode_calls: list[bytes] = []

    def encode(self, obj: Any) -> bytes:
        self.encode_calls.append(obj)
        import orjson

        return orjson.dumps(obj)

    def decode(self, data: bytes) -> Any:
        self.decode_calls.append(data)
        import orjson

        return orjson.loads(data)


class TestAsyncHttpTransportErrorClassification:
    """Tests 1-4: error_class for ok/graphql/transport matches sync behavior."""

    @respx.mock
    async def test_execute_ok_returns_ok_class(self) -> None:
        """execute() on 200+data returns ErrorClass.OK with data."""
        respx.post("https://example.com/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}, "errors": []})
        )

        transport = AsyncHttpTransport("https://example.com/")
        result = await transport.execute("{ hello }")

        assert result.error_class == ErrorClass.OK
        assert result.data == {"hello": "world"}
        assert result.errors == []

    @respx.mock
    async def test_execute_graphql_errors_returns_graphql_class(self) -> None:
        """execute() on 200+errors returns ErrorClass.GRAPHQL."""
        respx.post("https://example.com/").mock(
            return_value=httpx.Response(200, json={"data": None, "errors": [{"message": "field not found"}]})
        )

        transport = AsyncHttpTransport("https://example.com/")
        result = await transport.execute("{ invalid }")

        assert result.error_class == ErrorClass.GRAPHQL
        assert result.data is None
        assert len(result.errors) == 1
        assert result.errors[0]["message"] == "field not found"

    @respx.mock
    async def test_execute_http_500_returns_transport_class(self) -> None:
        """execute() on HTTP 500 returns ErrorClass.TRANSPORT."""
        respx.post("https://example.com/").mock(return_value=httpx.Response(500, text="Internal Server Error"))

        transport = AsyncHttpTransport("https://example.com/")
        result = await transport.execute("{ x }")

        assert result.error_class == ErrorClass.TRANSPORT
        assert result.data is None
        assert "HTTP 500" in result.errors[0]["message"]

    @respx.mock
    async def test_execute_connect_error_returns_transport_class(self) -> None:
        """execute() on ConnectError returns ErrorClass.TRANSPORT."""
        respx.post("https://example.com/").mock(side_effect=httpx.ConnectError("Connection refused"))

        transport = AsyncHttpTransport("https://example.com/")
        result = await transport.execute("{ x }")

        assert result.error_class == ErrorClass.TRANSPORT
        assert result.data is None
        assert "Transport error" in result.errors[0]["message"]


class TestAsyncHttpTransportUsesCodec:
    """Tests 5-8: codec injection and factory default."""

    @respx.mock
    async def test_execute_uses_injected_codec(self) -> None:
        """execute() calls codec.encode for request and codec.decode for response."""
        spy = SpyCodec()
        respx.post("https://example.com/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}, "errors": []})
        )

        transport = AsyncHttpTransport("https://example.com/", codec=spy)
        result = await transport.execute("{ hello }")

        assert len(spy.encode_calls) == 1
        assert spy.encode_calls[0] == {"query": "{ hello }"}
        assert len(spy.decode_calls) == 1
        assert result.data == {"hello": "world"}
        assert result.error_class == ErrorClass.OK

    @respx.mock
    async def test_post_raw_uses_codec(self) -> None:
        """post_raw() also uses codec for encode/decode."""
        spy = SpyCodec()
        respx.post("https://example.com/").mock(
            return_value=httpx.Response(200, json={"data": None, "errors": [{"message": "oops"}]})
        )

        transport = AsyncHttpTransport("https://example.com/", codec=spy)
        result = await transport.post_raw({"query": "{ broken }", "variables": {"x": 1}})

        assert len(spy.encode_calls) == 1
        assert spy.encode_calls[0] == {"query": "{ broken }", "variables": {"x": 1}}
        assert result.error_class == ErrorClass.GRAPHQL

    async def test_default_codec_from_factory(self) -> None:
        """When no codec passed, AsyncHttpTransport uses get_codec() factory."""
        from graphql_mcp.ports.json_codec import JsonCodec

        transport = AsyncHttpTransport("https://example.com/")
        assert isinstance(transport._codec, JsonCodec)

    @respx.mock
    async def test_codec_decode_error_returns_transport_error(self) -> None:
        """If codec.decode raises ValueError, result is TRANSPORT error."""
        bad_codec = MagicMock()
        bad_codec.encode.return_value = b'{"query":"{ x }"}'
        bad_codec.decode.side_effect = ValueError("bad json")

        respx.post("https://example.com/").mock(return_value=httpx.Response(200, content=b"not-json"))

        transport = AsyncHttpTransport("https://example.com/", codec=bad_codec)
        result = await transport.execute("{ x }")

        assert result.error_class == ErrorClass.TRANSPORT
        assert "Invalid JSON" in result.errors[0]["message"]


class TestAsyncHttpTransportLifecycle:
    """Test 9: close lifecycle."""

    async def test_close_calls_aclose_on_underlying_client(self) -> None:
        """close() calls aclose on underlying httpx.AsyncClient."""
        transport = AsyncHttpTransport("https://example.com/")
        assert not transport._client.is_closed

        await transport.close()
        assert transport._client.is_closed


class TestAsyncProtocolConformance:
    """Test 10: protocol conformance check."""

    async def test_async_transport_is_instance_of_protocol(self) -> None:
        """AsyncHttpTransport satisfies AsyncGraphQLTransport protocol."""
        from graphql_mcp.ports.transport import AsyncGraphQLTransport

        transport = AsyncHttpTransport("https://example.com/")
        assert isinstance(transport, AsyncGraphQLTransport)
