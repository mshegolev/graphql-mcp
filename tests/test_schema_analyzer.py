from __future__ import annotations

from generic_graphql_mcp.adapters.outbound.schema_analyzer import SchemaAnalyzer
from tests.conftest import SAMPLE_SDL, SAMPLE_SUPERGRAPH_SDL

analyzer = SchemaAnalyzer()


class TestBuildSummary:
    def test_extracts_query_fields(self) -> None:
        summary = analyzer.build_summary(SAMPLE_SDL)
        assert "hello" in summary.query_fields
        assert "users" in summary.query_fields

    def test_extracts_types_excluding_builtins(self) -> None:
        summary = analyzer.build_summary(SAMPLE_SDL)
        type_names = [t.name for t in summary.types]
        assert "User" in type_names
        assert "Query" in type_names
        assert "__Schema" not in type_names

    def test_type_kinds_are_set(self) -> None:
        summary = analyzer.build_summary(SAMPLE_SDL)
        user_type = next(t for t in summary.types if t.name == "User")
        assert user_type.kind == "OBJECT"


class TestDescribeType:
    def test_returns_type_info_with_fields(self) -> None:
        info = analyzer.describe_type(SAMPLE_SDL, "User")
        assert info is not None
        assert info.name == "User"
        assert info.kind == "OBJECT"
        field_names = [f.name for f in info.fields]
        assert "id" in field_names
        assert "name" in field_names

    def test_returns_none_for_unknown_type(self) -> None:
        assert analyzer.describe_type(SAMPLE_SDL, "NonExistent") is None

    def test_subgraph_is_none_without_supergraph(self) -> None:
        info = analyzer.describe_type(SAMPLE_SDL, "User")
        assert info is not None
        assert info.subgraph is None

    def test_subgraph_populated_from_supergraph(self) -> None:
        info = analyzer.describe_type(SAMPLE_SUPERGRAPH_SDL, "User")
        assert info is not None
        assert info.subgraph == "users"

    def test_field_args_extracted(self) -> None:
        sdl = """\
type Query {
  users(limit: Int, offset: Int): [User]
}
type User {
  id: ID!
  name: String!
}
"""
        info = analyzer.describe_type(sdl, "Query")
        assert info is not None
        users_field = next(f for f in info.fields if f.name == "users")
        assert len(users_field.args) == 2
        assert any("limit" in a for a in users_field.args)


class TestListSubgraphs:
    def test_extracts_subgraphs_from_supergraph_sdl(self) -> None:
        subgraphs = analyzer.list_subgraphs(SAMPLE_SUPERGRAPH_SDL)
        assert len(subgraphs) >= 2
        names = [s.name for s in subgraphs]
        assert "users" in names
        assert "products" in names

    def test_subgraph_has_url(self) -> None:
        subgraphs = analyzer.list_subgraphs(SAMPLE_SUPERGRAPH_SDL)
        users = next(s for s in subgraphs if s.name == "users")
        assert users.url == "http://users:4001/graphql"

    def test_subgraph_has_owned_types(self) -> None:
        subgraphs = analyzer.list_subgraphs(SAMPLE_SUPERGRAPH_SDL)
        users = next(s for s in subgraphs if s.name == "users")
        assert "User" in users.owned_types

    def test_returns_empty_list_for_non_supergraph(self) -> None:
        subgraphs = analyzer.list_subgraphs(SAMPLE_SDL)
        assert subgraphs == []

    def test_returns_empty_for_enum_without_directives(self) -> None:
        # A schema that has join__Graph enum but no @join__graph directives
        fake_sdl = "type Query { x: String }\nenum join__Graph { FOO BAR }"
        subgraphs = analyzer.list_subgraphs(fake_sdl)
        assert subgraphs == []


class TestSchemaAnalyzerCache:
    def test_same_sdl_reuses_cache(self) -> None:
        analyzer2 = SchemaAnalyzer()
        analyzer2.build_summary(SAMPLE_SDL)
        analyzer2.build_summary(SAMPLE_SDL)
        s1 = analyzer2.build_summary(SAMPLE_SDL)
        s2 = analyzer2.build_summary(SAMPLE_SDL)
        assert s1.query_fields == s2.query_fields

    def test_different_sdl_rebuilds(self) -> None:
        analyzer3 = SchemaAnalyzer()
        s1 = analyzer3.build_summary(SAMPLE_SDL)
        sdl2 = "type Query { other: String }"
        s2 = analyzer3.build_summary(sdl2)
        assert s1.query_fields != s2.query_fields
        assert "other" in s2.query_fields
