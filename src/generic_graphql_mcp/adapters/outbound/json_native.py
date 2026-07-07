"""Rust-backed JSON codec via pyo3 native extension."""

from __future__ import annotations

from typing import Any


class RustJsonCodec:
    """Rust-backed JSON codec via pyo3 native extension.

    Wraps the ``generic_graphql_mcp._native`` module built with maturin.
    Uses serde_json under the hood with sorted keys for deterministic output.
    """

    def __init__(self) -> None:
        from generic_graphql_mcp._native import decode, encode  # type: ignore[import-not-found]

        self._encode = encode
        self._decode = decode

    def encode(self, obj: Any) -> bytes:
        """Serialize a Python object to JSON bytes with sorted keys."""
        return bytes(self._encode(obj))

    def decode(self, data: bytes) -> Any:
        """Deserialize JSON bytes to a Python object."""
        return self._decode(data)
