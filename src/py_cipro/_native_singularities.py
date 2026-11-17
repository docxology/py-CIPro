"""Patchwise Jacobian ideals from CIPro's projective singularity routines."""

from fractions import Fraction
from itertools import combinations, product
from math import comb, prod
from numbers import Integral

import sympy as sp
from sympy.polys.polyerrors import CoercionFailed, PolynomialError

from ._native_errors import NativeUnsupportedError
from ._native_geometry import amb_coords


def _equations(value):
    if isinstance(value, (list, tuple)):
        return tuple(equation for item in value for equation in _equations(item))
    if isinstance(value, (sp.Expr, Fraction, Integral)) and not isinstance(value, bool):
        return (sp.sympify(value),)
    raise NativeUnsupportedError("Native singularity checks take exact SymPy polynomial equations.")


def _poly(expression, variables):
    try:
        return sp.Poly(expression, *variables, domain=sp.QQ)
    except (PolynomialError, CoercionFailed) as exc:
        raise NativeUnsupportedError("Native singularity checks take rational polynomials in ambient coordinates.") from exc


def _patch_ideals(geometry):
    if "DefEqs" not in geometry:
        raise NativeUnsupportedError("Supply DefEqs or compute it through CIProp before direct singularity calls.")
    coordinates = amb_coords(geometry)
    variables = tuple(variable for group in coordinates for variable in group)
    ambient = len(variables) - len(coordinates)
    equations = _equations(geometry["DefEqs"])
    if not coordinates or not 1 <= ambient <= 8 or not equations:
        raise NativeUnsupportedError("Native singularity checks require 1–8 affine variables and at least one equation.")
    rank = min(ambient, len(equations))
    if prod(map(len, coordinates)) > 64 or comb(ambient, rank) * comb(len(equations), rank) > 64:
        raise NativeUnsupportedError("Native singularity checks cover at most 64 patches and 64 maximal minors per patch.")
    polynomials = tuple(_poly(equation, variables) for equation in equations)
    if any(polynomial.total_degree() > 12 for polynomial in polynomials):
        raise NativeUnsupportedError("Native singularity checks cover equations of total degree at most 12.")
    for fixed in product(*coordinates):
        patch = tuple((variable, 1) for variable in fixed)
        substitution = dict(patch)
        affine = tuple(variable for variable in variables if variable not in substitution)
        specialized = tuple(equation.xreplace(substitution) for equation in equations)
        jacobian = sp.Matrix([[equation.diff(variable) for equation in specialized] for variable in affine])
        minors = tuple(
            sp.expand(jacobian.extract(rows, columns).det())
            for rows in combinations(range(ambient), rank)
            for columns in combinations(range(len(equations)), rank)
        )
        yield specialized + minors, patch, affine


def singularity_locus(geometry, **_options):
    """Return the generators and coordinate substitution rules on each covered patch."""
    data = tuple(_patch_ideals(geometry))
    return tuple(item[0] for item in data), tuple(item[1] for item in data)


def singularity_check(geometry, *, FieldChar=101, **_options):
    """Check whether the affine Jacobian ideals contain one, in the requested field."""
    if "SingularLocus" in geometry:
        raise NativeUnsupportedError("The upstream cached SingularLocus branch has no Python equivalent.")
    if isinstance(FieldChar, bool) or not isinstance(FieldChar, Integral):
        raise NativeUnsupportedError("Native FieldChar must be zero or a positive prime.")
    characteristic = int(FieldChar)
    if characteristic != 0 and not sp.isprime(characteristic):
        raise NativeUnsupportedError("Native FieldChar must be zero or a positive prime.")
    for generators, _patch, variables in _patch_ideals(geometry):
        if characteristic:
            reduced = []
            for generator in generators:
                terms = {}
                for monomial, coefficient in _poly(generator, variables).terms():
                    numerator, denominator = map(int, coefficient.as_numer_denom())
                    if denominator % characteristic == 0:
                        raise NativeUnsupportedError("A rational coefficient does not reduce in the requested field.")
                    terms[monomial] = numerator * pow(denominator, -1, characteristic) % characteristic
                reduced.append(sp.Poly.from_dict(terms, variables, modulus=characteristic).as_expr())
            basis = sp.groebner(reduced, *variables, modulus=characteristic)
        else:
            basis = sp.groebner(generators, *variables, domain=sp.QQ)
        if tuple(basis) != (sp.S.One,):
            return "True"  # CIPro v1.0 uses a string in this branch.
    return False


NATIVE_FUNCTIONS = {"SingularityCheck": singularity_check, "SingularityLocus": singularity_locus}
NATIVE_PROPERTIES = {"Singular": singularity_check, "SingularLocus": singularity_locus}
