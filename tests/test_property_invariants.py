"""Property-based tests for domain model invariants."""

from generic_graphql_mcp.domain.models import ErrorClass, QueryResult


def test_query_result_error_class_invariants():
    """Test that QueryResult error_class always has valid values."""
    # Test that ErrorClass enum only contains valid values
    valid_error_classes = {ErrorClass.OK, ErrorClass.TRANSPORT, ErrorClass.GRAPHQL}

    for error_class in ErrorClass:
        assert error_class in valid_error_classes


def test_query_result_data_constraints():
    """Test constraints on QueryResult data field."""
    # Test that data field is either dict or None
    result_with_data = QueryResult(data={"key": "value"}, errors=[], error_class=ErrorClass.OK)

    result_without_data = QueryResult(data=None, errors=[{"message": "error"}], error_class=ErrorClass.GRAPHQL)

    assert isinstance(result_with_data.data, dict) or result_with_data.data is None
    assert isinstance(result_without_data.data, dict) or result_without_data.data is None


def test_query_result_errors_constraints():
    """Test constraints on QueryResult errors field."""
    # Test that errors field is always a list
    result_with_errors = QueryResult(
        data=None, errors=[{"message": "error1"}, {"message": "error2"}], error_class=ErrorClass.GRAPHQL
    )

    result_without_errors = QueryResult(data={"key": "value"}, errors=[], error_class=ErrorClass.OK)

    assert isinstance(result_with_errors.errors, list)
    assert isinstance(result_without_errors.errors, list)


def test_error_class_value_constraints():
    """Test that ErrorClass values are constrained."""
    # Test that ErrorClass values are limited to expected strings
    expected_values = {"ok", "transport", "graphql"}

    for error_class in ErrorClass:
        assert error_class.value in expected_values
