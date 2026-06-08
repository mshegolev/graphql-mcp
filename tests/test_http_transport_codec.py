"""Tests proving HttpTransport uses the JsonCodec port, not bare orjson.

Verifies HARD-01: codec factory wiring into transport.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import respx

from graphql_mcp.adapters.outbound.http_transport import HttpTransport
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


class TestHttpTransportUsesCodec:
    """Verify HttpTransport delegates to injected codec, not bare orjson."""

    @respx.mock
    def test_execute_uses_codec_encode_and_decode(self) -> None:
        """execute() calls codec.encode for request and codec.decode for response."""
        spy = SpyCodec()
        respx.post("https://example.com/").mock(
            return_value=httpx.Response(200, json={"data": {"hello": "world"}, "errors": []})
        )

        transport = HttpTransport("https://example.com/", codec=spy)
        result = transport.execute("{ hello }")

        assert len(spy.encode_calls) == 1
        assert spy.encode_calls[0] == {"query": "{ hello }"}
        assert len(spy.decode_calls) == 1
        assert result.data == {"hello": "world"}
        assert result.error_class == ErrorClass.OK

    @respx.mock
    def test_post_raw_uses_codec(self) -> None:
        """post_raw() also uses codec for encode/decode."""
        spy = SpyCodec()
        respx.post("https://example.com/").mock(
            return_value=httpx.Response(200, json={"data": None, "errors": [{"message": "oops"}]})
        )

        transport = HttpTransport("https://example.com/", codec=spy)
        result = transport.post_raw({"query": "{ broken }", "variables": {"x": 1}})

        assert len(spy.encode_calls) == 1
        assert spy.encode_calls[0] == {"query": "{ broken }", "variables": {"x": 1}}
        assert result.error_class == ErrorClass.GRAPHQL

    def test_default_codec_from_factory(self) -> None:
        """When no codec passed, HttpTransport uses get_codec() factory."""
        from graphql_mcp.ports.json_codec import JsonCodec

        transport = HttpTransport("https://example.com/")
        assert isinstance(transport._codec, JsonCodec)

    @respx.mock
    def test_codec_decode_error_returns_transport_error(self) -> None:
        """If codec.decode raises ValueError, result is TRANSPORT error."""
        bad_codec = MagicMock()
        bad_codec.encode.return_value = b'{"query":"{ x }"}'
        bad_codec.decode.side_effect = ValueError("bad json")

        respx.post("https://example.com/").mock(return_value=httpx.Response(200, content=b"not-json"))

        transport = HttpTransport("https://example.com/", codec=bad_codec)
        result = transport.execute("{ x }")

        assert result.error_class == ErrorClass.TRANSPORT
        assert "Invalid JSON" in result.errors[0]["message"]


class TestNoOrjsonInTransport:
    """Verify the orjson import has been removed from http_transport.py."""

    def test_no_orjson_in_module_dict(self) -> None:
        import graphql_mcp.adapters.outbound.http_transport as mod

        source_file = mod.__file__
        with open(source_file) as f:
            source = f.read()
        assert "import orjson" not in source
        assert "orjson.dumps" not in source
        assert "orjson.loads" not in source
