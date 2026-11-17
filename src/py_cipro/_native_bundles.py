"""Exact line-bundle and ambient cohomology operations in CIPro conventions."""

from collections.abc import Mapping, Sequence
from fractions import Fraction
from itertools import combinations, combinations_with_replacement, permutations, product
from math import comb, factorial, prod

import sympy as sp

from ._native_errors import NativeUnsupportedError
from ._native_geometry import class_convert, class_to_class, kahler_basis
from ._native_symmetry import random_poly


def _sequence(value):
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _matrix(value, key):
    if not _sequence(value) or any(not _sequence(row) for row in value):
        raise NativeUnsupportedError(f"{key} requires a matrix of Python sequences.")
    rows = tuple(tuple(row) for row in value)
    if rows and any(len(row) != len(rows[0]) for row in rows):
        raise ValueError(f"{key} must be rectangular.")
    return rows


def _exact(value):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction, sp.Expr)) or (
        isinstance(value, sp.Expr) and value.has(sp.Float)
    ):
        raise NativeUnsupportedError("Use exact integer, rational or SymPy coefficients in Python.")
    return value


def _integer(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, sp.Integer)):
        raise NativeUnsupportedError(f"{name} requires exact integer values in Python.")
    return int(value)


def _dimensions(geometry):
    dims = tuple(_integer(n, "DimPs") for n in geometry["DimPs"])
    if not dims or min(dims) < 1:
        raise NativeUnsupportedError("Python line-bundle geometry requires positive ambient dimensions.")
    return dims


def _charge_matrix(value):
    return tuple(tuple(_exact(x) for x in row) for row in _matrix(value, "LBS"))


def _integer_charges(value):
    return tuple(tuple(_integer(x, "LBS") for x in row) for row in _matrix(value, "LBS"))


def _columns(rows):
    return tuple(zip(*rows))


def _sum_columns(columns):
    return tuple(map(sum, zip(*columns)))


def line_tensor(first, second, /):
    """Tensor two sums with column order given by the Cartesian product."""
    left, right = _charge_matrix(first), _charge_matrix(second)
    if len(left) != len(right):
        raise ValueError("LineTensor inputs must have the same number of ambient factors.")
    return _columns(tuple(_sum_columns(pair) for pair in product(_columns(left), _columns(right))))


def _power_columns(rows, power, choose):
    return _columns(tuple(_sum_columns(group) for group in choose(_columns(rows), power)))


def line_wedge(line, power, /):
    """Exterior power, including the released helper's zero-column-charge convention."""
    rows = _charge_matrix(line)
    power = _integer(power, "LineWedge power")
    if power < 0:
        raise ValueError("LineWedge power must be nonnegative.")
    if power == 0 or power > len(_columns(rows)):
        return ((0,),) * len(rows)
    return _power_columns(rows, power, combinations)


def line_symm(line, power, /):
    """Symmetric power, ordered by nondecreasing tuples of summand indices."""
    rows = _charge_matrix(line)
    power = _integer(power, "LineSymm power")
    if power < 0:
        raise ValueError("LineSymm power must be nonnegative.")
    if power == 0:
        return ((0,),) * len(rows)
    return _power_columns(rows, power, combinations_with_replacement)


def default_lbs(geometry, /, **_options):
    if "DimPs" in geometry:
        dimensions = len(geometry["DimPs"])
    elif "Conf" in geometry:
        dimensions = len(geometry["Conf"])
    else:
        dimensions = 1
    return ((0,),) * dimensions


def lbs_rank(geometry, /, **_options):
    rows = _matrix(geometry["LBS"], "LBS")
    return len(rows[0]) if rows else 0


def _association_list(value):
    if isinstance(value, Mapping):
        return (value,)
    if not _sequence(value) or not value or any(not isinstance(item, Mapping) for item in value):
        raise ValueError("Supply a geometry association or a nonempty sequence of associations.")
    return tuple(value)


