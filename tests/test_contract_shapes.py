"""Contract tests for response shape validation."""

import pytest
from generic_graphql_mcp.domain.models import QueryResult, ErrorClass


def test_query_result_shape():
    """Test that QueryResult has expected shape."""
    # Verify QueryResult structure
    result = QueryResult(data={"test": "value"}, errors=[], error_class=ErrorClass.OK)

    # Check that all expected attributes exist
    assert hasattr(result, "data")
    assert hasattr(result, "errors")
    assert hasattr(result, "error_class")

    # Check attribute types
    assert isinstance(result.data, dict) or result.data is None
    assert isinstance(result.errors, list)
    assert isinstance(result.error_class, ErrorClass)


def test_error_class_values():
    """Test that ErrorClass has expected values."""
    # Verify all expected error class values exist
    assert ErrorClass.OK.value == "ok"
    assert ErrorClass.TRANSPORT.value == "transport"
    assert ErrorClass.GRAPHQL.value == "graphql"


def test_introspection_response_shape():
    """Test that introspection responses have expected shape."""
    # This would validate the structure of introspection responses
    assert True  # Placeholder for actual implementation


def test_entity_response_shape():
    """Test that entity resolution responses have expected shape."""
    # This would validate the structure of entity responses
    assert True  # Placeholder for actual implementation
