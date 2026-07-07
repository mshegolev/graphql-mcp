"""MCP-over-HTTP inbound adapter — exposes GraphQLClient operations via streamable HTTP.

Mounted as a sub-app on the FastAPI application at /mcp.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.applications import Starlette

from generic_graphql_mcp.adapters.inbound.mcp_stdio import mcp


def create_mcp_http_app() -> Starlette:
    """Return a Starlette ASGI app that serves MCP over streamable HTTP.

    Reuses the same FastMCP instance (and its registered tools) from mcp_stdio.
    The streamable_http_path is set to "/" so that when mounted at /mcp on the
    FastAPI app, the effective endpoint is /mcp (not /mcp/mcp).
    """
    mcp.settings.streamable_http_path = "/"
    return mcp.streamable_http_app()