def _compatible_bundles(value):
    geos = _association_list(value)
    first = geos[0]
    conf = _matrix(first["Conf"], "Conf")
    dims = tuple(first["DimPs"])
    for geometry in geos:
        if conf != _matrix(geometry["Conf"], "Conf") or dims != tuple(geometry["DimPs"]):
            raise NativeUnsupportedError("Python bundle operations require identical underlying CI configurations.")
        if len(geometry["LBS"]) != len(dims):
            raise ValueError("LBS must have one row per ambient factor.")
    return geos, conf, dims


def lbs_sum(geometries, /, **_options):
    geos, conf, dims = _compatible_bundles(geometries)
    columns = tuple(column for geometry in geos for column in _columns(_charge_matrix(geometry["LBS"])))
    return {"Conf": conf, "DimPs": dims, "LBS": _columns(columns)}


def lbs_tensor(geometries, /, **_options):
    geos, conf, dims = _compatible_bundles(geometries)
    columns = product(*(_columns(_charge_matrix(geometry["LBS"])) for geometry in geos))
    return {"Conf": conf, "DimPs": dims, "LBS": _columns(tuple(map(_sum_columns, columns)))}


def _rounded_power(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Fraction, sp.Rational)):
        raise NativeUnsupportedError("TensorPower in Python requires a finite real scalar.")
    try:
        return max(0, round(value))
    except (ValueError, OverflowError) as exc:
        raise ValueError("TensorPower must be finite.") from exc


def lbs_wedge(geometries, /, *, TensorPower=2, **_options):
    geometry = _association_list(geometries)[0]
    rows = _charge_matrix(geometry["LBS"])
    power = _rounded_power(TensorPower)
    result = ((),) * len(rows) if power == 0 or power > lbs_rank(geometry) else _power_columns(rows, power, combinations)
    return {**geometry, "LBS": result}


def lbs_symm(geometries, /, *, TensorPower=2, **_options):
    geometry = _association_list(geometries)[0]
    rows = _charge_matrix(geometry["LBS"])
    power = _rounded_power(TensorPower)
    result = ((),) * len(rows) if power == 0 else _power_columns(rows, power, combinations_with_replacement)
    return {**geometry, "LBS": result}


def _degree_cap(dimension):
    if isinstance(dimension, bool) or not isinstance(dimension, (int, Fraction, sp.Rational)):
        raise NativeUnsupportedError("The Python Chern character needs an exact numeric CI dimension.")
    if dimension < 0:
        raise ValueError("The CI dimension must be nonnegative.")
    capped = sp.Rational(min(dimension, 5))
    return int(capped) if capped.is_Integer else 5


def line_chern_character(charge, dimension, /):
    if not _sequence(charge):
        raise NativeUnsupportedError("Supply a Python sequence of line-bundle charges.")
    first = sum(_exact(coeff) * variable for coeff, variable in zip(charge, kahler_basis(len(charge))))
    return sp.expand(sum(first**degree / sp.Integer(factorial(degree)) for degree in range(_degree_cap(dimension) + 1)))


def bundle_chern_character_poly(geometry, /, **_options):
    return sp.expand(sum(line_chern_character(column, geometry["CIDim"]) for column in _columns(_charge_matrix(geometry["LBS"]))))


def bundle_chern_character(geometry, /, **_options):
    return class_convert(geometry["ChLBSPoly"], geometry["ISec"], geometry["CIDim"], len(geometry["Conf"]))


def bundle_chern_poly(geometry, /, **_options):
    _dimensions(geometry)
    return class_to_class(geometry["ChLBSPoly"], geometry["CIDim"], len(geometry["Conf"]), geometry["CIDim"], "Ch", "C")


def bundle_chern(geometry, /, **_options):
    return class_convert(geometry["CLBSPoly"], geometry["ISec"], geometry["CIDim"], len(geometry["Conf"]))


def bundle_index(geometry, /, **_options):
    dims = _dimensions(geometry)
    variables = kahler_basis(len(dims))
    expression = sp.expand(geometry["TdPoly"] * geometry["ChLBSPoly"] * geometry["Mu"])
    result = sp.Poly(expression, *variables).coeff_monomial(dims)
    if result.is_Integer:
        return int(result)
    if result.is_Rational:
        return Fraction(int(result.p), int(result.q))
    return result


