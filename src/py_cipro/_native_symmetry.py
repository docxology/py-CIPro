"""Native finite matrix and symbolic polynomial operations from CIPro v1.0."""

from collections import Counter
from collections.abc import Mapping, Sequence
from itertools import combinations, groupby, permutations, product
from math import comb, factorial, isfinite, prod
from numbers import Number
from operator import index
import random

from sympy import Expr, Float, I, ImmutableMatrix, IndexedBase, Integer, Poly, Rational, Symbol, exp, expand, pi, simplify, sympify
from sympy.matrices.exceptions import NonInvertibleMatrixError
from sympy.polys.polyerrors import PolynomialError

from ._native_errors import NativeUnsupportedError


_TOLERANCE = Rational(1, 10**10)
_MAX_GROUP_SIZE = 1024
_MAX_REORDERS = factorial(8)
_MAX_MONOMIALS = 50_000
_MAX_INVARIANT_TRIALS = 2_000


def _sequence(value):
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _integer(value):
    if isinstance(value, bool):
        raise ValueError("Expected an integer, not a Boolean")
    try:
        return index(value)
    except TypeError as exc:
        raise NativeUnsupportedError("This Python operation requires integral input") from exc


def _expression(value):
    if isinstance(value, str):
        return Symbol(value)
    if isinstance(value, Expr):
        return value
    if isinstance(value, Number) and not isinstance(value, bool):
        return sympify(value)
    raise NativeUnsupportedError("Use Python numbers or a SymPy expression for this operation")


def _is_matrix(value):
    return (
        _sequence(value) and bool(value) and _sequence(value[0]) and bool(value[0])
        and all(_sequence(row) and len(row) == len(value[0]) and not any(_sequence(x) for x in row) for row in value)
    )


def _matrix(value):
    if not _is_matrix(value):
        raise ValueError("Expected a nonempty rectangular matrix")
    return tuple(tuple(row) for row in value)


def _numeric_matrix(value, *, exact=False):
    matrix = tuple(tuple(_expression(x) for x in row) for row in _matrix(value))
    if any(x.is_number is not True or x.is_finite is not True for row in matrix for x in row):
        raise NativeUnsupportedError("Native group calculations require finite numeric matrix entries")
    if exact and any(x.has(Float) for row in matrix for x in row):
        raise NativeUnsupportedError("Native group enumeration requires exact matrix entries")
    return matrix


def _identity(size):
    return tuple(tuple(int(i == j) for j in range(size)) for i in range(size))


def _transpose(matrix):
    return tuple(zip(*matrix))


def _dot(left, right):
    if len(left[0]) != len(right):
        raise ValueError("Matrices have incompatible dimensions")
    columns = _transpose(right)
    return tuple(tuple(sum(a * b for a, b in zip(row, column)) for column in columns) for row in left)


def _vector_dot(matrix, vector):
    return tuple(row[0] for row in _dot(matrix, tuple((value,) for value in vector)))


def _blocks(sizes):
    ranges = []
    offset = 0
    for size in sizes:
        size = _integer(size)
        if size < 1:
            raise ValueError("Projective block sizes must be positive")
        ranges.append(range(offset, offset + size))
        offset += size
    return tuple(ranges), offset


def _projective_sizes(association):
    return tuple(_integer(dim) + 1 for dim in association["DimPs"])


def block_matrix2(first, second):
    """Join rectangular blocks with zero padding off the block diagonal."""
    one, two = _matrix(first), _matrix(second)
    return tuple(row + (0,) * len(two[0]) for row in one) + tuple((0,) * len(one[0]) + row for row in two)


def block_matrix(matrices):
    """Join a sequence of valid nonempty blocks along the diagonal."""
    if not any(_is_matrix(matrix) for matrix in matrices):
        return None
    if not all(_is_matrix(matrix) for matrix in matrices):
        raise NativeUnsupportedError("Native BlockMatrix requires all supplied blocks to be rectangular")
    result = _matrix(matrices[0])
    for matrix in matrices[1:]:
        result = block_matrix2(result, matrix)
    return result


def perm_matrix(matrix, sizes):
    """Return the block occupancy matrix used by CIPro's permutation tests."""
    matrix = _numeric_matrix(matrix)
    blocks, size = _blocks(sizes)
    if (len(matrix), len(matrix[0])) != (size, size):
        return {"Gen": ()}
    return tuple(tuple(int(any(matrix[i][j].is_zero is not True for i in rows for j in cols)) for cols in blocks) for rows in blocks)


