"""Integration test fixtures.

These tests run against a real mock GraphQL server (either via docker compose
or a local subprocess). The GRAPHQL_ENDPOINT env var must point to the server.

For local development without Docker:
    # Terminal 1: Start mock server
    python tests/integration/mock_server.py

    # Terminal 2: Run tests
    GRAPHQL_ENDPOINT=http://localhost:4000/graphql pytest tests/integration/ -v
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time

import pytest


def _wait_for_server(url: str, timeout: float = 10.0) -> bool:
    """Poll server health endpoint until it responds or timeout."""
    import urllib.request

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception:
            time.sleep(0.3)
    return False


@pytest.fixture(scope="session")
def graphql_endpoint():
    """Return the GraphQL endpoint URL.

    If GRAPHQL_ENDPOINT is set, use it (docker compose mode).
    Otherwise, start the mock server as a subprocess (local dev mode).
    """
    endpoint = os.environ.get("GRAPHQL_ENDPOINT")
    if endpoint:
        # Docker compose or manual mode — endpoint already set
        yield endpoint
        return

    # Local mode: start mock server subprocess
    port = 4321  # Use a non-standard port to avoid conflicts
    server_proc = subprocess.Popen(
        [sys.executable, "tests/integration/mock_server.py"],
        env={**os.environ, "MOCK_SERVER_HOST": "127.0.0.1", "MOCK_SERVER_PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    endpoint = f"http://127.0.0.1:{port}/graphql"
    health_url = f"http://127.0.0.1:{port}/health"

    if not _wait_for_server(health_url):
        server_proc.kill()
        stdout, stderr = server_proc.communicate(timeout=5)
        raise RuntimeError(f"Mock server failed to start.\nstdout: {stdout.decode()}\nstderr: {stderr.decode()}")

    yield endpoint

    # Cleanup
    server_proc.send_signal(signal.SIGTERM)
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_proc.kill()
        server_proc.wait()