def coh_list(geometry, /, *, CohQ=0, **_options):
    rank = lbs_rank(geometry)
    if _sequence(CohQ):
        if len(CohQ) != rank:
            raise ValueError("Supply one cohomology degree per line-bundle summand.")
        return tuple(_integer(q, "CohQ") for q in CohQ)
    return (_integer(CohQ, "CohQ"),) * rank


def _compositions(total, length, *, reverse=False):
    if length == 1:
        yield (total,)
        return
    values = range(total, -1, -1) if reverse else range(total + 1)
    for first in values:
        for rest in _compositions(total - first, length - 1, reverse=reverse):
            yield first, *rest


def _bott_space(dims, charge):
    if any(-dimension <= k < 0 for dimension, k in zip(dims, charge)):
        return None, 0
    degree = sum(dimension for dimension, k in zip(dims, charge) if k < 0)
    rank = prod(comb(k + dimension, dimension) if k >= 0 else comb(-k - 1, dimension) for dimension, k in zip(dims, charge))
    return degree, rank


def _ambient_coordinates(geometry, dims):
    coords = geometry["AmbCoords"]
    if not _sequence(coords) or len(coords) != len(dims) or any(
        not _sequence(level) or len(level) != dim + 1 for level, dim in zip(coords, dims)
    ):
        raise ValueError("AmbCoords must have n + 1 coordinates per P^n factor.")
    return tuple(tuple(_exact(coord) for coord in level) for level in coords)


def _bott_basis(dims, charge, q, coords):
    degree, rank = _bott_space(dims, charge)
    if not rank or q != degree:
        return ()
    factors = []
    for dimension, k, variables in zip(dims, charge, coords):
        exponent_vectors = (
            _compositions(k, dimension + 1, reverse=True)
            if k >= 0 else
            (tuple(-part - 1 for part in vector) for vector in _compositions(-k - dimension - 1, dimension + 1))
        )
        factors.append(tuple(sp.prod(variable**power for variable, power in zip(variables, vector)) for vector in exponent_vectors))
    return tuple(sp.prod(terms) for terms in product(*factors))


def ambient_basis(geometry, /, **_options):
    dims = _dimensions(geometry)
    rows = _integer_charges(geometry["LBS"])
    if len(rows) != len(dims):
        raise ValueError("LBS must have one row per ambient factor.")
    charge_columns = _columns(rows)
    q = coh_list(geometry, CohQ=geometry["CohList"])
    coords = _ambient_coordinates(geometry, dims)
    return tuple(_bott_basis(dims, charge, degree, coords) for charge, degree in zip(charge_columns, q))


def ambient_coh_dim(geometry, /, **_options):
    return sum(map(len, geometry["Basis"]))


def coh_coset(geometry, /, **_options):
    dim = _integer(geometry["AmbCohDim"], "AmbCohDim")
    if dim <= 0:
        return (), ()
    identity = tuple(tuple(int(i == j) for j in range(dim)) for i in range(dim))
    return identity, ((0,),) * dim


def coh_info(_geometry, /, *, CohInfo=(), **_options):
    return tuple(CohInfo) if _sequence(CohInfo) else CohInfo


def _modular_rank(matrix, modulus):
    data = []
    for row in matrix:
        converted = []
        for coefficient in row:
            exact = sp.sympify(_exact(coefficient))
            if not exact.is_Rational:
                raise NativeUnsupportedError("Prime-modulus rank requires rational coefficients in Python.")
            denominator = int(exact.q)
            if denominator % modulus == 0:
                raise ValueError("A coefficient denominator is zero in the requested finite field.")
            converted.append(int(exact.p) * pow(denominator, -1, modulus) % modulus)
        data.append(converted)
    rank = 0
    for column in range(len(matrix[0])):
        pivot = next((i for i in range(rank, len(data)) if data[i][column]), None)
        if pivot is None:
            continue
        data[rank], data[pivot] = data[pivot], data[rank]
        head = data[rank]
        inverse = pow(head[column], -1, modulus)
        for i in range(rank + 1, len(data)):
            scale = data[i][column] * inverse
            data[i] = [(value - scale * base) % modulus for value, base in zip(data[i], head)]
        rank += 1
    return rank


