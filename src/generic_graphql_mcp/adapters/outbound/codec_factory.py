"""Codec auto-detection factory.

Returns the Rust native codec when available, orjson fallback otherwise.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from generic_graphql_mcp.ports.json_codec import JsonCodec


def get_codec() -> JsonCodec:
    """Return Rust codec if the native extension is available, orjson fallback otherwise."""
    try:
        from generic_graphql_mcp.adapters.outbound.json_native import RustJsonCodec

        return RustJsonCodec()
    except ImportError:
        from generic_graphql_mcp.adapters.outbound.json_orjson import OrjsonCodec

        return OrjsonCodec()