def mat_proj_trivial(matrix, sizes):
    matrix = _numeric_matrix(matrix)
    blocks, size = _blocks(sizes)
    if (len(matrix), len(matrix[0])) != (size, size):
        return False
    return (
        all(matrix[i][j].is_zero is True for i in range(size) for j in range(size) if i != j)
        and all(matrix[i][i] == matrix[block.start][block.start] for block in blocks for i in block)
    )


def _within_tolerance(distance, *, inclusive=False):
    comparison = distance <= _TOLERANCE if inclusive else distance < _TOLERANCE
    try:
        return bool(comparison)
    except TypeError:
        # Algebraic complex entries can leave Abs unevaluated even with no free symbols.
        try:
            numeric = abs(complex(distance.evalf(50)))
        except (TypeError, ValueError, OverflowError) as exc:
            raise NativeUnsupportedError("The Python backend could not resolve the numeric matrix tolerance") from exc
        if not isfinite(numeric):
            raise NativeUnsupportedError("The Python backend could not resolve the numeric matrix tolerance")
        return numeric <= float(_TOLERANCE) if inclusive else numeric < float(_TOLERANCE)


def mat_proj_equiv(first, second, sizes):
    first = _numeric_matrix(first)
    second = _numeric_matrix(second)
    blocks, size = _blocks(sizes)
    if any((len(matrix), len(matrix[0])) != (size, size) for matrix in (first, second)):
        return False
    left, right = map(ImmutableMatrix, (first, second))
    try:
        if left.rank() != size:
            return False
        quotient = left * right.inv()
    except NonInvertibleMatrixError:
        return False
    off_diagonal = sum(abs(quotient[i, j]) for i in range(size) for j in range(size) if i != j)
    return (
        _within_tolerance(off_diagonal, inclusive=True)
        and all(
            _within_tolerance(sum(abs(quotient[i, i] - quotient[block.start, block.start]) for i in block), inclusive=True)
            for block in blocks
        )
    )


def _matrix_element(element, *, exact=False):
    matrices = (element,) if _is_matrix(element) else element
    if not _sequence(matrices) or not matrices:
        raise ValueError("A group element must contain at least one matrix")
    result = tuple(_numeric_matrix(matrix, exact=exact) for matrix in matrices)
    if any(len(matrix) != len(matrix[0]) for matrix in result):
        raise ValueError("Every group action must be square")
    return result


def _elements(elements, *, exact=False):
    result = tuple(_matrix_element(element, exact=exact) for element in elements)
    if result and any(tuple(map(len, element)) != tuple(map(len, result[0])) for element in result):
        raise ValueError("All elements must act on the same matrix dimensions")
    return result


def _product(left, right):
    if len(left) != len(right):
        raise ValueError("Group elements contain different numbers of matrix factors")
    return tuple(_dot(a, b) for a, b in zip(left, right))


def md(groups):
    """Multiply corresponding matrices across any number of matrix lists."""
    if not groups:
        return ()
    groups = tuple(tuple(tuple(tuple(_expression(x) for x in row) for row in _matrix(matrix)) for matrix in group) for group in groups)
    result = groups[0]
    for group in groups[1:]:
        result = _product(result, group)
    return result


def arrange_gen(association):
    return _elements(association["Gen"])


def gen(association, **_options):
    if "Conf" in association and "DimPs" in association:
        return ((_identity(sum(_projective_sizes(association))), _identity(len(_matrix(association["Conf"])[0]))),)
    diagonal = tuple(exp(2 * pi * I * Rational(power, 5)) for power in (0, 1, 2, -2, -1))
    return ((tuple(tuple(diagonal[i] if i == j else 0 for j in range(5)) for i in range(5)), ((1,),)),)


def _distance(left, right):
    return sum(abs(simplify(a - b)) for lm, rm in zip(left, right) for lr, rr in zip(lm, rm) for a, b in zip(lr, rr))


def gen_order(association, *, MaxGenOrder=99, **_options):
    generators = arrange_gen(association)
    limit = _integer(MaxGenOrder)
    if limit > _MAX_GROUP_SIZE:
        raise NativeUnsupportedError(f"Native GenOrder supports at most {_MAX_GROUP_SIZE} powers")
    orders = []
    for generator in generators:
        identity = tuple(_identity(len(matrix)) for matrix in generator)
        power = identity
        for order in range(1, limit + 1):
            power = _product(power, generator)
            if _within_tolerance(_distance(power, identity)):
                orders.append(order)
                break
        else:
            orders.append(None)
    return tuple(orders)