def _matrix_rank(matrix, modulus):
    if not matrix or not matrix[0]:
        return 0
    if modulus:
        return _modular_rank(matrix, modulus)
    return sp.Matrix(tuple(tuple(_exact(value) for value in row) for row in matrix)).rank()


def lbs_coh_dim(geometry, /, *, Modulus=0, **_options):
    a, b = (_matrix(m, "Coset") for m in geometry["Coset"])
    if not a or not b:
        return 0
    modulus = _integer(Modulus, "Modulus")
    if modulus != 0 and not sp.isprime(modulus):
        raise NativeUnsupportedError("In Python, coset rank supports characteristic zero or a prime modulus.")
    return _matrix_rank(a, modulus) - _matrix_rank(b, modulus)


def _block_diagonal(matrices):
    before = 0
    total = sum(len(matrix[0]) for matrix in matrices if matrix)
    result = []
    for matrix in matrices:
        if matrix:
            width = len(matrix[0])
            result.extend((0,) * before + row + (0,) * (total - before - width) for row in matrix)
            before += width
    return tuple(result)


def direct_sum_lbs(value, /, *, CicyMeth="NoCount", **options):
    geos = _association_list(value)
    if CicyMeth not in {"NoCount", "Count"}:
        raise NativeUnsupportedError("DirectSumLBS supports CicyMeth='NoCount' or 'Count' in Python.")
    prepared = []
    for i, geometry in enumerate(geos, start=1):
        dim = geometry["LBSCohDim"] if "LBSCohDim" in geometry else lbs_coh_dim(geometry, **options)
        info = tuple(geometry["CohInfo"])
        if CicyMeth == "Count":
            info = tuple(i if label is None else (i, label) for label in info)
        prepared.append({**geometry, "LBSCohDim": dim, "CohInfo": info})
    chosen = [geometry for geometry in prepared if geometry["LBSCohDim"] > 0] or prepared[:1]
    first = chosen[0]
    a, b = zip(*(tuple(_matrix(m, "Coset") for m in geometry["Coset"]) for geometry in chosen))
    return {
        "DimPs": first["DimPs"], "LBS": _columns(tuple(column for geometry in chosen for column in _columns(_charge_matrix(geometry["LBS"])))),
        "AmbCoords": first["AmbCoords"], "AmbCohdim": sum(geometry["AmbCohDim"] for geometry in chosen),
        "CohList": tuple(q for geometry in chosen for q in geometry["CohList"]),
        "Basis": tuple(item for geometry in chosen for item in geometry["Basis"]),
        "Coset": (_block_diagonal(a), _block_diagonal(b)),
        "LBSCohDim": sum(geometry["LBSCohDim"] for geometry in chosen),
        "CohInfo": tuple(label for geometry in chosen for label in geometry["CohInfo"]),
    }


def _ci_bundle(geometries):
    geometry = _association_list(geometries)[0]
    dims = _dimensions(geometry)
    config = _matrix(geometry["Conf"], "Conf")
    charges = _integer_charges(geometry["LBS"])
    if len(config) != len(dims) or len(charges) != len(dims):
        raise ValueError("Conf and LBS must have one row per ambient factor.")
    degrees = tuple(tuple(_integer(value, "Conf") for value in col) for col in _columns(config))
    lines = _columns(charges)
    if not lines or any(min(column) < 0 or not any(column) for column in degrees):
        raise NativeUnsupportedError("Python requires a nonzero bundle rank and nonnegative nonconstant defining multidegrees.")
    return geometry, dims, degrees, lines


def _koszul_twists(charge, degrees):
    for size in range(len(degrees) + 1):
        for subset in combinations(degrees, size):
            yield (-1)**size, tuple(k - sum(col[i] for col in subset) for i, k in enumerate(charge))


def _one_projective_dimensions(ambient_dim, degrees, charge):
    dim = ambient_dim - len(degrees)
    if dim == 0:
        return (prod(d for (d,) in degrees),)

    def sections(k):
        return sum(sign * comb(twist + ambient_dim, ambient_dim)
                   for sign, (twist,) in _koszul_twists((k,), degrees) if twist >= 0)

    canonical_degree = sum(d for (d,) in degrees) - ambient_dim - 1
    return (sections(charge), *(0,) * (dim - 1), sections(canonical_degree - charge))


