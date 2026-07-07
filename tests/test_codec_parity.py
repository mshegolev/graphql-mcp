"""Parity tests: RustJsonCodec and OrjsonCodec must produce byte-identical output.

Covers GQL-10 parity requirement: Rust native and orjson fallback at parity under test.
"""

from __future__ import annotations

import pytest

from generic_graphql_mcp.adapters.outbound.json_orjson import OrjsonCodec
from generic_graphql_mcp.ports.json_codec import JsonCodec

# Try importing RustJsonCodec; skip Rust tests if not built
try:
    from generic_graphql_mcp.adapters.outbound.json_native import RustJsonCodec

    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


@pytest.fixture()
def rust_codec():
    if not HAS_NATIVE:
        pytest.skip("Rust native extension not built")
    return RustJsonCodec()


@pytest.fixture()
def orjson_codec():
    return OrjsonCodec()


# --- Protocol conformance ---


class TestProtocolConformance:
    """Both codecs satisfy the JsonCodec Protocol."""

    def test_orjson_is_json_codec(self, orjson_codec):
        assert isinstance(orjson_codec, JsonCodec)

    def test_rust_is_json_codec(self, rust_codec):
        assert isinstance(rust_codec, JsonCodec)


# --- Byte-identical parity ---

PARITY_CASES = [
    # Simple types
    ({"a": 1}, "simple_dict"),
    ({"b": 2, "a": 1}, "unsorted_keys"),
    ([1, 2, 3], "list"),
    ("hello", "string"),
    (42, "integer"),
    (3.14, "float"),
    (True, "bool_true"),
    (False, "bool_false"),
    (None, "null"),
    # Nested
    ({"z": {"b": 2, "a": 1}, "a": [3, 2, 1]}, "nested_unsorted"),
    (
        {"data": {"users": [{"name": "Alice", "id": "1"}, {"name": "Bob", "id": "2"}]}},
        "graphql_response_shape",
    ),
    # Edge cases
    ({}, "empty_dict"),
    ([], "empty_list"),
    ({"": "empty_key"}, "empty_string_key"),
    ({"emoji": "\U0001f600\U0001f389"}, "unicode"),
    ({"special": "line\nbreak\ttab"}, "escape_chars"),
]


class TestByteParity:
    """RustJsonCodec and OrjsonCodec produce byte-identical output."""

    @pytest.mark.parametrize("obj,label", PARITY_CASES, ids=[c[1] for c in PARITY_CASES])
    def test_encode_parity(self, rust_codec, orjson_codec, obj, label):
        rust_out = rust_codec.encode(obj)
        orjson_out = orjson_codec.encode(obj)
        assert rust_out == orjson_out, f"Parity failure on {label}:\n  rust:   {rust_out!r}\n  orjson: {orjson_out!r}"

    @pytest.mark.parametrize("obj,label", PARITY_CASES, ids=[c[1] for c in PARITY_CASES])
    def test_roundtrip_parity(self, rust_codec, orjson_codec, obj, label):
        """Encode with one, decode with the other — round-trip works."""
        rust_encoded = rust_codec.encode(obj)
        orjson_decoded = orjson_codec.decode(rust_encoded)

        orjson_encoded = orjson_codec.encode(obj)
        rust_decoded = rust_codec.decode(orjson_encoded)

        # Decoded values should be equal
        assert rust_decoded == orjson_decoded


# --- Large payload parity ---


def _make_large_payload(n_keys: int) -> dict:
    """Generate a dict with n_keys entries, deeply nested."""
    return {
        f"field_{i:04d}": {
            "value": i,
            "nested": {"z_key": True, "a_key": f"val_{i}"},
            "list": [i, i + 1, i + 2],
        }
        for i in range(n_keys)
    }


class TestLargePayloadParity:
    """Parity on larger payloads (100KB+ and 1MB+ when serialized)."""

    def test_100kb_parity(self, rust_codec, orjson_codec):
        payload = _make_large_payload(1200)  # ~100KB
        rust_out = rust_codec.encode(payload)
        orjson_out = orjson_codec.encode(payload)
        assert len(rust_out) > 100_000, f"Payload too small: {len(rust_out)} bytes"
        assert rust_out == orjson_out

    def test_1mb_parity(self, rust_codec, orjson_codec):
        payload = _make_large_payload(12000)  # ~1MB
        rust_out = rust_codec.encode(payload)
        orjson_out = orjson_codec.encode(payload)
        assert len(rust_out) > 1_000_000, f"Payload too small: {len(rust_out)} bytes"
        assert rust_out == orjson_out


# --- Codec factory ---


class TestCodecFactory:
    """get_codec() auto-detection."""

    def test_get_codec_returns_codec(self):
        from generic_graphql_mcp.adapters.outbound.codec_factory import get_codec

        codec = get_codec()
        assert isinstance(codec, JsonCodec)

    def test_get_codec_returns_rust_when_available(self):
        from generic_graphql_mcp.adapters.outbound.codec_factory import get_codec

        codec = get_codec()
        if HAS_NATIVE:
            assert type(codec).__name__ == "RustJsonCodec"
        else:
            assert type(codec).__name__ == "OrjsonCodec"


# --- Edge case: float precision ---


class TestFloatParity:
    """Verify float formatting matches between codecs."""

    @pytest.mark.parametrize("val", [0.1, 0.2, 0.3, 1e-7, 1e15, -0.0, 1.0])
    def test_float_encode_parity(self, rust_codec, orjson_codec, val):
        rust_out = rust_codec.encode({"v": val})
        orjson_out = orjson_codec.encode({"v": val})
        assert rust_out == orjson_out, (
            f"Float parity failure for {val}:\n  rust:   {rust_out!r}\n  orjson: {orjson_out!r}"
        )