def abelian(association, **_options):
    return all(
        _within_tolerance(_distance(_product(a, b), _product(b, a)))
        for a, b in combinations(arrange_gen(association), 2)
    )


def proj_abelian(association, **_options):
    """Reproduce the v1.0 test, which compares each product with itself."""
    generators = arrange_gen(association)
    if len(generators) < 2:
        return True
    return all(mat_proj_equiv((matrix := _product(a, b)[0]), matrix, _projective_sizes(association)) for a, b in combinations(generators, 2))


def _simplify_element(element):
    return tuple(tuple(tuple(simplify(x) for x in row) for row in matrix) for matrix in element)


def gen_group(association, **_options):
    generators = tuple(dict.fromkeys(_simplify_element(element) for element in _elements(association["Gen"], exact=True)))
    group = dict.fromkeys(generators)
    if len(group) > _MAX_GROUP_SIZE:
        raise NativeUnsupportedError(f"Native GenGroup supports at most {_MAX_GROUP_SIZE} elements")
    stack = list(generators)
    while stack:
        element = stack.pop()
        for generator in generators:
            multiplied = _simplify_element(_product(element, generator))
            if multiplied not in group:
                if len(group) >= _MAX_GROUP_SIZE:
                    raise NativeUnsupportedError(f"Native GenGroup could not close within {_MAX_GROUP_SIZE} elements")
                group[multiplied] = None
                stack.append(multiplied)
    return tuple(group)


def g_order(association, **_options):
    return len(association["Group"])


def proj_trivial_group(association, **_options):
    sizes = _projective_sizes(association)
    return tuple(element for element in _elements(association["Group"]) if mat_proj_trivial(element[0], sizes))


def proj_trivial_order(association, **_options):
    return len(association["ProjTrivialGroup"])


def _number_order(value):
    real, imaginary = value.as_real_imag()
    return real, abs(imaginary), imaginary


def proj_gen_group(association, **_options):
    remaining = _elements(association["Group"], exact=True)
    trivial = _elements(association["ProjTrivialGroup"], exact=True)
    classes = []
    while remaining:
        first = remaining[0]
        coset = tuple(_simplify_element(_product(first, member)) for member in trivial)
        if first not in coset:
            raise NativeUnsupportedError("The supplied projectively trivial members do not form compatible cosets")
        classes.append(coset)
        # Wolfram Complement sorts its result after subtracting the class.
        remaining = tuple(sorted(set(remaining) - set(coset), key=lambda element: tuple(
            tuple(tuple(_number_order(x) for x in row) for row in matrix) for matrix in element
        )))
    return tuple(classes)


def proj_order(association, **_options):
    denominator = len(association["ProjTrivialGroup"])
    if not denominator:
        raise NativeUnsupportedError("The projectively trivial subgroup must contain the identity")
    return Rational(len(association["Group"]), denominator)


def perm_group_gen(association, **_options):
    sizes = _projective_sizes(association)
    result = []
    for element in arrange_gen(association):
        group = (perm_matrix(element[0], sizes),)
        if len(element) > 1:
            group += (perm_matrix(element[1], (1,) * len(element[1])),)
        result.append(group)
    return tuple(result)


def _reorder(matrix, rows, cols):
    return tuple(tuple(matrix[i][j] for j in cols) for i in rows)


def _perm(order):
    identity = _identity(len(order))
    return tuple(identity[i] for i in order)


def _int_matrix(value):
    return tuple(tuple(_integer(x) for x in row) for row in _matrix(value))


def _max_conjugates(matrix):
    size = len(matrix)
    if factorial(size) > _MAX_REORDERS:
        raise NativeUnsupportedError("Native symmetric normal form supports permutation blocks of at most 8 rows")
    greatest = None
    orders = []
    for order in permutations(range(size)):
        candidate = _reorder(matrix, order, order)
        if greatest is None or candidate > greatest:
            greatest, orders = candidate, [order]
        elif candidate == greatest:
            orders.append(order)
    return greatest, orders


def symm_mat_normal0(value, *, MaxDim=8, **_options):
    matrix = _int_matrix(value)
    if len(matrix) != len(matrix[0]):
        raise ValueError("SymmMatNormal0 requires a square matrix")
    normal, orders = _max_conjugates(matrix)
    # MaxDim only controls Wolfram's warning. Native calculation has its own fixed bound.
    return normal, tuple(_perm(order) for order in orders)


