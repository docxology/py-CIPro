"""Small JSON examples for the native CIPro method catalog."""


def _example(*args, **options):
    return {"args": list(args), "options": options}


def _symbol(name):
    return {"$symbol": name}


def _indexed(name, *indices):
    return {"$indexed": [name, *indices]}


def _pow(base, power):
    return {"$pow": [base, power]}


def _add(*terms):
    return {"$add": list(terms)}


def _mul(*factors):
    return {"$mul": list(factors)}


_QUINTIC = {"Conf": [[5]], "DimPs": [4]}
_CURVE = {"Conf": [[2]], "DimPs": [1]}
_CONIC = {"Conf": [[2]], "DimPs": [2]}
_CONIC_EQUATION = _add(*(_pow(_indexed("x", 1, i), 2) for i in range(3)))
_X, _Y = _symbol("a"), _symbol("b")
_J = _indexed("J", 1)
_T = _indexed("t", 1)
_QUINTIC_CHERN = _add(1, _mul(10, _pow(_J, 2)), _mul(-40, _pow(_J, 3)))
_COORDS = [[_X, _Y]]
_I2 = [[1, 0], [0, 1]]
_SWAP = [[0, 1], [1, 0]]
_SIGN = [[-1, 0], [0, 1]]
_GROUP = [[_I2], [_SIGN]]
_SYMMETRY = {
    **_CURVE,
    "Gen": [[_SIGN]],
    "AmbCoords": _COORDS,
    "MonList": [[_pow(_X, 2), _pow(_Y, 2), _mul(_X, _Y)]],
}
_GROUP_DATA = {**_SYMMETRY, "Group": _GROUP, "ProjTrivialGroup": [[_I2]]}
_P1 = {"Conf": [[]], "DimPs": [1], "AmbCoords": _COORDS, "LBS": [[1]]}
_P1_ONE = {
    **_P1,
    "CIDim": 1,
    "AmbDim": 1,
    "CohList": [0],
    "Basis": [_COORDS[0]],
    "CohInfo": [],
    "AmbCohDim": 2,
    "LBSCohDim": 2,
    "Coset": [_I2, [[0], [0]]],
}
_P1_ZERO = {
    **_P1_ONE,
    "LBS": [[0]],
    "Basis": [[1]],
    "AmbCohDim": 1,
    "LBSCohDim": 1,
    "Coset": [[[1]], [[0]]],
}
_P1_IMAGE = {**_P1_ONE, "Coset": [[[1], [0]], [[0], [0]]], "LBSCohDim": 1}
_QUINTIC_LINES = {**_QUINTIC, "LBS": [[-1, 1, 2]]}
_BICUBIC = {"Conf": [[3], [3]], "DimPs": [2, 2]}
_CLASS_DATA = {
    **_QUINTIC,
    "LBS": [[1]],
    "CIDim": 3,
    "ISec": [[[5]]],
    "ChLBSPoly": _add(1, _J, _mul({"$rational": [1, 2]}, _pow(_J, 2)), _mul({"$rational": [1, 6]}, _pow(_J, 3))),
    "CLBSPoly": _add(1, _J),
    "TdPoly": _add(1, _mul({"$rational": [5, 6]}, _pow(_J, 2))),
    "Mu": _mul(5, _J),
}


def _methods(names, example):
    return dict.fromkeys(names.split(), example)


_FUNCTIONS = {
    **_methods(
        "AmbCoords AmbDim CCIPoly CCI ChCIPoly ChCI TdCIPoly TdCI CIDim CYQ DimPs "
        "EulerCI HilbertSeries Intersec IntersecForm KCI Mu CICheck",
        _example(_QUINTIC),
    ),
    **_methods("ArrangeGen Abelian GenOrder GenGroup ProjAbelian PermGroupGen", _example(_SYMMETRY)),
    **_methods("GOrder ProjGenGroup ProjOrder ProjTrivialGroup ProjTrivialOrder", _example(_GROUP_DATA)),
    **_methods("ChLBSPoly ChLBS CLBSPoly CLBS IndLBS", _example(_CLASS_DATA)),
    **_methods("Basis AmbCohDim Coset CohInfo LBSCohDim", _example(_P1_ONE)),
    **_methods("CohList LBSRank", _example(_QUINTIC_LINES)),
    "BlockMatrix": _example([[[1, 2]], [[3], [4]]]),
    "BlockMatrix2": _example([[1, 2]], [[3], [4]]),
    "CIEquiv": _example([_BICUBIC, _BICUBIC]),
    "CIEquiv2": _example({"Conf": [[1, 2], [3, 4]]}, {"Conf": [[4, 3], [2, 1]]}, 2),
    "CIMod": _example(_QUINTIC_LINES, "LBSWedge", TensorPower=2),
    "CINormal": _example({"Conf": [[3, 0], [1, 2]], "DimPs": [4, 2]}),
    "CIProp": _example(_QUINTIC, ["CIDim", "CY", "Euler"]),
    "ChLBPoly": _example([1], 3),
    "Class2Class": _example(_QUINTIC_CHERN, 3, 1, 3),
    "ClassConvert": _example(_QUINTIC_CHERN, [[[5]]], 3, 1),
    "Data": _example("Cicy3", 7890),
    "DefConf": _example({"DimPs": [1]}),
    "DefEqs": _example(_CONIC, Eqs=[_CONIC_EQUATION]),
    "Gen": _example(_CURVE),
    "GenericDefEqs": _example(_SYMMETRY, CoeffRange=[1, 1]),
    "HilbertExpand": _example([1], "t", _pow(_add(1, _mul(-1, _T)), -2), 4),
    "InvDefEqs": _example({"InvMon": [[_pow(_X, 2)], [_pow(_Y, 2)]]}, CoeffRange=[1, 1]),
    "InvMon": _example(_GROUP_DATA),
    "InvQ": _example({**_SYMMETRY, "DefEqs": [_add(_pow(_X, 2), _pow(_Y, 2))]}),
    "LineSymm": _example([[1, 2], [3, 5]], 2),
    "LineTensor": _example([[1, 2], [3, 5]], [[0, 4], [0, 2]]),
    "LineWedge": _example([[1, 2, 3], [3, 5, 6]], 2),
    "MD": _example([[_SWAP], [_SIGN]]),
    "MList": _example(3, [_X, _Y]),
    "MMList": _example([1, 2], [_COORDS[0], [_symbol("u"), _symbol("v")]]),
    "MMonList": _example(_SYMMETRY),
    "MatNormal": _example([[3, 0], [1, 2]]),
    "MatProjEquiv": _example([[4, 0], [0, -3]], _I2, [1, 1]),
    "MatProjTrivial": _example([[2, 0], [0, 2]], [2]),
    "PermMatrix": _example(_SWAP, [1, 1]),
    "RandomPoly": _example([2], _COORDS, CoeffRange=[2, 2]),
    "ReynoldsPoly": _example([_add(_X, _Y)], [_X, _Y], _GROUP),
    "SingularityCheck": _example({**_CONIC, "DefEqs": [_CONIC_EQUATION]}, FieldChar=0),
    "SingularityLocus": _example({**_CONIC, "DefEqs": [_mul(_indexed("x", 1, 0), _indexed("x", 1, 1))]}),
    "SymmMatNormal": _example([[2, 1], [1, 1]]),
    "SymmMatNormal0": _example([[2, 1], [1, 1]]),
    "TransformPoly": _example(_add(_pow(_X, 2), _Y), [_X, _Y], _SWAP),
}

