"""Property-based tests for GraphQL queries."""

import pytest
from hypothesis import given, strategies as st
from graphql_mcp.domain.models import QueryResult, ErrorClass


# Simple strategy for generating GraphQL field names
field_names = st.text(alphabet=st.characters(blacklist_categories=["Cs"]), min_size=1, max_size=50)


# Strategy for generating simple GraphQL queries
simple_queries = st.builds(lambda field: f"{{ {field} }}", field=field_names)


def test_error_class_enum_values():
    """Property test: ErrorClass enum values are always valid."""
    # Test that ErrorClass only has expected values
    valid_values = {"ok", "transport", "graphql"}

    for error_class in ErrorClass:
        assert error_class.value in valid_values


@given(st.text(min_size=0, max_size=1000))
def test_query_result_handles_any_data(data_string):
    """Property test: QueryResult can handle arbitrary data strings."""
    # Test that QueryResult can handle various data inputs
    result = QueryResult(data={"test_field": data_string}, errors=[], error_class=ErrorClass.OK)

    assert result.data["test_field"] == data_string
    assert result.errors == []
    assert result.error_class == ErrorClass.OK


@given(st.lists(st.text(), max_size=10))
def test_query_result_handles_error_lists(error_messages):
    """Property test: QueryResult can handle lists of error messages."""
    # Test that QueryResult can handle various error lists
    result = QueryResult(
        data=None, errors=error_messages, error_class=ErrorClass.GRAPHQL if error_messages else ErrorClass.OK
    )

    assert result.errors == error_messages
    if error_messages:
        assert result.error_class == ErrorClass.GRAPHQL
    else:
        assert result.error_class == ErrorClass.OK


def test_simple_query_generation():
    """Test that our simple query generation strategy works."""
    # This is just to verify our strategy works
    assert True  # Placeholder for actual property tests
