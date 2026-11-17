"""Exact integer-configuration geometry from the released CIPro v1.0 formulas."""

from collections import defaultdict
from collections.abc import Mapping, Sequence
from fractions import Fraction
from itertools import product
from math import comb, factorial, prod
from numbers import Integral
from warnings import warn

import sympy as sp

from ._native_errors import NativeUnsupportedError


def _sequence(value, name):
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be a sequence.")
    return value


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, (Integral, sp.Integer)):
        if isinstance(value, sp.Expr) and not value.is_number:
            raise NativeUnsupportedError(f"The Python implementation requires numeric {name}.")
        raise ValueError(f"{name} must be an integer.")
    return int(value)


def _geometry(geometry):
    if not isinstance(geometry, Mapping):
        raise ValueError("Expected a geometry association (mapping).")
    return geometry


def _configuration(geometry):
    geometry = _geometry(geometry)
    value = geometry["Conf"] if "Conf" in geometry else def_conf(geometry)
    rows = tuple(
        tuple(_integer(value, "configuration degree") for value in _sequence(row, "Conf row"))
        for row in _sequence(value, "Conf")
    )
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("Conf must be a nonempty rectangular matrix of degrees.")
    return rows


def _ambient_dimensions(geometry):
    geometry = _geometry(geometry)
    if "DimPs" not in geometry:
        return dim_ps(geometry)
    dims = tuple(_integer(d, "ambient dimension") for d in _sequence(geometry["DimPs"], "DimPs"))
    if not dims or min(dims) < 0:
        raise ValueError("DimPs must contain nonnegative dimensions.")
    return dims


def _configuration_and_dimensions(geometry):
    rows = _configuration(geometry)
    dims = _ambient_dimensions(geometry)
    if len(rows) != len(dims):
        raise ValueError("Conf and DimPs must have the same number of ambient factors.")
    return rows, dims


def _cached(geometry, key, compute, options):
    return geometry[key] if key in geometry else compute(geometry, **options)


def _symbol_base(name):
    if isinstance(name, sp.IndexedBase):
        return name
    if isinstance(name, sp.Symbol) or isinstance(name, str) and name:
        return sp.IndexedBase(name)
    raise NativeUnsupportedError("Use a symbol name, SymPy Symbol, or IndexedBase for a Python coordinate basis.")


def kahler_basis(count, name="J"):
    """Build the indexed basis corresponding to Wolfram's Subscript[name, i]."""
    base = _symbol_base(name)
    return tuple(base[i] for i in range(1, count + 1))


def _number(value):
    if isinstance(value, sp.Integer):
        return int(value)
    if isinstance(value, sp.Rational):
        return Fraction(int(value.p), int(value.q))
    return value


def _poly(value, variables):
    if not isinstance(value, (sp.Expr, Integral, Fraction)):
        raise NativeUnsupportedError("The Python implementation expects an exact SymPy polynomial or scalar.")
    try:
        return sp.Poly(value, *variables)
    except sp.PolynomialError as exc:
        raise NativeUnsupportedError("The Python implementation expects a polynomial in the indexed basis.") from exc


def _column_form(column, variables):
    return sum(coefficient * variable for coefficient, variable in zip(column, variables))


def _dense_tensor(size, rank, entry, prefix=()):
    if rank == 0:
        return _number(entry(prefix))
    return tuple(_dense_tensor(size, rank - 1, entry, (*prefix, i)) for i in range(size))


def _tensor_at(tensor, indices):
    try:
        for index in indices:
            tensor = tensor[index]
    except (TypeError, IndexError, KeyError) as exc:
        raise ValueError("ISec does not have the expected dimensions.") from exc
    return tensor


def _indices(powers):
    return tuple(i for i, n in enumerate(powers) for _ in range(n))


def _powers(indices, size):
    return tuple(indices.count(i) for i in range(size))


def _multinomial(powers):
    return factorial(sum(powers)) // prod(factorial(n) for n in powers)


def def_conf(geometry, **options):
    geometry = _geometry(geometry)
    return tuple(() for _ in _ambient_dimensions(geometry)) if "DimPs" in geometry else None


def dim_ps(geometry, **options):
    return tuple(max(sum(row), 2) - 1 for row in _configuration(geometry))


def amb_coords(geometry, **options):
    dims = _ambient_dimensions(geometry)
    name = options.get("CoordName", "x")
    if isinstance(name, (list, tuple)):
        if len(name) < len(dims):
            raise NativeUnsupportedError("CoordName needs one symbol per ambient factor in Python.")
        return tuple(tuple(_symbol_base(label)[j] for j in range(d + 1)) for label, d in zip(name, dims))
    base = _symbol_base(name)
    return tuple(tuple(base[i, j] for j in range(d + 1)) for i, d in enumerate(dims, 1))


