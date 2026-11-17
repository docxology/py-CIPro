"""Python bindings for the upstream CIPro Wolfram Language package."""

from wolframclient.language import wl, wlexpr

from ._catalog import FUNCTIONS, MODIFICATIONS, PROPERTIES
from ._client import CIPro, CIProError, Evaluation, EvaluationError, KernelUnavailable
from ._release import RELEASE_SHA256, RELEASE_TAG

__all__ = [
    "CIPro",
    "CIProError",
    "Evaluation",
    "EvaluationError",
    "FUNCTIONS",
    "KernelUnavailable",
    "MODIFICATIONS",
    "PROPERTIES",
    "RELEASE_SHA256",
    "RELEASE_TAG",
    "wl",
    "wlexpr",
]
