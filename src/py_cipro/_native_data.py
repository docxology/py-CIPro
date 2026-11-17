"""Read numerical Cicy3 associations directly from the released text member."""

from wolframclient.language.expression import WLExpressionMeta, WLSymbol

from ._native_errors import NativeUnsupportedError
from .catalog import _cicy3_source_rows


def _fields(value):
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (tuple, list)):
        return tuple(name for item in value for name in _fields(item))
    raise NativeUnsupportedError("Python Data field selection takes strings.")


def native_data(dataset, condition, keys=(), /):
    """Native read-only Data for the original Cicy3 associations."""
    if not isinstance(dataset, str) or dataset != "Cicy3":
        raise NativeUnsupportedError("Python Data reads the bundled textual Cicy3 dataset.")
    rows = _cicy3_source_rows()
    if isinstance(condition, str) and condition == "Length":
        return len(rows)
    if type(condition) is int:
        if not 1 <= condition <= len(rows):
            raise IndexError(f"Cicy3 indices range from 1 to {len(rows)}.")
        return_one = True
        selected = (rows[condition - 1],)
    else:
        return_one = False
        if (isinstance(condition, str) and condition == "All") or (
            isinstance(condition, WLSymbol) and condition.name in ("All", "System`All")
        ):
            selected = rows
        elif isinstance(condition, (list, tuple)) and len(condition) == 2 and all(type(i) is int for i in condition):
            begin, end = sorted(condition)
            selected = rows[max(begin, 1) - 1 : min(end, len(rows))] if end >= 1 else ()
        elif callable(condition) and not isinstance(condition, WLExpressionMeta):
            selected = tuple(row for row in rows if condition(dict(row)) is True)
        else:
            raise NativeUnsupportedError("Python Data takes 'All', 'Length', an index, an inclusive pair, or a Python predicate.")
    names = _fields(keys)
    if not names:
        results = tuple(dict(row) for row in selected)
        return results[0] if return_one else results
    if any(name not in rows[0] for name in names):
        raise NativeUnsupportedError("Python Data field selection requires fields present in the released records.")
    if len(names) == 1:
        return tuple(row[names[0]] for row in selected)
    return tuple(tuple(row[name] for name in names) for row in selected)
