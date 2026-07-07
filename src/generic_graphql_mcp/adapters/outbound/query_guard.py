from __future__ import annotations

import logging

from graphql import parse as gql_parse
from graphql.language.ast import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    SelectionSetNode,
)

from generic_graphql_mcp.domain.errors import MutationGuardError, QueryDepthError

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


def _measure_depth(
    selection_set: SelectionSetNode | None,
    fragments: dict[str, FragmentDefinitionNode],
    visited: set[str],
) -> int:
    """Recursively measure the maximum nesting depth of a selection set."""
    if selection_set is None:
        return 0
    max_depth = 0
    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            depth = 1 + _measure_depth(selection.selection_set, fragments, visited)
        elif isinstance(selection, InlineFragmentNode):
            # Inline fragment is a type condition, not an extra field level
            depth = _measure_depth(selection.selection_set, fragments, visited)
        elif isinstance(selection, FragmentSpreadNode):
            name = selection.name.value
            if name in visited:
                # Cycle protection
                depth = 0
            else:
                visited.add(name)
                frag = fragments.get(name)
                depth = _measure_depth(frag.selection_set, fragments, visited) if frag else 0
                visited.discard(name)
        else:
            depth = 0
        max_depth = max(max_depth, depth)
    return max_depth


def check_query_depth(query_str: str, max_depth: int) -> None:
    """Raise :class:`QueryDepthError` if *query_str* exceeds *max_depth*.

    Uses graphql-core AST parsing to measure nesting depth.
    Parse errors are silently ignored — let the upstream server validate.
    """
    if not query_str or not query_str.strip():
        return
    try:
        doc = gql_parse(query_str)
    except Exception:  # noqa: BLE001 – parse errors are fine
        return

    fragments: dict[str, FragmentDefinitionNode] = {
        defn.name.value: defn for defn in doc.definitions if isinstance(defn, FragmentDefinitionNode)
    }

    for defn in doc.definitions:
        if isinstance(defn, OperationDefinitionNode):
            depth = _measure_depth(defn.selection_set, fragments, set())
            if depth > max_depth:
                raise QueryDepthError(depth, max_depth)
