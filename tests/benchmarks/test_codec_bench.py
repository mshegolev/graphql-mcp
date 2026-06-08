"""Codec performance benchmarks: Rust native vs orjson fallback.

Run with: pytest --benchmark-enable tests/benchmarks/ -v
Or:       pytest --benchmark-only tests/benchmarks/ -v

Benchmarks are disabled by default (--benchmark-disable in pyproject.toml).
"""

from __future__ import annotations

import pytest

from graphql_mcp.adapters.outbound.json_orjson import OrjsonCodec

try:
    from graphql_mcp.adapters.outbound.json_native import RustJsonCodec

    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False


# --- OrjsonCodec benchmarks (always available) ---


class TestOrjsonBenchmarks:
    """Benchmark OrjsonCodec encode/decode on 100KB and 1MB payloads."""

    def test_orjson_encode_100kb(self, benchmark, payload_100kb):
        codec = OrjsonCodec()
        benchmark(codec.encode, payload_100kb)

    def test_orjson_decode_100kb(self, benchmark, encoded_100kb):
        codec = OrjsonCodec()
        benchmark(codec.decode, encoded_100kb)

    def test_orjson_encode_1mb(self, benchmark, payload_1mb):
        codec = OrjsonCodec()
        benchmark(codec.encode, payload_1mb)

    def test_orjson_decode_1mb(self, benchmark, encoded_1mb):
        codec = OrjsonCodec()
        benchmark(codec.decode, encoded_1mb)


# --- RustJsonCodec benchmarks (only when native extension built) ---


@pytest.mark.skipif(not HAS_NATIVE, reason="Rust native extension not built")
class TestRustBenchmarks:
    """Benchmark RustJsonCodec encode/decode on 100KB and 1MB payloads."""

    def test_rust_encode_100kb(self, benchmark, payload_100kb):
        codec = RustJsonCodec()
        benchmark(codec.encode, payload_100kb)

    def test_rust_decode_100kb(self, benchmark, encoded_100kb):
        codec = RustJsonCodec()
        benchmark(codec.decode, encoded_100kb)

    def test_rust_encode_1mb(self, benchmark, payload_1mb):
        codec = RustJsonCodec()
        benchmark(codec.encode, payload_1mb)

    def test_rust_decode_1mb(self, benchmark, encoded_1mb):
        codec = RustJsonCodec()
        benchmark(codec.decode, encoded_1mb)
