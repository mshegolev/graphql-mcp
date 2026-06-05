from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class JsonCodec(Protocol):
    """Port: JSON encode/decode. Phase 3 provides Rust and orjson adapters."""

    def encode(self, obj: Any) -> bytes:
        """Serialize a Python object to JSON bytes."""
        ...

    def decode(self, data: bytes) -> Any:
        """Deserialize JSON bytes to a Python object."""
        ...
