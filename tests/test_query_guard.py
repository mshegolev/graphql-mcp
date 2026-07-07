from __future__ import annotations

import pytest

from generic_graphql_mcp.adapters.outbound.query_guard import (
    check_mutation_guard,
    contains_mutation,
)
from generic_graphql_mcp.domain.errors import MutationGuardError


class TestContainsMutation:
    def test_detects_anonymous_mutation(self) -> None:
        assert contains_mutation('mutation { createUser(name: "x") { id } }') is True

    def test_detects_named_mutation(self) -> None:
        assert contains_mutation('mutation CreateUser { createUser(name: "x") { id } }') is True

    def test_query_is_not_mutation(self) -> None:
        assert contains_mutation("{ users { id } }") is False

    def test_named_query_is_not_mutation(self) -> None:
        assert contains_mutation("query GetUsers { users { id } }") is False

    def test_subscription_is_not_mutation(self) -> None:
        assert contains_mutation("subscription { onUserCreated { id } }") is False

    def test_field_named_mutation_is_not_mutation(self) -> None:
        # A field called "mutationLog" is NOT a mutation operation
        assert contains_mutation("{ mutationLog { id } }") is False

    def test_unparseable_query_returns_false(self) -> None:
        assert contains_mutation("not a valid query {{{{") is False

    def test_empty_string_returns_false(self) -> None:
        assert contains_mutation("") is False


class TestCheckMutationGuard:
    def test_raises_on_mutation(self) -> None:
        with pytest.raises(MutationGuardError, match="Mutations are blocked"):
            check_mutation_guard("mutation { deleteUser(id: 1) { id } }")

    def test_allows_query(self) -> None:
        check_mutation_guard("{ users { id } }")  # should not raise