def _ci_line_dimensions(dims, degrees, charge):
    dim = sum(dims) - len(degrees)
    if not degrees:
        q, rank = _bott_space(dims, charge)
        return tuple(rank if i == q else 0 for i in range(dim + 1))
    if len(dims) == 1:
        return _one_projective_dimensions(dims[0], degrees, charge[0])

    # If every Koszul sheaf has only H^0, the total complex has no higher H^q.
    def sections(k):
        total = 0
        for sign, twist in _koszul_twists(k, degrees):
            q, rank = _bott_space(dims, twist)
            if rank and q != 0:
                return None
            total += sign * rank
        return total

    h0 = sections(charge)
    if h0 is not None:
        return (h0, *(0,) * dim)
    canonical = tuple(sum(column[i] for column in degrees) - n - 1 for i, n in enumerate(dims))
    h0_dual = sections(tuple(k - l for k, l in zip(canonical, charge)))
    if h0_dual is None:
        raise NativeUnsupportedError("This multiprojective CohLBS case needs the Wolfram spectral-sequence maps.")
    return (*(0,) * dim, h0_dual)


def coh_lbs(geometries, /, *, CohFormat="Dim", CohSum=True, CohProt=False, Modulus=0, **_options):
    """Calculate exact dimension tables in the supported Bott and Koszul cases."""
    if CohFormat != "Dim" or CohProt is not False or type(CohSum) is not bool or Modulus != 0:
        raise NativeUnsupportedError("Python CohLBS supports dimension output, without a protocol or modular ranks.")
    geometry, dims, degrees, lines = _ci_bundle(geometries)
    if len(degrees) > sum(dims):
        raise NativeUnsupportedError("Python CohLBS requires a nonnegative expected CI dimension.")
    if degrees and "DefEqs" in geometry:
        equations = geometry["DefEqs"]
        if not _sequence(equations) or len(equations) != len(degrees) or not all(sp.expand(_exact(eq)) != 0 for eq in equations):
            raise NativeUnsupportedError("Python CohLBS assumes nonzero equations defining a regular complete intersection.")
    values = tuple(zip(*(_ci_line_dimensions(dims, degrees, line) for line in lines)))
    return tuple((sum(row),) for row in values) if CohSum else values


def _signature(indices):
    return (-1)**sum(a > b for a, b in combinations(indices, 2))


def map_lbs(geometries, /, **options):
    """Draw a map from the given source to target line-bundle sums."""
    pair = _association_list(geometries)
    if len(pair) != 2:
        raise ValueError("MapLBS needs a source and target association.")
    source, target = pair
    left, right = _integer_charges(source["LBS"]), _integer_charges(target["LBS"])
    coords = tuple(tuple(level) for level in source["AmbCoords"])
    if len(left) != len(right) or len(left) != len(coords):
        raise ValueError("MapLBS line-bundle charges and coordinates must cover the same factors.")
    return tuple(tuple(random_poly(tuple(a - b for a, b in zip(outgoing, incoming)), coords, **options)
                       for incoming in _columns(left)) for outgoing in _columns(right))


def _rational_monomial(term, variables):
    coefficient, monomial = sp.sympify(_exact(term)).as_coeff_Mul(rational=True)
    powers = {} if monomial == 1 else monomial.as_powers_dict()
    if not coefficient.is_Rational or any(base not in variables or not value.is_Integer for base, value in powers.items()):
        raise NativeUnsupportedError("Prepared BBW calculations require rational coordinate monomials.")
    return coefficient, tuple(int(powers.get(variable, 0)) for variable in variables)


