"""Benchmark fixtures: pre-built payloads at 100KB and 1MB sizes."""

from __future__ import annotations

import pytest


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


@pytest.fixture(scope="session")
def payload_100kb() -> dict:
    """~100KB JSON payload."""
    return _make_large_payload(1200)


@pytest.fixture(scope="session")
def payload_1mb() -> dict:
    """~1MB JSON payload."""
    return _make_large_payload(12000)


@pytest.fixture(scope="session")
def encoded_100kb(payload_100kb: dict) -> bytes:
    """Pre-encoded 100KB payload bytes for decode benchmarks."""
    import orjson

    return orjson.dumps(payload_100kb, option=orjson.OPT_SORT_KEYS)


@pytest.fixture(scope="session")
def encoded_1mb(payload_1mb: dict) -> bytes:
    """Pre-encoded 1MB payload bytes for decode benchmarks."""
    import orjson

    return orjson.dumps(payload_1mb, option=orjson.OPT_SORT_KEYS)
