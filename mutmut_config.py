# Mutmut configuration file


def pre_mutation(context):
    """Hook called before each mutation."""
    # Skip mutations in test files
    if context.filename.startswith("tests/"):
        context.skip = True

    # Skip mutations in __init__.py files
    if context.filename.endswith("__init__.py"):
        context.skip = True


def pre_run(context):
    """Hook called before running tests."""
    # Can be used to set up test environment
    pass


def post_run(context):
    """Hook called after running tests."""
    # Can be used to clean up test environment
    pass
