"""Simple functions for demonstrating mutation testing."""


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_add__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_add__mutmut)
def add(a, b):
    """Add two numbers."""
    return a + b


def x_add__mutmut_orig(a, b):
    """Add two numbers."""
    return a + b


def x_add__mutmut_1(a, b):
    """Add two numbers."""
    return a - b

mutants_x_add__mutmut['_mutmut_orig'] = x_add__mutmut_orig # type: ignore # mutmut generated
mutants_x_add__mutmut['x_add__mutmut_1'] = x_add__mutmut_1 # type: ignore # mutmut generated
mutants_x_is_positive__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_is_positive__mutmut)
def is_positive(x):
    """Check if a number is positive."""
    return x > 0


def x_is_positive__mutmut_orig(x):
    """Check if a number is positive."""
    return x > 0


def x_is_positive__mutmut_1(x):
    """Check if a number is positive."""
    return x >= 0


def x_is_positive__mutmut_2(x):
    """Check if a number is positive."""
    return x > 1

mutants_x_is_positive__mutmut['_mutmut_orig'] = x_is_positive__mutmut_orig # type: ignore # mutmut generated
mutants_x_is_positive__mutmut['x_is_positive__mutmut_1'] = x_is_positive__mutmut_1 # type: ignore # mutmut generated
mutants_x_is_positive__mutmut['x_is_positive__mutmut_2'] = x_is_positive__mutmut_2 # type: ignore # mutmut generated
mutants_x_get_max__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_max__mutmut)
def get_max(a, b):
    """Get the maximum of two numbers."""
    if a > b:
        return a
    else:
        return b


def x_get_max__mutmut_orig(a, b):
    """Get the maximum of two numbers."""
    if a > b:
        return a
    else:
        return b


def x_get_max__mutmut_1(a, b):
    """Get the maximum of two numbers."""
    if a >= b:
        return a
    else:
        return b

mutants_x_get_max__mutmut['_mutmut_orig'] = x_get_max__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_max__mutmut['x_get_max__mutmut_1'] = x_get_max__mutmut_1 # type: ignore # mutmut generated
