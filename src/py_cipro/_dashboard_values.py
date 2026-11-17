"""Structured expression input and exact JSON display values for the dashboard."""

from collections.abc import Mapping
from decimal import Decimal
from fractions import Fraction
import math
import re

import sympy as sp
from wolframclient.language import wl
from wolframclient.language.expression import WLExpressionMeta


_SYMBOL = re.compile(r"[A-Za-z][A-Za-z0-9]{0,63}\Z")
_CONSTANTS = {"I": sp.I, "Pi": sp.pi, "E": sp.E, "All": "All", "Automatic": "Automatic", "None": None}
_MAX_JSON_INTEGER = 2**53 - 1
_INTEGER_TEXT = re.compile(r"-?(?:0|[1-9][0-9]{0,255})\Z")


def _symbol(value, backend):
    if not isinstance(value, str) or _SYMBOL.fullmatch(value) is None:
        raise ValueError("Symbol names must contain up to 64 letters or digits and start with a letter.")
    return getattr(wl, f"Global`{value}") if backend == "wolfram" else sp.Symbol(value)


def _parts(value, size=None):
    if not isinstance(value, list) or not value or (size is not None and len(value) != size):
        raise ValueError("This symbolic tag needs an array of the documented arguments.")
    return value


def decode(value, backend="python", *, _depth=0):
    """Build typed objects from JSON and the dashboard's fixed symbolic tags."""
    if _depth > 24:
        raise ValueError("Dashboard inputs may contain at most 24 nested levels.")

    def decode_child(child):
        return decode(child, backend, _depth=_depth + 1)

    if isinstance(value, list):
        return [decode_child(child) for child in value]
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Dashboard numbers must be finite.")
    if not isinstance(value, dict):
        return value
    tags = [key for key in value if key.startswith("$")]
    if not tags:
        return {key: decode_child(child) for key, child in value.items()}
    if len(value) != 1:
        raise ValueError("A symbolic tag must be the only key in its object.")
    tag = tags[0]
    data = value[tag]
    wolfram = backend == "wolfram"
    if tag == "$symbol":
        return _symbol(data, backend)
    if tag == "$constant":
        if not isinstance(data, str) or data not in _CONSTANTS:
            raise ValueError("Unknown dashboard constant.")
        return getattr(wl, f"System`{data}") if wolfram else _CONSTANTS[data]
    if tag == "$indexed":
        name, *indices = _parts(data)
        _symbol(name, backend)
        if not 1 <= len(indices) <= 4 or any(type(index) is not int for index in indices):
            raise ValueError("An indexed symbol requires one to four integer indices.")
        return wl.Subscript(_symbol(name, backend), *indices) if wolfram else sp.IndexedBase(name)[tuple(indices)]
    if tag == "$integer":
        if not isinstance(data, str) or _INTEGER_TEXT.fullmatch(data) is None:
            raise ValueError("An exact integer tag requires a decimal string of up to 256 digits.")
        return int(data)
    if tag == "$rational":
        numerator, denominator = map(decode_child, _parts(data, 2))
        if type(numerator) is not int or type(denominator) is not int or denominator == 0:
            raise ValueError("A rational requires integer numerator and nonzero integer denominator.")
        return wl.Rational(numerator, denominator) if wolfram else sp.Rational(numerator, denominator)
    if tag == "$pow":
        base, exponent = _parts(data, 2)
        if type(exponent) is not int or not -64 <= exponent <= 64:
            raise ValueError("A power requires an integer exponent from −64 to 64.")
        return wl.Power(decode_child(base), exponent) if wolfram else sp.Pow(decode_child(base), exponent)
    if tag in ("$add", "$mul"):
        parts = _parts(data)
        if len(parts) > 64:
            raise ValueError("A sum or product accepts at most 64 operands.")
        operands = (decode_child(part) for part in parts)
        if wolfram:
            return (wl.Plus if tag == "$add" else wl.Times)(*operands)
        return (sp.Add if tag == "$add" else sp.Mul)(*operands)
    raise ValueError(f"Unsupported symbolic input tag {tag!r}.")


def _integer(value):
    value = int(value)
    return value if abs(value) <= _MAX_JSON_INTEGER else {"$integer": str(value)}


def encode(value):
    """Keep exact scalars, polynomial representations and nested collection shapes."""
    count = 0

    def convert(item, depth=0):
        nonlocal count
        count += 1
        if count > 20_000 or depth > 32:
            raise ValueError("The result is too large for the dashboard. Try a smaller selection.")
        if item is None or isinstance(item, (str, bool)):
            return item
        if isinstance(item, (int, sp.Integer)):
            return _integer(item)
        if isinstance(item, Fraction):
            return {"$rational": [_integer(item.numerator), _integer(item.denominator)]}
        if isinstance(item, sp.Rational):
            return {"$rational": [_integer(item.p), _integer(item.q)]}
        if isinstance(item, float) and math.isfinite(item):
            return item
        if isinstance(item, Decimal):
            return {"$expression": str(item), "language": "decimal"}
        if isinstance(item, complex):
            return {"$complex": [convert(item.real, depth + 1), convert(item.imag, depth + 1)]}
        if isinstance(item, (sp.MatrixBase, sp.NDimArray)) or type(item).__module__.startswith("numpy"):
            return convert(item.tolist(), depth + 1)
        if isinstance(item, sp.Basic):
            return {"$expression": sp.sstr(item), "language": "sympy"}
        if isinstance(item, WLExpressionMeta):
            return {"$expression": str(item), "language": "wolfram"}
        if isinstance(item, (tuple, list)):
            return [convert(child, depth + 1) for child in item]
        if isinstance(item, Mapping):
            if all(isinstance(key, str) for key in item):
                return {key: convert(child, depth + 1) for key, child in item.items()}
            return {"$association": [[convert(key, depth + 1), convert(child, depth + 1)] for key, child in item.items()]}
        raise ValueError(f"The dashboard cannot display the CIPro result type {type(item).__name__}.")

    return convert(value)
