from __future__ import annotations


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁSchemaResolutionErrorǁ__init____mutmut: MutantDict = {}  # type: ignore


class SchemaResolutionError(Exception):
    """Raised when all schema cascade sources fail."""

    @_mutmut_mutated(mutants_xǁSchemaResolutionErrorǁ__init____mutmut)
    def __init__(self, message: str = "All schema sources failed") -> None:
        super().__init__(message)

    def xǁSchemaResolutionErrorǁ__init____mutmut_orig(self, message: str = "All schema sources failed") -> None:
        super().__init__(message)

    def xǁSchemaResolutionErrorǁ__init____mutmut_1(self, message: str = "XXAll schema sources failedXX") -> None:
        super().__init__(message)

    def xǁSchemaResolutionErrorǁ__init____mutmut_2(self, message: str = "all schema sources failed") -> None:
        super().__init__(message)

    def xǁSchemaResolutionErrorǁ__init____mutmut_3(self, message: str = "ALL SCHEMA SOURCES FAILED") -> None:
        super().__init__(message)

    def xǁSchemaResolutionErrorǁ__init____mutmut_4(self, message: str = "All schema sources failed") -> None:
        super().__init__(None)

mutants_xǁSchemaResolutionErrorǁ__init____mutmut['_mutmut_orig'] = SchemaResolutionError.xǁSchemaResolutionErrorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁSchemaResolutionErrorǁ__init____mutmut['xǁSchemaResolutionErrorǁ__init____mutmut_1'] = SchemaResolutionError.xǁSchemaResolutionErrorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁSchemaResolutionErrorǁ__init____mutmut['xǁSchemaResolutionErrorǁ__init____mutmut_2'] = SchemaResolutionError.xǁSchemaResolutionErrorǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁSchemaResolutionErrorǁ__init____mutmut['xǁSchemaResolutionErrorǁ__init____mutmut_3'] = SchemaResolutionError.xǁSchemaResolutionErrorǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁSchemaResolutionErrorǁ__init____mutmut['xǁSchemaResolutionErrorǁ__init____mutmut_4'] = SchemaResolutionError.xǁSchemaResolutionErrorǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁMutationGuardErrorǁ__init____mutmut: MutantDict = {}  # type: ignore


class MutationGuardError(Exception):
    """Raised when a mutation is attempted while GRAPHQL_ALLOW_MUTATIONS=false."""

    @_mutmut_mutated(mutants_xǁMutationGuardErrorǁ__init____mutmut)
    def __init__(self, message: str = "Mutations are blocked; set GRAPHQL_ALLOW_MUTATIONS=true to allow") -> None:
        super().__init__(message)

    def xǁMutationGuardErrorǁ__init____mutmut_orig(self, message: str = "Mutations are blocked; set GRAPHQL_ALLOW_MUTATIONS=true to allow") -> None:
        super().__init__(message)

    def xǁMutationGuardErrorǁ__init____mutmut_1(self, message: str = "XXMutations are blocked; set GRAPHQL_ALLOW_MUTATIONS=true to allowXX") -> None:
        super().__init__(message)

    def xǁMutationGuardErrorǁ__init____mutmut_2(self, message: str = "mutations are blocked; set graphql_allow_mutations=true to allow") -> None:
        super().__init__(message)

    def xǁMutationGuardErrorǁ__init____mutmut_3(self, message: str = "MUTATIONS ARE BLOCKED; SET GRAPHQL_ALLOW_MUTATIONS=TRUE TO ALLOW") -> None:
        super().__init__(message)

    def xǁMutationGuardErrorǁ__init____mutmut_4(self, message: str = "Mutations are blocked; set GRAPHQL_ALLOW_MUTATIONS=true to allow") -> None:
        super().__init__(None)

mutants_xǁMutationGuardErrorǁ__init____mutmut['_mutmut_orig'] = MutationGuardError.xǁMutationGuardErrorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁMutationGuardErrorǁ__init____mutmut['xǁMutationGuardErrorǁ__init____mutmut_1'] = MutationGuardError.xǁMutationGuardErrorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁMutationGuardErrorǁ__init____mutmut['xǁMutationGuardErrorǁ__init____mutmut_2'] = MutationGuardError.xǁMutationGuardErrorǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁMutationGuardErrorǁ__init____mutmut['xǁMutationGuardErrorǁ__init____mutmut_3'] = MutationGuardError.xǁMutationGuardErrorǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁMutationGuardErrorǁ__init____mutmut['xǁMutationGuardErrorǁ__init____mutmut_4'] = MutationGuardError.xǁMutationGuardErrorǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁQueryDepthErrorǁ__init____mutmut: MutantDict = {}  # type: ignore


class QueryDepthError(Exception):
    """Raised when query exceeds GRAPHQL_MAX_QUERY_DEPTH."""

    @_mutmut_mutated(mutants_xǁQueryDepthErrorǁ__init____mutmut)
    def __init__(self, depth: int, max_depth: int) -> None:
        super().__init__(f"Query depth {depth} exceeds maximum allowed depth {max_depth}")
        self.depth = depth
        self.max_depth = max_depth

    def xǁQueryDepthErrorǁ__init____mutmut_orig(self, depth: int, max_depth: int) -> None:
        super().__init__(f"Query depth {depth} exceeds maximum allowed depth {max_depth}")
        self.depth = depth
        self.max_depth = max_depth

    def xǁQueryDepthErrorǁ__init____mutmut_1(self, depth: int, max_depth: int) -> None:
        super().__init__(None)
        self.depth = depth
        self.max_depth = max_depth

    def xǁQueryDepthErrorǁ__init____mutmut_2(self, depth: int, max_depth: int) -> None:
        super().__init__(f"Query depth {depth} exceeds maximum allowed depth {max_depth}")
        self.depth = None
        self.max_depth = max_depth

    def xǁQueryDepthErrorǁ__init____mutmut_3(self, depth: int, max_depth: int) -> None:
        super().__init__(f"Query depth {depth} exceeds maximum allowed depth {max_depth}")
        self.depth = depth
        self.max_depth = None

mutants_xǁQueryDepthErrorǁ__init____mutmut['_mutmut_orig'] = QueryDepthError.xǁQueryDepthErrorǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁQueryDepthErrorǁ__init____mutmut['xǁQueryDepthErrorǁ__init____mutmut_1'] = QueryDepthError.xǁQueryDepthErrorǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁQueryDepthErrorǁ__init____mutmut['xǁQueryDepthErrorǁ__init____mutmut_2'] = QueryDepthError.xǁQueryDepthErrorǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁQueryDepthErrorǁ__init____mutmut['xǁQueryDepthErrorǁ__init____mutmut_3'] = QueryDepthError.xǁQueryDepthErrorǁ__init____mutmut_3 # type: ignore # mutmut generated
