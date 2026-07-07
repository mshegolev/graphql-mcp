"""Tests for MCP-over-HTTP inbound adapter.

Verifies that MCP tools are accessible via streamable HTTP transport
mounted on the FastAPI app at /mcp.  Uses Starlette TestClient to invoke
the sub-app directly (with lifespan) so the session manager is initialised.
"""

from __future__ import annotations

import json

import pytest
from starlette.testclient import TestClient

from generic_graphql_mcp.adapters.inbound.lib import GraphQLClient
from generic_graphql_mcp.adapters.inbound.mcp_http import create_mcp_http_app
from generic_graphql_mcp.adapters.inbound.mcp_stdio import mcp as mcp_instance
from generic_graphql_mcp.adapters.inbound.rest import set_client
from generic_graphql_mcp.config import GraphQLConfig
from generic_graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


def _parse_sse_data(text: str) -> dict:
    """Extract the first JSON-RPC result from an SSE event stream."""
    for line in text.strip().splitlines():
        if line.startswith("data: "):
            return json.loads(line[len("data: ") :])
    raise ValueError(f"No SSE data line found in: {text!r}")


@pytest.fixture()
def _mcp_test_env():
    """Set up a test GraphQLClient and disable DNS rebinding protection."""
    source = MockSchemaSource("test", sdl=SAMPLE_SDL)
    service = SchemaService(sources=[source], ttl_seconds=0)
    config = GraphQLConfig(allow_mutations=False)
    client = GraphQLClient(schema_service=service, transport=None, config=config)
    set_client(client)

    # Patch _get_client in mcp_stdio module so MCP tools resolve our test client
    import generic_graphql_mcp.adapters.inbound.mcp_stdio as mcp_mod

    original_get_client = mcp_mod._get_client
    mcp_mod._get_client = lambda: client

    # Disable DNS rebinding protection for testserver host
    orig_dns = mcp_instance.settings.transport_security.enable_dns_rebinding_protection
    mcp_instance.settings.transport_security.enable_dns_rebinding_protection = False

    # Reset session manager so each test gets a fresh one via lifespan
    orig_session_manager = mcp_instance._session_manager
    mcp_instance._session_manager = None

    yield

    mcp_mod._get_client = original_get_client
    mcp_instance.settings.transport_security.enable_dns_rebinding_protection = orig_dns
    mcp_instance._session_manager = orig_session_manager


@pytest.fixture()
def mcp_client(_mcp_test_env):
    """Starlette TestClient for the MCP sub-app (with lifespan for session manager)."""
    mcp_app = create_mcp_http_app()
    with TestClient(mcp_app) as tc:
        yield tc


def _initialize(tc: TestClient) -> str:
    """Send MCP initialize and return the session ID."""
    resp = tc.post(
        "/",
        json={
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1.0"},
            },
            "id": 1,
        },
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    assert resp.status_code == 200
    session_id = resp.headers.get("mcp-session-id")
    assert session_id is not None

    # Verify the response contains serverInfo
    data = _parse_sse_data(resp.text)
    assert "result" in data
    assert data["result"]["serverInfo"]["name"] == "generic-graphql-mcp"

    # Send initialized notification
    tc.post(
        "/",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": session_id,
        },
    )
    return session_id


class TestMCPHTTPInitialize:
    def test_mcp_initialize_returns_server_info(self, mcp_client: TestClient) -> None:
        """POST to MCP sub-app with initialize returns 200 with serverInfo."""
        resp = mcp_client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "test", "version": "0.1.0"},
                },
                "id": 1,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
            },
        )
        assert resp.status_code == 200
        data = _parse_sse_data(resp.text)
        assert data["result"]["serverInfo"]["name"] == "generic-graphql-mcp"
        assert "protocolVersion" in data["result"]


class TestMCPHTTPToolsList:
    def test_mcp_tools_list_returns_all_tools(self, mcp_client: TestClient) -> None:
        """After initializing a session, tools/list returns all 8 registered tools."""
        session_id = _initialize(mcp_client)

        resp = mcp_client.post(
            "/",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {},
                "id": 2,
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "mcp-session-id": session_id,
            },
        )
        assert resp.status_code == 200
        data = _parse_sse_data(resp.text)
        tool_names = {t["name"] for t in data["result"]["tools"]}
        expected = {
            "query",
            "raw",
            "introspect",
            "describe_type",
            "list_subgraphs",
            "refresh_schema",
            "entities",
            "subscribe",
        }
        assert tool_names == expected
