from __future__ import annotations

from unittest.mock import patch

from generic_graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


class TestTTLCache:
    """Test TTL caching behavior of SchemaService."""

    def test_cache_hit_within_ttl(self):
        """Within TTL, resolve() returns cached schema without calling sources."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=300)

        result1 = service.resolve()
        result2 = service.resolve()

        assert result1.source_name == "test"
        assert result2.source_name == "test"
        assert source.call_count == 1  # Only called once

    def test_cache_expired_refetches(self):
        """After TTL expires, resolve() re-fetches from sources."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=10)

        # First call -- fetches and caches
        monotonic_values = [100.0, 100.0]  # resolve check + cache set
        with patch("generic_graphql_mcp.domain.schema_service.time.monotonic", side_effect=monotonic_values):
            service.resolve()

        assert source.call_count == 1

        # Second call -- TTL expired (time jumped past TTL)
        monotonic_values_2 = [200.0, 200.0]  # resolve check (200-100=100 > 10 TTL) + cache set
        with patch("generic_graphql_mcp.domain.schema_service.time.monotonic", side_effect=monotonic_values_2):
            service.resolve()

        assert source.call_count == 2

    def test_invalidate_forces_refetch(self):
        """invalidate() clears cache, next resolve() re-fetches."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=300)

        service.resolve()
        assert source.call_count == 1

        service.invalidate()
        service.resolve()
        assert source.call_count == 2  # Called again after invalidation

    def test_invalidate_then_resolve_uses_same_source(self):
        """After invalidate(), resolve() goes through the cascade again."""
        source = MockSchemaSource("test", sdl=SAMPLE_SDL)
        service = SchemaService(sources=[source], ttl_seconds=300)

        result1 = service.resolve()
        service.invalidate()
        result2 = service.resolve()

        assert result1.source_name == "test"
        assert result2.source_name == "test"
        assert source.call_count == 2