def amb_dim(geometry, **options):
    return sum(_ambient_dimensions(geometry))


def ci_dim(geometry, **options):
    rows = _configuration(geometry)
    ambient = _integer(_cached(geometry, "AmbDim", amb_dim, options), "ambient dimension")
    columns = tuple(zip(*rows))
    if any(not any(column) for column in columns):
        warn("Configuration matrix contains a zero degree section.", stacklevel=2)
        return -1
    negative = sum(any(degree < 0 for degree in column) for column in columns)
    if negative:
        warn(f"Configuration contains {negative} section(s) with negative degrees.", stacklevel=2)
    return ambient - len(columns) + negative


def cy_q(geometry, **options):
    rows, dimensions = _configuration_and_dimensions(geometry)
    return all(sum(row) - 1 == dimension for row, dimension in zip(rows, dimensions))


def canonical_bundle(geometry, **options):
    rows, dimensions = _configuration_and_dimensions(geometry)
    return tuple((sum(row) - dimension - 1,) for row, dimension in zip(rows, dimensions))


def mu(geometry, **options):
    rows = _configuration(geometry)
    basis = kahler_basis(len(rows), options.get("KFormsName", "J"))
    return sp.prod(_column_form(column, basis) for column in zip(*rows))


def intersec_form(geometry, **options):
    rows, dims = _configuration_and_dimensions(geometry)
    dimension = _integer(_cached(geometry, "CIDim", ci_dim, options), "CI dimension")
    if dimension <= 0:
        return None
    forms = kahler_basis(len(rows), options.get("KFormsName", "J"))
    moduli = kahler_basis(len(rows), options.get("KModuliName", "t"))
    integrand = _poly(_cached(geometry, "Mu", mu, options), forms)
    terms = []
    for powers, coefficient in integrand.terms():
        remainder = tuple(target - power for target, power in zip(dims, powers))
        if min(remainder) >= 0 and sum(remainder) == dimension:
            terms.append(coefficient * _multinomial(remainder) * sp.prod(t**n for t, n in zip(moduli, remainder)))
    return sp.Add(*terms)


def intersec(geometry, **options):
    rows, _ = _configuration_and_dimensions(geometry)
    value = _cached(geometry, "ISecForm", intersec_form, options)
    if value is None:
        return None
    moduli = kahler_basis(len(rows), options.get("KModuliName", "t"))
    coefficients = _poly(value, moduli)

    def intersection(indices):
        powers = _powers(indices, len(rows))
        return coefficients.coeff_monomial(powers) / _multinomial(powers)

    return _dense_tensor(len(rows), coefficients.total_degree(), intersection)


def _multiply(left, right, dims, limit):
    result = defaultdict(int)
    for a, coefficient_a in left.items():
        for b, coefficient_b in right.items():
            powers = tuple(x + y for x, y in zip(a, b))
            if sum(powers) <= limit and all(p <= d for p, d in zip(powers, dims)):
                result[powers] += coefficient_a * coefficient_b
    return {powers: c for powers, c in result.items() if c}


def chern_poly(geometry, **options):
    rows, dims = _configuration_and_dimensions(geometry)
    dimension = _integer(_cached(geometry, "CIDim", ci_dim, options), "CI dimension")
    if dimension < 0:
        raise NativeUnsupportedError("CPoly requires a nonnegative CI dimension.")
    n = len(rows)
    one = (0,) * n
    units = tuple(tuple(int(i == j) for i in range(n)) for j in range(n))
    polynomial = {one: 1}
    for basis, dim in zip(units, dims):
        factor = {tuple(k * i for i in basis): comb(dim + 1, k) for k in range(min(dim, dimension) + 1)}
        polynomial = _multiply(polynomial, factor, dims, dimension)
    for column in zip(*rows):
        linear = {basis: -degree for basis, degree in zip(units, column) if degree}
        power = {one: 1}
        reciprocal = {one: 1}
        for _ in range(dimension):
            power = _multiply(power, linear, dims, dimension)
            reciprocal.update(power)
        polynomial = _multiply(polynomial, reciprocal, dims, dimension)
    forms = kahler_basis(n, options.get("KFormsName", "J"))
    return sp.Add(*(coefficient * sp.prod(j**k for j, k in zip(forms, powers)) for powers, coefficient in polynomial.items()))


