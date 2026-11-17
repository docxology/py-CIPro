"""Public capability limits of the Python backend."""


class NativeUnsupportedError(NotImplementedError):
    """The Wolfram operation or argument domain has no native implementation."""
