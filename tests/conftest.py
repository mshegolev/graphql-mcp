from __future__ import annotations

import pytest

from graphql_mcp.domain.models import SchemaGraph

SAMPLE_SDL = """\
type Query {
  hello: String
  users: [User]
}

type User {
  id: ID!
  name: String!
  email: String
}
"""


class MockSchemaSource:
    """A configurable mock schema source for testing."""

    def __init__(
        self,
        source_name: str,
        sdl: str | None = None,
        should_raise: bool = False,
    ) -> None:
        self._name = source_name
        self._sdl = sdl
        self._should_raise = should_raise
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def fetch_schema(self) -> SchemaGraph | None:
        self.call_count += 1
        if self._should_raise:
            raise ConnectionError(f"Mock error from {self._name}")
        if self._sdl is None:
            return None
        return SchemaGraph(sdl=self._sdl, source_name=self._name)


@pytest.fixture
def sample_sdl() -> str:
    return SAMPLE_SDL


@pytest.fixture
def successful_source(sample_sdl: str) -> MockSchemaSource:
    return MockSchemaSource("test_source", sdl=sample_sdl)


@pytest.fixture
def failing_source() -> MockSchemaSource:
    return MockSchemaSource("failing_source", should_raise=True)


@pytest.fixture
def none_source() -> MockSchemaSource:
    return MockSchemaSource("none_source", sdl=None)