def _bbw_basis(geometry, variables, rank):
    if len(geometry["Basis"]) != rank:
        raise ValueError("A prepared Basis must have one list of monomials per line-bundle summand.")
    offset = 0
    result = []
    for terms in geometry["Basis"]:
        vectors = []
        for term in terms:
            coefficient, exponent = _rational_monomial(term, variables)
            if coefficient != 1:
                raise NativeUnsupportedError("Prepared BBW bases require monic Laurent monomials.")
            vectors.append(exponent)
        if len(vectors) != len(set(vectors)):
            raise ValueError("A prepared BBW summand cannot have duplicate basis monomials.")
        result.append((offset, tuple(vectors)))
        offset += len(vectors)
    if offset != geometry["AmbCohDim"]:
        raise ValueError("Prepared Basis and AmbCohDim disagree.")
    return result


def _ambient_bbw_map(source, target, polys):
    dims = _dimensions(source)
    coords = _ambient_coordinates(source, dims)
    if dims != _dimensions(target) or coords != _ambient_coordinates(target, dims):
        raise NativeUnsupportedError("Prepared BBW maps need the same ambient coordinates on source and target.")
    variables = tuple(x for level in coords for x in level)
    if len(set(variables)) != len(variables) or any(not isinstance(x, (sp.Symbol, sp.Indexed)) for x in variables):
        raise NativeUnsupportedError("Prepared BBW maps need distinct SymPy coordinate symbols.")
    left = _columns(_integer_charges(source["LBS"]))
    right = _columns(_integer_charges(target["LBS"]))
    if any(len(charge) != len(dims) for charge in (*left, *right)):
        raise ValueError("Map line-bundle charges and ambient factors must agree.")
    matrix = _matrix(polys, "Map")
    if len(matrix) != len(right) or any(len(row) != len(left) for row in matrix):
        raise ValueError("Map shape must be target bundle rank by source bundle rank.")
    inputs = _bbw_basis(source, variables, len(left))
    outputs = _bbw_basis(target, variables, len(right))
    result = sp.zeros(target["AmbCohDim"], source["AmbCohDim"])
    variable_positions = {x: i for i, x in enumerate(variables)}
    groups = tuple(tuple(variable_positions[x] for x in level) for level in coords)
    for i, (offset_out, out_vectors) in enumerate(outputs):
        positions = {powers: index for index, powers in enumerate(out_vectors, start=offset_out)}
        for j, (offset_in, in_vectors) in enumerate(inputs):
            degree = tuple(out - incoming for out, incoming in zip(right[i], left[j]))
            terms = [term for term in sp.Add.make_args(sp.expand(_exact(matrix[i][j]))) if term != 0]
            for term in terms:
                coefficient, powers = _rational_monomial(term, variables)
                if any(k < 0 for k in powers) or tuple(sum(powers[pos] for pos in group) for group in groups) != degree:
                    raise NativeUnsupportedError("Map entries must be polynomial and have the prescribed multidegree.")
                for column, vector in enumerate(in_vectors, start=offset_in):
                    row = positions.get(tuple(a + b for a, b in zip(vector, powers)))
                    if row is not None:
                        result[row, column] += coefficient
    return result


def _bbw_coset(geometry):
    size = geometry["AmbCohDim"]
    matrices = tuple(_matrix(item, "Coset") for item in geometry["Coset"])
    if size == 0 and matrices == ((), ()):
        return sp.zeros(0, 0), sp.zeros(0, 0)
    if len(matrices) != 2 or any(len(item) != size for item in matrices):
        raise ValueError("Prepared Coset matrices must have AmbCohDim rows.")
    converted = tuple(sp.Matrix(tuple(tuple(_exact(value) for value in row) for row in item)) for item in matrices)
    if any(any(not value.is_Rational for value in item) for item in converted):
        raise NativeUnsupportedError("Prepared Coset matrices require rational coefficients.")
    return converted


def _reduced_columns(matrix):
    reduced, _ = matrix.T.rref()
    basis = [row for row in reduced.tolist() if any(row)]
    return sp.Matrix(basis).T if basis else sp.zeros(matrix.rows, 1)


def _projected_nullspace(matrix, rows):
    basis = matrix.nullspace()
    if basis:
        return sp.Matrix.hstack(*(vector[:rows, :] for vector in basis))
    return None


def _tuple_matrix(matrix):
    return tuple(map(tuple, matrix.tolist()))


