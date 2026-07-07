from __future__ import annotations

import pytest

from generic_graphql_mcp.domain.errors import SchemaResolutionError
from generic_graphql_mcp.domain.schema_service import SchemaService
from tests.conftest import SAMPLE_SDL, MockSchemaSource


class TestSchemaCascade:
    """Test the cascade fallback behavior of SchemaService."""

    def test_first_source_wins(self):
        """When the first source succeeds, later sources are not tried."""
        first = MockSchemaSource("first", sdl=SAMPLE_SDL)
        second = MockSchemaSource("second", sdl=SAMPLE_SDL)

        service = SchemaService(sources=[first, second], ttl_seconds=0)
        result = service.resolve()

        assert result.source_name == "first"
        assert first.call_count == 1
        assert second.call_count == 0

    def test_fallback_on_none(self):
        """When a source returns None, cascade tries the next source."""
        first = MockSchemaSource("gitlab", sdl=None)
        second = MockSchemaSource("introspection", sdl=SAMPLE_SDL)

        service = SchemaService(sources=[first, second], ttl_seconds=0)
        result = service.resolve()

        assert result.source_name == "introspection"
        assert first.call_count == 1
        assert second.call_count == 1

    def test_fallback_on_exception(self):
        """When a source raises an exception, cascade tries the next source."""
        first = MockSchemaSource("gitlab", should_raise=True)
        second = MockSchemaSource("introspection", sdl=SAMPLE_SDL)

        service = SchemaService(sources=[first, second], ttl_seconds=0)
        result = service.resolve()

        assert result.source_name == "introspection"
        assert first.call_count == 1
        assert second.call_count == 1

    def test_full_cascade_fallback(self):
        """Cascade falls through None->exception->None->success."""
        gitlab = MockSchemaSource("gitlab", sdl=None)
        introspection = MockSchemaSource("introspection", should_raise=True)
        federation = MockSchemaSource("federation", sdl=None)
        file_src = MockSchemaSource("sdl_file", sdl=SAMPLE_SDL)

        service = SchemaService(
            sources=[gitlab, introspection, federation, file_src],
            ttl_seconds=0,
        )
        result = service.resolve()

        assert result.source_name == "sdl_file"
        assert gitlab.call_count == 1
        assert introspection.call_count == 1
        assert federation.call_count == 1
        assert file_src.call_count == 1

    def test_all_sources_fail_raises_error(self):
        """When all sources fail, SchemaResolutionError is raised."""
        failing = MockSchemaSource("failing", should_raise=True)
        none_src = MockSchemaSource("none", sdl=None)

        service = SchemaService(sources=[failing, none_src], ttl_seconds=0)

        with pytest.raises(SchemaResolutionError, match="All schema sources failed"):
            service.resolve()

    def test_empty_sources_raises_error(self):
        """When no sources are configured, SchemaResolutionError is raised."""
        service = SchemaService(sources=[], ttl_seconds=0)

        with pytest.raises(SchemaResolutionError, match="All schema sources failed"):
            service.resolve()
