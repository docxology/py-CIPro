"""Compute the counts and exact checks used by the py-CIPro manuscript figures."""

from collections import Counter
from fractions import Fraction
from itertools import accumulate, product
from math import comb
from statistics import median

from py_cipro import CIPro, NativeUnsupportedError
from py_cipro.catalog import MEMBER, get_catalog

from check_intersections import analytic_fixture


def archive_analysis(catalog):
    records = catalog.records
    nonproducts = [row for row in records if not row.product]
    products = [row for row in records if row.product]
    pair_counts = Counter((row.h11, row.h21) for row in nonproducts)
    ranked_pairs = sorted(pair_counts, key=lambda pair: (-pair_counts[pair], pair))
    ranked_counts = [pair_counts[pair] for pair in ranked_pairs]
    nonproduct_eulers = Counter(row.euler for row in nonproducts)
    product_eulers = Counter(row.euler for row in products)
    shapes = Counter((len(row.ambient_dimensions), len(row.configuration[0])) for row in records)
    factor_totals = Counter(len(row.ambient_dimensions) for row in nonproducts)
    factor_favour = Counter(len(row.ambient_dimensions) for row in nonproducts if row.favourable)
    (modal_factors, modal_codimension), modal_count = shapes.most_common(1)[0]
    multiplicity_edges = (1, 2, 5, 10, 25, 50, 100, 200)
    multiplicity_bins = [
        {"min": lower, "max": upper - 1, "pairs": sum(lower <= count < upper for count in ranked_counts)}
        for lower, upper in zip(multiplicity_edges, multiplicity_edges[1:])
    ]
    multiplicity_bins.append({"min": multiplicity_edges[-1], "max": None,
                              "pairs": sum(count >= multiplicity_edges[-1] for count in ranked_counts)})
    return {
        "release": catalog.release,
        "dataset": catalog.dataset,
        "archive_sha256": catalog.sha256,
        "dataset_member": MEMBER,
        "dataset_sha256": catalog.member_sha256,
        "records": len(records),
        "nonproduct_records": len(nonproducts),
        "products": len(products),
        "product_hodge_pairs": sorted({(row.h11, row.h21) for row in products}),
        "nonproduct_hodge_pairs": len(pair_counts),
        "singleton_pairs": multiplicity_bins[0]["pairs"],
        "top10_records": sum(ranked_counts[:10]),
        "top20_records": sum(ranked_counts[:20]),
        "pairs_to_half": next(rank for rank, total in enumerate(accumulate(ranked_counts), start=1)
                              if 2 * total >= len(nonproducts)),
        "favourable_nonproduct_records": sum(factor_favour.values()),
        "favourable_product_records": sum(row.favourable for row in products),
        "nonproduct_zero_euler": nonproduct_eulers[0],
        "product_zero_euler": product_eulers[0],
        "median_euler": int(median(row.euler for row in records)),
        "hodge_euler_identity_matches": sum(row.euler == 2 * (row.h11 - row.h21) for row in records),
        "modal_shape": {"factors": modal_factors, "codimension": modal_codimension, "records": modal_count},
        "hodge_pairs": [{"h11": pair[0], "h21": pair[1], "records": pair_counts[pair]}
                        for pair in ranked_pairs],
        "euler_counts": [{"euler": value, "nonproducts": nonproduct_eulers[value], "products": product_eulers[value]}
                         for value in sorted(nonproduct_eulers.keys() | product_eulers.keys())],
        "shape_counts": [{"factors": factors, "codimension": codimension, "records": count}
                         for (factors, codimension), count in sorted(shapes.items())],
        "favourability": [{"factors": factors, "records": factor_totals[factors],
                          "favourable": factor_favour[factors]} for factors in sorted(factor_totals)],
        "multiplicity_bins": multiplicity_bins,
    }


def _geometry(record, charges):
    return {
        "Conf": record.configuration,
        "DimPs": record.ambient_dimensions,
        "LBS": [[charge] for charge in charges],
    }