def _bbw_result(geometry, numerator, denominator, *, modification):
    fields = ("DimPs", "LBS", "AmbCoords", "CohList", "Basis", "CohInfo")
    result = {key: geometry[key] for key in fields}
    if modification == "MapSpaceLBS":
        result.update({key: geometry[key] for key in ("Conf", "AmbDim", "CIDim", "AmbCohDim")})
    else:
        result["AmbCohdim"] = geometry["AmbCohDim"]
    result["Coset"] = _tuple_matrix(numerator), _tuple_matrix(denominator)
    result["LBSCohDim"] = numerator.rank() - denominator.rank()
    return result


def _bbw_map_space(source, target, polys, space, check, modification):
    mapping = _ambient_bbw_map(source, target, polys)
    a, b = _bbw_coset(source)
    at, bt = _bbw_coset(target)
    if mapping.rows == 0 or mapping.cols == 0:
        if space == "Ker":
            return _bbw_result(source, a, b, modification=modification)
        if space == "Im":
            return _bbw_result(target, sp.zeros(0, 0), sp.zeros(0, 0), modification=modification)
        return _bbw_result(target, at, bt, modification=modification)

    ma = mapping * a
    if check and (ma.row_join(at).rank() != at.rank() or (mapping * b).row_join(bt).rank() != bt.rank()):
        raise ValueError("The map does not preserve the prepared source and target cosets.")
    if space == "Ker":
        projected = _projected_nullspace(ma.row_join(bt), a.cols)
        if projected is None:
            zero = sp.zeros(a.rows, 1)
            return _bbw_result(source, zero, zero, modification=modification)
        return _bbw_result(source, a * projected, b, modification=modification)
    if space == "Im":
        projected = _projected_nullspace(bt.row_join(ma), bt.cols)
        common = sp.zeros(bt.rows, 1) if projected is None else bt * projected
        return _bbw_result(target, _reduced_columns(ma), _reduced_columns(common), modification=modification)
    return _bbw_result(target, at, _reduced_columns(ma.row_join(bt)), modification=modification)


def _bbw_options(options):
    if options.get("Modulus", 0) != 0 or options.get("Numerical", False) or options.get("Meth", "expand") != "expand":
        raise NativeUnsupportedError("Prepared BBW map spaces support exact characteristic-zero expansion in Python.")


def map_space_lbs(geometries, /, *, Map=None, Space="Ker", CicyMeth="Check", **options):
    """Kernel, image, or cokernel of a map between prepared exact BBW cosets."""
    _bbw_options(options)
    if Space not in ("Ker", "Im", "Coker"):
        raise NativeUnsupportedError("Python MapSpaceLBS supports Space='Ker', 'Im', or 'Coker'.")
    if "OutFormat" in options and options["OutFormat"] != Space:
        raise NativeUnsupportedError("Use Space to select the Python map result.")
    source, target = _association_list(geometries)
    polys = map_lbs((source, target), **options) if Map is None else Map
    return _bbw_map_space(source, target, polys, Space, CicyMeth == "Check", "MapSpaceLBS")


def quotient_lbs(geometries, /, **options):
    """Form the released quotient by the identity map from the second coset into the first."""
    _bbw_options(options)
    target, source = _association_list(geometries)
    rank = lbs_rank(target)
    identity = tuple(tuple(int(i == j) for j in range(rank)) for i in range(rank))
    return _bbw_map_space(source, target, identity, "Coker", False, "QuotientLBS")