_PROPERTIES = {
    **_methods("AmbDim CIDim CY Mu ISecForm ISec CPoly C ChPoly Ch TdPoly Td Euler K", _example(_QUINTIC, Format="Short")),
    **_methods(
        "GenOrder Abelian ProjAbelian Group Order ProjTrivialGroup ProjTrivialOrder ProjGroup "
        "ProjOrder PermGroupGen InvMon MonList",
        _example({**_CURVE, "Gen": [[_SIGN]]}, Format="Short"),
    ),
    **_methods("LBSRank ChLBSPoly ChLBS CLBSPoly CLBS IndLBS", _example({**_QUINTIC, "LBS": [[1]]}, Format="Short")),
    **_methods("CohList Basis AmbCohDim Coset CohInfo LBSCohDim", _example(_P1, Format="Short")),
    "Conf": _example({"DimPs": [1]}, Format="Short"),
    "DimPs": _example({"Conf": [[3], [3]]}, Format="Short"),
    "AmbCoords": _example(_CONIC, Format="Short"),
    "Gen": _example(_CURVE, Format="Short"),
    "InvQ": _example(
        {**_CURVE, "Gen": [[_SIGN]]},
        Eqs=[_add(*(_pow(_indexed("x", 1, i), 2) for i in range(2)))],
        Format="Short",
    ),
    "DefEqs": _example(_CONIC, Eqs=[_CONIC_EQUATION], Format="Short"),
    "Singular": _example(_CONIC, Eqs=[_CONIC_EQUATION], FieldChar=0, Format="Short"),
    "SingularLocus": _example(_CONIC, Eqs=[_mul(_indexed("x", 1, 0), _indexed("x", 1, 1))], Format="Short"),
    "LBS": _example(_QUINTIC, Format="Short"),
    "HilbertSeries": _example(_QUINTIC, HilbertFormat=4, Format="Short"),
}

_MODIFICATIONS = {
    "CINormal": _example({"Conf": [[3, 0], [1, 2]], "DimPs": [4, 2]}),
    "CIEquiv": _example([_BICUBIC, _BICUBIC]),
    "LBSSum": _example([_P1_ZERO, _P1_ONE]),
    "LBSTensor": _example([_QUINTIC_LINES, {**_QUINTIC, "LBS": [[1]]}]),
    "LBSWedge": _example(_QUINTIC_LINES, TensorPower=2),
    "LBSSymm": _example(_QUINTIC_LINES, TensorPower=2),
    "CohLBS": _example(_QUINTIC_LINES, CohSum=False),
    "DirectSumLBS": _example([_P1_ZERO, _P1_ONE]),
    "KoszulLBS": _example({**_P1, "Conf": [[1, 1]], "LBS": [[4]], "DefEqs": [_X, _Y]}, Ekpq=[1, 2, 0]),
    "MapLBS": _example([_P1_ZERO, _P1_ONE], CoeffRange=[1, 1]),
    "MapSpaceLBS": _example([_P1_ZERO, _P1_ONE], Map=[[_X]], Space="Coker"),
    "QuotientLBS": _example([_P1_ONE, _P1_IMAGE]),
}

for _name, _sample in _MODIFICATIONS.items():
    if _name in _FUNCTIONS:
        continue
    (_geometry,) = _sample["args"]
    _geometries = _geometry if isinstance(_geometry, list) else [_geometry]
    _FUNCTIONS[_name] = _example(_geometries, **_sample["options"])

EXAMPLES = {
    (kind, name): example
    for kind, examples in (("function", _FUNCTIONS), ("property", _PROPERTIES), ("modification", _MODIFICATIONS))
    for name, example in examples.items()
}
