"""Dispatch the Python equivalents of the released CIPro v1.0 definitions."""

from collections.abc import Mapping, Sequence
from inspect import signature
import warnings

from . import _native_bundles, _native_geometry, _native_singularities, _native_symmetry
from ._catalog import MODIFICATION_DEPENDENCIES, PROPERTY_DEPENDENCIES
from ._native_bundles import NATIVE_MOD_DEPENDENCY_OVERRIDES
from ._native_data import native_data
from ._native_errors import NativeUnsupportedError


def _keys(value):
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (tuple, list)):
        return tuple(key for entry in value for key in _keys(entry))
    raise NativeUnsupportedError("Python dispatch takes a key or a nested list of string keys.")


def _association(value):
    if not isinstance(value, Mapping):
        raise NativeUnsupportedError("Python dispatch requires a Python mapping for a CI association.")
    return dict(value)


def _required(key, dependencies, kind):
    try:
        return dependencies[key]
    except KeyError:
        raise ValueError(f"Unknown CIPro {kind} {key!r}.") from None


def _compute_property(key, association, added, options):
    dependencies = _required(key, PROPERTY_DEPENDENCIES, "property")
    if key in association:
        return
    function = NATIVE_PROPERTIES.get(key)
    if function is None:
        raise NativeUnsupportedError(f"CIProp property {key!r} requires Wolfram.")
    for dependency in dependencies:
        _compute_property(dependency, association, added, options)
    value = function(association, **options)
    fields = value if isinstance(value, Mapping) else {key: value}
    association.update(fields)
    added.update(fields)


def native_property(geometry, keys, /, **options):
    association = _association(geometry)
    requested = _keys(keys)
    if not requested:
        raise NativeUnsupportedError("CIProp help and key display require Wolfram. See the concordance for keys.")
    output = options.get("Format", "Full")
    if not isinstance(output, str) or output not in ("Full", "Medium", "Short"):
        raise NativeUnsupportedError("Python CIProp supports Format='Full', 'Medium', or 'Short'.")
    added = {}
    for key in requested:
        _compute_property(key, association, added, options)
    if output == "Full":
        return association
    if output == "Medium":
        return added
    if not added:
        raise NativeUnsupportedError("Format='Short' needs a newly computed field. Use Format='Full' for cached fields.")
    return next(reversed(added.values()))


def native_modify(geometry, key, /, **options):
    if not isinstance(key, str):
        raise NativeUnsupportedError("Python CIMod takes one string operation key.")
    dependencies = _required(key, MODIFICATION_DEPENDENCIES, "modification")
    dependencies = NATIVE_MOD_DEPENDENCY_OVERRIDES.get(key, dependencies)
    function = NATIVE_MODIFICATIONS.get(key)
    if function is None:
        raise NativeUnsupportedError(f"CIMod operation {key!r} requires Wolfram.")
    if isinstance(geometry, Mapping):
        geometries = (geometry,)
    elif isinstance(geometry, Sequence) and not isinstance(geometry, (str, bytes)):
        geometries = geometry
    else:
        raise NativeUnsupportedError("Python CIMod takes a mapping or sequence of mappings.")
    if options.get("Format", "Full") != "Full":
        raise NativeUnsupportedError("Python CIMod supports the default Format='Full'.")
    prepared = []
    for item in geometries:
        association = _association(item)
        if "Conf" not in association:
            raise ValueError("A CIMod association requires Conf.")
        added = {}
        for dependency in dependencies:
            _compute_property(dependency, association, added, options)
        prepared.append(association)
    return function(prepared, **options)


def native_check(geometry, /, **options):
    if not isinstance(geometry, Mapping) or "Conf" not in geometry:
        return False
    if "Num" not in geometry and "Degree" not in geometry:
        unknown = sorted(set(geometry) - PROPERTY_DEPENDENCIES.keys(), key=str)
        if unknown:
            warnings.warn(f"Unrecognized CIPro keys: {unknown!r}", stacklevel=2)
        for key in geometry.keys() & PROPERTY_DEPENDENCIES.keys():
            missing = tuple(dep for dep in PROPERTY_DEPENDENCIES[key] if dep not in geometry)
            if missing:
                warnings.warn(f"CIPro key {key!r} is missing prerequisites {missing!r}", stacklevel=2)
    return True


NATIVE_FUNCTIONS = {
    **_native_geometry.NATIVE_FUNCTIONS,
    **_native_bundles.NATIVE_FUNCTIONS,
    **_native_symmetry.NATIVE_FUNCTIONS,
    **_native_singularities.NATIVE_FUNCTIONS,
    "CICheck": native_check,
    "CIProp": native_property,
    "CIMod": native_modify,
    "Data": native_data,
}
NATIVE_PROPERTIES = {
    **_native_geometry.NATIVE_PROPERTIES,
    **_native_bundles.NATIVE_PROPERTIES,
    **_native_symmetry.NATIVE_PROPERTIES,
    **_native_singularities.NATIVE_PROPERTIES,
}
NATIVE_MODIFICATIONS = {
    **_native_bundles.NATIVE_MODIFICATIONS,
    **_native_symmetry.NATIVE_MODIFICATIONS,
}


def call_native(name, args, options):
    function = NATIVE_FUNCTIONS.get(name)
    if function is None:
        raise NativeUnsupportedError(f"CIPro function {name!r} requires Wolfram.")
    try:
        signature(function).bind(*args, **options)
    except TypeError as exc:
        raise NativeUnsupportedError(f"This {name} call has no matching Python signature: {exc}") from exc
    return function(*args, **options)
