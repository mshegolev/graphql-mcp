from __future__ import annotations

import logging

from graphql import parse as gql_parse
from graphql.language.ast import OperationType

from graphql_mcp.domain.errors import MutationGuardError

logger = logging.getLogger(__name__)


def contains_mutation(query_str: str) -> bool:
    """Return True if *query_str* contains a mutation operation.

    Uses graphql-core AST parsing to detect ``OperationType.MUTATION``.
    Subscriptions and queries are **not** blocked.
    If the string cannot be parsed (invalid GraphQL), returns ``False``
    — let the server-side validator decide.
    """
    if not query_str or not query_str.strip():
        return False
    try:
        doc = gql_parse(query_str)
    except Exception:  # noqa: BLE001 – any parse error is fine
        return False

    return any(hasattr(defn, "operation") and defn.operation == OperationType.MUTATION for defn in doc.definitions)


def check_mutation_guard(query_str: str) -> None:
    """Raise :class:`MutationGuardError` if *query_str* is a mutation.

    No-op if the query is not a mutation.
    """
    if contains_mutation(query_str):
        raise MutationGuardError()