def symm_mat_normal(value, **_options):
    matrix = _int_matrix(value)
    if matrix != _transpose(matrix):
        raise ValueError("SymmMatNormal requires a symmetric matrix")
    tallies = [tuple(sorted(Counter(row).items())) for row in matrix]
    # Canonical Wolfram ordering compares shorter expressions before their contents.
    row_order = sorted(range(len(matrix)), key=lambda i: (len(tallies[i]), tallies[i]))
    blocks = [tuple(block) for _, block in groupby(row_order, key=tallies.__getitem__)]
    local_orders = [tuple(tuple(block[i] for i in order) for order in _max_conjugates(_reorder(matrix, block, block))[1]) for block in blocks]
    if prod(map(len, local_orders)) > _MAX_REORDERS:
        raise NativeUnsupportedError("Native symmetric normal form exceeds its permutation search bound")
    candidates = (tuple(i for block in ordering for i in block) for ordering in product(*local_orders))
    order = max(candidates, key=lambda p: _reorder(matrix, p, p))
    return _reorder(matrix, order, order), _perm(order)


def mat_normal(value):
    matrix = _int_matrix(value)
    _, row_perm = symm_mat_normal(_dot(matrix, _transpose(matrix)))
    rows = _dot(row_perm, matrix)
    columns = _transpose(rows)
    order = sorted(range(len(columns)), key=columns.__getitem__, reverse=True)
    return _transpose(tuple(columns[i] for i in order)), row_perm, _perm(order)


def ci_normal(association, **_options):
    if not isinstance(association, Mapping):
        association = association[0]
    configuration, row_perm, col_perm = mat_normal(association["Conf"])
    dimensions = tuple(_integer(dim) for dim in association["DimPs"])
    return {"Conf": configuration, "DimPs": _vector_dot(row_perm, dimensions), "RowPerm": row_perm, "ColPerm": col_perm}


def ci_equiv(associations, **_options):
    first, second = (ci_normal(association) for association in associations[:2])
    return (first["Conf"], first["DimPs"]) == (second["Conf"], second["DimPs"])


def ci_equiv2(first, second, power):
    matrices = (_int_matrix(first["Conf"]), _int_matrix(second["Conf"]))
    power = _integer(power)
    if not 1 <= power <= 8:
        raise NativeUnsupportedError("Native CIEquiv2 supports 1 through 8 comparison powers")
    permutations_found = []
    for left, right in (matrices, tuple(_transpose(matrix) for matrix in matrices)):
        orders = []
        for exponent in range(1, power + 1):
            values = [tuple(sum(x**exponent for x in row) for row in matrix) for matrix in (left, right)]
            if sorted(values[0]) != sorted(values[1]):
                return False, ()
            if len(set(values[1])) != len(values[1]):
                raise NativeUnsupportedError("Native CIEquiv2 requires unambiguous powered matrix signatures")
            targets = {value: i for i, value in enumerate(values[1])}
            orders.append(tuple(targets[value] for value in values[0]))
        if len(set(orders)) != 1:
            return False, ()
        permutations_found.append(_perm(orders[0]))
    row, col = permutations_found
    if _dot(_dot(row, matrices[0]), _transpose(col)) != matrices[1]:
        return "Methods Insufficient"
    return True, row, col