def koszul_lbs(geometries, /, *, Ekpq=(0, 0, 0), **_options):
    """Calculate the released Koszul map with explicitly supplied equations."""
    geometry, dims, degrees, lines = _ci_bundle(geometries)
    k, p, q = tuple(_integer(value, "Ekpq") for value in Ekpq)
    if not 0 <= k <= p <= len(degrees) or not 0 <= q <= sum(dims):
        raise NativeUnsupportedError("Python KoszulLBS supports 0 ≤ k ≤ p ≤ codimension and ambient q.")
    coordinates = _ambient_coordinates(geometry, dims)
    equations = tuple(sp.expand(_exact(eq)) for eq in geometry["DefEqs"])
    if len(equations) != len(degrees):
        raise ValueError("DefEqs must contain one polynomial per configuration column.")
    charge = lines[0]
    indices = range(len(degrees))
    targets = tuple(combinations(indices, p - k))
    sources = tuple(combinations(indices, p))

    def entry(target, source):
        if any(index not in source for index in target):
            return 0
        removed = tuple(index for index in source if index not in target)
        sign = _signature((*target, *removed))
        crossing = [i for i, a in enumerate(charge)
                    if a - sum(degrees[j][i] for j in source) < 0 <= a - sum(degrees[j][i] for j in target)]
        if not crossing:
            return sign * sp.prod(equations[index] for index in removed)

        linear = {i: tuple(j for j in removed if degrees[j][i] == 1) for i in crossing}
        if any(len(linear[i]) != dims[i] + 1 or any(degrees[j][i] not in (0, 1) for j in removed) for i in crossing):
            return 0
        factors = {j: tuple(i for i in crossing if j in linear[i]) for j in removed}
        spectators = tuple(j for j in removed if not factors[j])
        contributors = tuple(j for j in removed if factors[j])
        prefactor = sign * sp.prod(equations[j] for j in spectators) * sp.prod(x for i in crossing for x in coordinates[i])
        total = 0
        for permutations_by_factor in product(*(permutations(range(dims[i] + 1)) for i in crossing)):
            by_factor = dict(zip(crossing, permutations_by_factor))
            coordinate = {(i, j): coordinates[i][idx] for i in crossing for j, idx in zip(linear[i], by_factor[i])}
            coefficient = sp.prod(equations[j].coeff(sp.prod(coordinate[i, j] for i in factors[j])) for j in contributors)
            total += coefficient * prod(_signature(permutation) for permutation in permutations_by_factor)
        return prefactor * total

    return tuple(tuple(entry(target, source) for source in sources) for target in targets)


NATIVE_FUNCTIONS = {
    "LineTensor": line_tensor, "LineWedge": line_wedge, "LineSymm": line_symm,
    "LBSRank": lbs_rank, "ChLBPoly": line_chern_character, "ChLBSPoly": bundle_chern_character_poly,
    "ChLBS": bundle_chern_character, "CLBSPoly": bundle_chern_poly, "CLBS": bundle_chern, "IndLBS": bundle_index,
    "LBSSum": lbs_sum, "LBSTensor": lbs_tensor, "LBSWedge": lbs_wedge, "LBSSymm": lbs_symm,
    "CohList": coh_list, "Basis": ambient_basis, "AmbCohDim": ambient_coh_dim, "Coset": coh_coset,
    "CohInfo": coh_info, "LBSCohDim": lbs_coh_dim, "DirectSumLBS": direct_sum_lbs,
    "CohLBS": coh_lbs, "KoszulLBS": koszul_lbs, "MapLBS": map_lbs,
    "MapSpaceLBS": map_space_lbs, "QuotientLBS": quotient_lbs,
}

NATIVE_PROPERTIES = {
    "LBS": default_lbs, "LBSRank": lbs_rank, "ChLBSPoly": bundle_chern_character_poly,
    "ChLBS": bundle_chern_character, "CLBSPoly": bundle_chern_poly, "CLBS": bundle_chern, "IndLBS": bundle_index,
    "CohList": coh_list, "Basis": ambient_basis, "AmbCohDim": ambient_coh_dim, "Coset": coh_coset,
    "CohInfo": coh_info, "LBSCohDim": lbs_coh_dim,
}

NATIVE_MODIFICATIONS = {
    "LBSSum": lbs_sum, "LBSTensor": lbs_tensor, "LBSWedge": lbs_wedge, "LBSSymm": lbs_symm,
    "DirectSumLBS": direct_sum_lbs, "CohLBS": coh_lbs, "KoszulLBS": koszul_lbs, "MapLBS": map_lbs,
    "MapSpaceLBS": map_space_lbs, "QuotientLBS": quotient_lbs,
}

NATIVE_MOD_DEPENDENCY_OVERRIDES = {"CohLBS": ("Conf", "DimPs", "LBS")}