def class_convert(polynomial, intersections, dimension, h11):
    """Return the CIPro coefficient tensors, dualizing the higher degrees by intersection."""
    dimension = _integer(dimension, "CI dimension")
    h11 = _integer(h11, "basis size")
    if dimension <= 0 or h11 <= 0:
        raise NativeUnsupportedError("ClassConvert requires a positive CI dimension and a nonempty basis.")
    forms = kahler_basis(h11)
    polys = defaultdict(list)
    for powers, coefficient in _poly(polynomial, forms).terms():
        polys[sum(powers)].append((_indices(powers), coefficient))
    values = []
    half_dimension = dimension // 2
    for degree in range(1, half_dimension + 1):
        coefficients = dict(polys[degree])
        values.append(_dense_tensor(h11, degree, lambda idx: coefficients.get(idx, 0)))
    for degree in range(half_dimension + 1, dimension + 1):
        values.append(_dense_tensor(
            h11,
            dimension - degree,
            lambda idx: sum(value * _tensor_at(intersections, (*idx, *selected)) for selected, value in polys[degree]),
        ))
    return tuple(values)


def _homogeneous_parts(polynomial, variables, count):
    result = [0] * count
    for powers, coefficient in _poly(polynomial, variables).terms():
        degree = sum(powers)
        if 1 <= degree <= count:
            result[degree - 1] += coefficient * sp.prod(base**n for base, n in zip(variables, powers))
    return tuple(result)


def class_to_class(polynomial, dimension, h11, rank, old="C", new="Ch"):
    """Apply the implemented characteristic-class conversions with exact coefficients."""
    dimension = _integer(dimension, "CI dimension")
    h11 = _integer(h11, "basis size")
    if h11 <= 0 or dimension < 0:
        raise ValueError("Class conversions require a nonempty basis and a nonnegative dimension.")
    if not isinstance(old, str) or not isinstance(new, str):
        raise NativeUnsupportedError("Use string identifiers for the input and output class types.")
    mode = old, new
    max_degree = {("C", "Ch"): 3, ("C", "Td"): 4, ("Ch", "C"): 4}.get(mode)
    if max_degree is None or dimension > max_degree:
        raise NativeUnsupportedError(f"The released {old} to {new} conversion is supported through dimension {max_degree} in Python.")
    c1, c2, c3, c4 = _homogeneous_parts(polynomial, kahler_basis(h11), 4)
    if mode == ("C", "Ch"):
        if not isinstance(rank, (Integral, sp.Expr, Fraction)):
            raise NativeUnsupportedError("Use a Python or SymPy scalar for rank.")
        pieces = (rank, c1, (c1**2 - 2 * c2) * sp.Rational(1, 2), (c1**3 - 3*c1*c2 + 3*c3) * sp.Rational(1, 6))
    elif mode == ("C", "Td"):
        pieces = (1, c1 * sp.Rational(1, 2), (c1**2 + c2) * sp.Rational(1, 12), c1*c2 * sp.Rational(1, 24),
                  (-c1**4 + 4*c1**2*c2 + c1*c3 + 3*c2**2 - c4) * sp.Rational(1, 720))
    else:
        pieces = (1, c1, (c1**2 - 2*c2) * sp.Rational(1, 2), (c1**3 - 6*c1*c2 + 12*c3) * sp.Rational(1, 6),
                  (c1**4 - 12*c1**2*c2 + 12*c2**2 + 48*c1*c3 - 144*c4) * sp.Rational(1, 24))
    return sp.expand(sum(pieces[:dimension + 1]))


def _converted_poly(geometry, options, mode):
    if _symbol_base(options.get("KFormsName", "J")) != sp.IndexedBase("J"):
        raise NativeUnsupportedError("The released characteristic-class converter uses the default J basis.")
    dimension = _integer(_cached(geometry, "CIDim", ci_dim, options), "CI dimension")
    polynomial = _cached(geometry, "CPoly", chern_poly, options)
    return class_to_class(polynomial, dimension, len(_configuration(geometry)), dimension, "C", mode)


def chern_character_poly(geometry, **options):
    return _converted_poly(geometry, options, "Ch")


def todd_poly(geometry, **options):
    return _converted_poly(geometry, options, "Td")


def _converted_tensor(geometry, options, key, compute):
    if _symbol_base(options.get("KFormsName", "J")) != sp.IndexedBase("J"):
        raise NativeUnsupportedError("The released characteristic-class converter uses the default J basis.")
    polynomial = _cached(geometry, key, compute, options)
    intersections = _cached(geometry, "ISec", intersec, options)
    dimension = _cached(geometry, "CIDim", ci_dim, options)
    return class_convert(polynomial, intersections, dimension, len(_configuration(geometry)))