def _cohomology(ci, geometry):
    return tuple(row[0] for row in ci.modify(geometry, "CohLBS", CohSum=False))


def _index(h):
    return h[0] - h[1] + h[2] - h[3]


def _quintic(ci, record):
    def sections(k):
        ambient_sections = comb(k + 4, 4) if k >= 0 else 0
        ideal_sections = comb(k - 1, 4) if k >= 5 else 0
        return ambient_sections - ideal_sections

    lower, upper = -10, 10
    checks = []
    for k in range(lower, upper + 1):
        geometry = _geometry(record, (k,))
        native = _cohomology(ci, geometry)
        native_index = ci.property(geometry, "IndLBS", Format="Short")
        expected = (sections(k), 0, 0, sections(-k))
        rr_index = Fraction(5 * k**3 + 25 * k, 6)
        if native != expected or native_index != rr_index or _index(native) != rr_index:
            raise ValueError(f"Quintic cohomology or index mismatch at charge {k}")
        checks.append({"k": k, "dimensions": native, "index": native_index})
    return {
        "record": record.id,
        "charge_range": [lower, upper],
        "points": len(checks),
        "cohomology_matches": len(checks),
        "index_matches": len(checks),
        "rows": checks,
    }


def _bicubic(ci, record):
    lower, upper = -8, 8
    checks = []
    statuses = Counter()
    for a, b in product(range(lower, upper + 1), repeat=2):
        geometry = _geometry(record, (a, b))
        native_index = ci.property(geometry, "IndLBS", Format="Short")
        rr_index = Fraction((3 * a * b + 6) * (a + b), 2)
        if native_index != rr_index:
            raise ValueError(f"Bicubic index mismatch at charges {(a, b)}")
        try:
            dimensions = _cohomology(ci, geometry)
        except NativeUnsupportedError:
            dimensions = None
        if dimensions is None:
            status = "unsupported"
        else:
            if _index(dimensions) != rr_index or dimensions[1] or dimensions[2]:
                raise ValueError(f"Bicubic cohomology mismatch at charges {(a, b)}")
            status = "h0_only" if dimensions[0] else "h3_only" if dimensions[3] else "acyclic"
        statuses[status] += 1
        checks.append({"a": a, "b": b, "status": status, "dimensions": dimensions, "index": native_index})
    by_charge = {(row["a"], row["b"]): row["dimensions"] for row in checks}
    dual_matches = 0
    for (a, b), dimensions in by_charge.items():
        dual = by_charge[-a, -b]
        if (dimensions is None) != (dual is None) or dimensions is not None and dimensions != dual[::-1]:
            raise ValueError(f"Bicubic Serre duality mismatch at charges {(a, b)}")
        dual_matches += dimensions is not None
    return {
        "record": record.id,
        "charge_range_per_axis": [lower, upper],
        "points": len(checks),
        "supported": dual_matches,
        **dict(sorted(statuses.items())),
        "index_matches": len(checks),
        "supported_index_and_duality_matches": dual_matches,
        "rows": checks,
    }


def manuscript_analysis():
    catalog = get_catalog()
    with CIPro(backend="python") as ci:
        fixtures = {}
        for name, number in (("quintic", 7890), ("bicubic", 7884), ("tetraquadric", 7862)):
            record = catalog.record(number)
            analytic = analytic_fixture(record)
            geometry = _geometry(record, (0,) * len(record.ambient_dimensions))
            native_euler = ci.property(geometry, "Euler", Format="Short")
            if native_euler != analytic["euler"]:
                raise ValueError(f"Euler disagrees with exact ambient calculation for {name}")
            fixtures[name] = {**analytic, "native_euler": native_euler}
        cohomology = {
            "quintic": _quintic(ci, catalog.record(7890)),
            "bicubic": _bicubic(ci, catalog.record(7884)),
        }
    return {"schema_version": 1, "catalog": archive_analysis(catalog),
            "fixtures": fixtures, "cohomology": cohomology}
