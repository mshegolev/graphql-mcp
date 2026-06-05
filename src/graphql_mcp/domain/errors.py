from __future__ import annotations


class SchemaResolutionError(Exception):
    """Raised when all schema cascade sources fail."""

    def __init__(self, message: str = "All schema sources failed") -> None:
        super().__init__(message)


class MutationGuardError(Exception):
    """Raised when a mutation is attempted while GRAPHQL_ALLOW_MUTATIONS=false."""

    def __init__(self, message: str = "Mutations are blocked; set GRAPHQL_ALLOW_MUTATIONS=true to allow") -> None:
        super().__init__(message)
