from __future__ import annotations


class SchemaResolutionError(Exception):
    """Raised when all schema cascade sources fail."""

    def __init__(self, message: str = "All schema sources failed") -> None:
        super().__init__(message)


class MutationGuardError(Exception):
    """Raised when a mutation is attempted while GRAPHQL_ALLOW_MUTATIONS=false."""

    def __init__(self, message: str = "Mutations are blocked; set GRAPHQL_ALLOW_MUTATIONS=true to allow") -> None:
        super().__init__(message)


class QueryDepthError(Exception):
    """Raised when query exceeds GRAPHQL_MAX_QUERY_DEPTH."""

    def __init__(self, depth: int, max_depth: int) -> None:
        super().__init__(f"Query depth {depth} exceeds maximum allowed depth {max_depth}")
        self.depth = depth
        self.max_depth = max_depth
