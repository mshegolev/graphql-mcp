"""Pure-Python fallback JSON codec using orjson."""

from __future__ import annotations

from typing import Any

import orjson


class OrjsonCodec:
    """Pure-Python fallback JSON codec using orjson.

    Uses ``orjson.OPT_SORT_KEYS`` for deterministic, sorted-key output
    matching the Rust native codec.
    """

    def encode(self, obj: Any) -> bytes:
        """Serialize a Python object to JSON bytes with sorted keys."""
        return orjson.dumps(obj, option=orjson.OPT_SORT_KEYS)

    def decode(self, data: bytes) -> Any:
        """Deserialize JSON bytes to a Python object."""
        return orjson.loads(data)