def _partitions(degree, length, largest):
    if degree == 0:
        yield ()
    elif length:
        for first in range(min(largest, degree), (degree + length - 1) // length - 1, -1):
            for rest in _partitions(degree - first, length - 1, first):
                yield first, *rest


def _unique_orders(counts, length):
    if length == 0:
        yield ()
    else:
        for value, count in counts.items():
            if count:
                counts[value] -= 1
                for suffix in _unique_orders(counts, length - 1):
                    yield value, *suffix
                counts[value] += 1


def m_list(degree, variables):
    """Enumerate monomials in CIPro's integer-partition order."""
    degree = _integer(degree)
    if degree < 0:
        return (0,)
    variables = tuple(_expression(value) for value in variables)
    if not variables:
        return ()
    size = len(variables)
    if size > 100 or comb(degree + size - 1, size - 1) > _MAX_MONOMIALS:
        raise NativeUnsupportedError("Native monomial enumeration exceeds its size bound")
    return tuple(
        prod(variable**power for variable, power in zip(variables, powers))
        for partition in _partitions(degree, size, degree)
        for powers in _unique_orders(Counter(partition + (0,) * (size - len(partition))), size)
    )


def mm_list(multidegree, variables):
    if not variables:
        return ()
    if len(multidegree) != len(variables):
        raise ValueError("Give one coordinate list per multidegree entry")
    groups = tuple(m_list(degree, group) for degree, group in zip(multidegree, variables))
    if prod(map(len, groups)) > _MAX_MONOMIALS:
        raise NativeUnsupportedError("Native multidegree monomial enumeration exceeds its size bound")
    return tuple(prod(terms) for terms in product(*groups))


def mmon_list(association, **_options):
    variables = association["AmbCoords"]
    return tuple(mm_list(degree, variables) for degree in _transpose(_int_matrix(association["Conf"])))


def _flatten_coords(coordinates):
    flat = tuple(_expression(x) for group in coordinates for x in (group if _sequence(group) else (group,)))
    if not flat or len(flat) != len(set(flat)):
        raise NativeUnsupportedError("Native polynomial transformations require distinct coordinates")
    return flat


def _transform(polynomial, coordinates, matrix):
    if (len(matrix), len(matrix[0])) != (len(coordinates), len(coordinates)):
        raise ValueError("The matrix must act on the flattened coordinate vector")
    return _expression(polynomial).xreplace(dict(zip(coordinates, _vector_dot(matrix, coordinates))))


def transform_poly(polynomial, coordinates, matrix):
    matrix = tuple(tuple(_expression(x) for x in row) for row in _matrix(matrix))
    return _transform(polynomial, _flatten_coords(coordinates), matrix)


def _act(polynomials, coordinates, element, *, ignore_incompatible=False):
    values = tuple(_transform(polynomial, coordinates, element[0]) for polynomial in polynomials)
    if len(element) > 1:
        equations = element[1]
        if len(equations) == len(values) or not ignore_incompatible:
            values = _vector_dot(equations, values)
    return values


def _reynolds(polynomials, coordinates, group):
    if not group:
        raise NativeUnsupportedError("A nonempty finite group is needed for ReynoldsPoly")
    if not polynomials:
        return ()
    transformed = (_act(polynomials, coordinates, element, ignore_incompatible=True) for element in group)
    return tuple(simplify(expand(Integer(1) / len(group) * sum(values))) for values in zip(*transformed))


def reynolds_poly(polynomials, coordinates, group):
    if any(_is_matrix(element) for element in group):
        raise NativeUnsupportedError("ReynoldsPoly expects lists of matrix actions for each group element")
    return _reynolds(polynomials, _flatten_coords(coordinates), _elements(group))


def inv_q(association, **_options):
    coordinates = _flatten_coords(association["AmbCoords"])
    equations = tuple(_expression(eq) for eq in association["DefEqs"])
    return all(
        simplify(a - b) == 0
        for element in arrange_gen(association)
        for a, b in zip(_act(equations, coordinates, element), equations)
    )


def inv_mon(association, **_options):
    monomials = tuple(tuple(_expression(x) for x in row) for row in association["MonList"])
    if (prod(map(len, monomials)) > _MAX_INVARIANT_TRIALS
            or sum(map(len, monomials)) > _MAX_INVARIANT_TRIALS):
        raise NativeUnsupportedError("Native invariant basis enumeration exceeds its size bound")
    coordinates = _flatten_coords(association["AmbCoords"])
    group = _elements(association["Group"], exact=True)
    if len(group) * prod(map(len, monomials)) > _MAX_MONOMIALS:
        raise NativeUnsupportedError("Native invariant averaging exceeds its size bound")
    invariants = dict.fromkeys(_reynolds(terms, coordinates, group) for terms in product(*monomials))
    rows = []
    try:
        for invariant in invariants:
            if not any(invariant):
                continue
            coefficients = []
            for polynomial, basis in zip(invariant, monomials):
                poly = Poly(polynomial, *coordinates)
                coefficients.extend(poly.coeff_monomial(monomial) for monomial in basis)
            rows.append(coefficients)
    except PolynomialError as exc:
        raise NativeUnsupportedError("Native InvMon requires polynomial coordinate expressions") from exc
    if not rows:
        return ()
    reduced, _ = ImmutableMatrix(rows).rref()
    result = []
    for i in range(reduced.rows):
        offset = 0
        equation_vector = []
        for basis in monomials:
            equation_vector.append(sum(reduced[i, offset + j] * value for j, value in enumerate(basis)))
            offset += len(basis)
        if any(equation_vector):
            result.append(tuple(equation_vector))
    return tuple(dict.fromkeys(result))


def _coefficients(kind, bounds, length, *prefix):
    if kind not in ("Integer", "Real", "CInteger", "CReal"):
        symbols = IndexedBase(str(kind))
        return tuple(symbols[(*prefix, i)] for i in range(1, length + 1))
    first, last = bounds if _sequence(bounds) else (0, bounds)
    if first > last:
        raise ValueError("CoeffRange must be in increasing order")
    if kind in ("Integer", "CInteger"):
        first, last = _integer(first), _integer(last)
        draw = random.randint
    else:
        draw = random.uniform
    real = tuple(draw(first, last) for _ in range(length))
    if kind in ("CInteger", "CReal"):
        return tuple(value + I * draw(first, last) for value in real)
    return real


def random_poly(multidegree, variables, *, CoeffRange=(1, 100), CoeffType="Integer", **_options):
    monomials = mm_list(multidegree, variables)
    return sum(a * b for a, b in zip(_coefficients(CoeffType, CoeffRange, len(monomials)), monomials))


def generic_def_eqs(association, *, CoeffRange=(1, 100), CoeffType="Integer", **_options):
    return tuple(
        sum(a * _expression(b) for a, b in zip(_coefficients(CoeffType, CoeffRange, len(monomials), equation), monomials))
        for equation, monomials in enumerate(association["MonList"], 1)
    )


def inv_def_eqs(association, *, CoeffRange=(1, 100), CoeffType="Integer", **_options):
    vectors = association["InvMon"]
    if not vectors:
        return 0
    coefficients = _coefficients(CoeffType, CoeffRange, len(vectors))
    return tuple(sum(a * _expression(b) for a, b in zip(coefficients, column)) for column in zip(*vectors, strict=True))


def def_eqs(association, *, Eqs=None, **options):
    if Eqs is not None:
        return tuple(_expression(eq) for eq in Eqs)
    if "InvMon" in association:
        return inv_def_eqs(association, **options)
    return generic_def_eqs(association, **options)


NATIVE_FUNCTIONS = {
    "Abelian": abelian,
    "ArrangeGen": arrange_gen,
    "BlockMatrix": block_matrix,
    "BlockMatrix2": block_matrix2,
    "CIEquiv": ci_equiv,
    "CIEquiv2": ci_equiv2,
    "CINormal": ci_normal,
    "DefEqs": def_eqs,
    "GOrder": g_order,
    "Gen": gen,
    "GenGroup": gen_group,
    "GenOrder": gen_order,
    "GenericDefEqs": generic_def_eqs,
    "InvDefEqs": inv_def_eqs,
    "InvMon": inv_mon,
    "InvQ": inv_q,
    "MD": md,
    "MList": m_list,
    "MMList": mm_list,
    "MMonList": mmon_list,
    "MatNormal": mat_normal,
    "MatProjEquiv": mat_proj_equiv,
    "MatProjTrivial": mat_proj_trivial,
    "PermGroupGen": perm_group_gen,
    "PermMatrix": perm_matrix,
    "ProjAbelian": proj_abelian,
    "ProjGenGroup": proj_gen_group,
    "ProjOrder": proj_order,
    "ProjTrivialGroup": proj_trivial_group,
    "ProjTrivialOrder": proj_trivial_order,
    "RandomPoly": random_poly,
    "ReynoldsPoly": reynolds_poly,
    "SymmMatNormal": symm_mat_normal,
    "SymmMatNormal0": symm_mat_normal0,
    "TransformPoly": transform_poly,
}

NATIVE_PROPERTIES = {
    "Abelian": abelian,
    "DefEqs": def_eqs,
    "Gen": gen,
    "GenOrder": gen_order,
    "Group": gen_group,
    "InvMon": inv_mon,
    "InvQ": inv_q,
    "MonList": mmon_list,
    "Order": g_order,
    "PermGroupGen": perm_group_gen,
    "ProjAbelian": proj_abelian,
    "ProjGroup": proj_gen_group,
    "ProjOrder": proj_order,
    "ProjTrivialGroup": proj_trivial_group,
    "ProjTrivialOrder": proj_trivial_order,
}

NATIVE_MODIFICATIONS = {"CINormal": ci_normal, "CIEquiv": ci_equiv}