def chern(geometry, **options):
    return _converted_tensor(geometry, options, "CPoly", chern_poly)


def chern_character(geometry, **options):
    return _converted_tensor(geometry, options, "ChPoly", chern_character_poly)


def todd(geometry, **options):
    return _converted_tensor(geometry, options, "TdPoly", todd_poly)


def euler(geometry, **options):
    dimension = _integer(_cached(geometry, "CIDim", ci_dim, options), "CI dimension")
    if dimension > 0:
        return _cached(geometry, "C", chern, options)[-1]
    dims = _ambient_dimensions(geometry)
    top = sp.prod(j**d for j, d in zip(kahler_basis(len(dims)), dims))
    return _number(sp.cancel(_cached(geometry, "Mu", mu, options) / top))


def hilbert_expand(dimensions, name, hilbert, output_format):
    """Extract the released HilbertFormat degree box or selected multidegrees."""
    if output_format in ((), []):
        return hilbert
    dims = _sequence(dimensions, "ambient dimensions")
    variables = kahler_basis(len(dims), name)
    if isinstance(output_format, (Integral, sp.Integer)):
        output_format = (0, _integer(output_format, "HilbertFormat"))
    degrees = _sequence(output_format, "HilbertFormat")
    if all(isinstance(row, (tuple, list)) for row in degrees):
        requested = [tuple(_integer(d, "Hilbert degree") for d in row) for row in degrees]
    else:
        bounds = tuple(_integer(d, "Hilbert degree bound") for d in degrees)
        requested = list(product(range(bounds[0], bounds[-1] + 1), repeat=len(dims)))
    if any(len(row) != len(dims) for row in requested):
        raise ValueError("Each Hilbert multidegree must have one degree per ambient factor.")
    if any(d < 0 for row in requested for d in row):
        raise NativeUnsupportedError("The Python Hilbert expansion requires nonnegative multidegrees.")
    zero = (0,) * len(variables)
    all_degrees = [zero, *(row for row in requested if row != zero)]
    if not isinstance(hilbert, (sp.Expr, Integral, Fraction)):
        raise NativeUnsupportedError("Use an exact Python or SymPy expression for the Hilbert series.")
    expanded = sp.sympify(hilbert)
    for i, variable in enumerate(variables):
        maximum = max(row[i] for row in all_degrees)
        expanded = sp.series(expanded, variable, 0, maximum + 1).removeO()
    coefficients = _poly(expanded, variables)
    return sp.Add(*(coefficients.coeff_monomial(row) * sp.prod(t**d for t, d in zip(variables, row)) for row in all_degrees))


def hilbert_series(geometry, **options):
    rows, dims = _configuration_and_dimensions(geometry)
    variables = kahler_basis(len(dims), "t")
    numerator = sp.prod(1 - sp.prod(t**d for t, d in zip(variables, column)) for column in zip(*rows))
    denominator = sp.prod((1 - t)**(d + 1) for t, d in zip(variables, dims))
    return hilbert_expand(dims, "t", numerator / denominator, options.get("HilbertFormat", ()))


NATIVE_FUNCTIONS = {
    "DefConf": def_conf,
    "DimPs": dim_ps,
    "AmbCoords": amb_coords,
    "AmbDim": amb_dim,
    "CIDim": ci_dim,
    "CYQ": cy_q,
    "Mu": mu,
    "IntersecForm": intersec_form,
    "Intersec": intersec,
    "CCIPoly": chern_poly,
    "ClassConvert": class_convert,
    "Class2Class": class_to_class,
    "CCI": chern,
    "ChCIPoly": chern_character_poly,
    "ChCI": chern_character,
    "TdCIPoly": todd_poly,
    "TdCI": todd,
    "EulerCI": euler,
    "KCI": canonical_bundle,
    "HilbertSeries": hilbert_series,
    "HilbertExpand": hilbert_expand,
}

NATIVE_PROPERTIES = {
    "Conf": def_conf,
    "DimPs": dim_ps,
    "AmbCoords": amb_coords,
    "AmbDim": amb_dim,
    "CIDim": ci_dim,
    "CY": cy_q,
    "Mu": mu,
    "ISecForm": intersec_form,
    "ISec": intersec,
    "CPoly": chern_poly,
    "C": chern,
    "ChPoly": chern_character_poly,
    "Ch": chern_character,
    "TdPoly": todd_poly,
    "Td": todd,
    "Euler": euler,
    "K": canonical_bundle,
    "HilbertSeries": hilbert_series,
}
