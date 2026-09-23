class ToolingError(Exception):
    """Fatal tooling error: reported to the user without a traceback."""


class StoreReadError(ToolingError):
    """A file matching a store filename carries no usable version."""
