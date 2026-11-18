#!/usr/bin/env python3
"""Audit four integral divisibilities on the supplied CICY3 ambient lattices."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path

from py_cipro._research_cubic import SIGNATURE_KEYS as INVARIANTS, _record_signature
from py_cipro.catalog import _cicy3_source_rows, get_catalog


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "integral-invariants.json"
WITNESS_IDS = (7702, 7741)
DIAGONAL_WITNESS_IDS = (6177, 6232)


def evaluated_contents(tensor, rank):
    """Check the coefficient formulas by evaluating on signed sums of generators."""
    def evaluate(x, y, z):
        return sum(
            a * b * c * tensor[tuple(sorted((i, j, k)))]
            for (i, a), (j, b), (k, c) in product(x, y, z)
        )

    units = [((i, 1),) for i in range(rank)]
    pairs = list(combinations(range(rank), 2))
    squares = [*units, *(((i, 1), (j, 1)) for i, j in pairs)]
    cubes = [*squares]
    cubes.extend(((i, 1), (j, -1)) for i, j in pairs)
    cubes.extend(u + v + w for u, v, w in combinations(units, 3))
    return (
        gcd(*(evaluate(x, x, y) for x, y in product(squares, units))),
        gcd(*(evaluate(x, x, x) for x in cubes)),
    )


def witness_record(record, row, tensor, c2):
    rank = len(record.ambient_dimensions)
    diagonals = [tensor[i, i, i] for i in range(rank)]
    odd_repeated_triples = [
        {"indices": [i + 1, i + 1, j + 1], "value": value}
        for i, j in product(range(rank), repeat=2)
        if (value := tensor[tuple(sorted((i, i, j)))]) % 2
    ]
    joint_cube_values = [
        {
            "generators": [i + 1, j + 1],
            "value": diagonals[i] + diagonals[j] + 3 * (tensor[i, i, j] + tensor[i, j, j]),
        }
        for i, j in combinations(range(rank), 2)
    ]
    return {
        **row,
        "hodge": [record.h11, record.h21],
        "euler": record.euler,
        "ambient_dimensions": list(record.ambient_dimensions),
        "configuration": [list(degrees) for degrees in record.configuration],
        "favourable": record.favourable,
        "c2": c2,
        "odd_repeated_triples": odd_repeated_triples,
        "basis_cube_values": diagonals,
        "pair_sum_cube_values": joint_cube_values,
    }


def compute_cubic_refinement(reference_path=REFERENCE):
    catalog = get_catalog()
    reference_bytes = reference_path.read_bytes()
    reference = json.loads(reference_bytes)
    if (reference["archive_sha256"], reference["dataset_sha256"]) != (catalog.sha256, catalog.member_sha256):
        raise ValueError("The reference integral audit does not match the bundled CICY3 archive.")
    sources = _cicy3_source_rows()
    nonproducts = (record for record in catalog.records if not record.product)
    rows = []
    joint = Counter()
    distributions = {key: Counter() for key in INVARIANTS}
    pair_cells = defaultdict(set)
    hodge_pair_cells = defaultdict(set)
    hodge_old = defaultdict(set)
    hodge_new = defaultdict(set)
    witnesses = {}

    for record, prior in zip(nonproducts, reference["rows"], strict=True):
        row, tensor, pairings = _record_signature(record, sources[record.id - 1]["C"][1])
        rank = len(record.ambient_dimensions)
        signature = tuple(row[key] for key in INVARIANTS)
        d1, d2, d3, dp = signature
        hodge = (record.h11, record.h21)

        if (
            (record.id, list(hodge), record.euler, pairings, d1, dp)
            != (prior["id"], prior["hodge"], prior["euler"], prior["c2"],
                prior["cubic_content"], prior["chern_content"])
        ):
            raise ValueError(f"Archive or prior integral-audit mismatch for record {record.id}.")
        if (d2, d3) != evaluated_contents(tensor, rank):
            raise ValueError(f"Value-based cubic content check failed for record {record.id}.")

        pair = (d1, dp)
        rows.append(row)
        joint[signature] += 1
        for key in INVARIANTS:
            distributions[key][row[key]] += 1
        pair_cells[pair].add(signature)
        hodge_pair_cells[hodge, pair].add(signature)
        hodge_old[hodge].add(pair)
        hodge_new[hodge].add(signature)
        if record.id in (*WITNESS_IDS, *DIAGONAL_WITNESS_IDS):
            witnesses[record.id] = witness_record(record, row, tensor, pairings)

    first, second = (witnesses[number] for number in WITNESS_IDS)
    if (
        any(first[key] != second[key] for key in ("hodge", "euler", "ambient_dimensions", "d1", "d3", "dp"))
        or first["d2"] == second["d2"]
    ):
        raise ValueError("The square-content witness no longer distinguishes the stated ambient lattices.")
    diagonal_first, diagonal_second = (witnesses[number] for number in DIAGONAL_WITNESS_IDS)
    if (
        any(diagonal_first[key] != diagonal_second[key] for key in ("hodge", "euler", "d1", "d2", "dp"))
        or diagonal_first["d3"] == diagonal_second["d3"]
    ):
        raise ValueError("The diagonal-content witness no longer distinguishes the stated ambient lattices.")
    summary = {
        "records": len(rows),
        "joint_pairs": len(pair_cells),
        "joint_quadruples": len(joint),
        "hodge_groups": len(hodge_old),
        "split_by_pair": sum(len(cells) > 1 for cells in hodge_old.values()),
        "split_by_quadruple": sum(len(cells) > 1 for cells in hodge_new.values()),
        "pair_cells_refined": sum(len(cells) > 1 for cells in pair_cells.values()),
        "hodge_pair_cells": len(hodge_pair_cells),
        "hodge_pair_cells_refined": sum(len(cells) > 1 for cells in hodge_pair_cells.values()),
        "hodge_groups_refined": sum(len(hodge_new[key]) > len(cells) for key, cells in hodge_old.items()),
    }
    variables = {
        "REFINEMENT_QUADRUPLES": summary["joint_quadruples"],
        "REFINEMENT_HODGE_SPLIT": summary["split_by_quadruple"],
        "REFINEMENT_PAIR_CELLS": summary["pair_cells_refined"],
        "REFINEMENT_HODGE_PAIR_CELLS": summary["hodge_pair_cells"],
        "REFINEMENT_HODGE_PAIR_CELLS_REFINED": summary["hodge_pair_cells_refined"],
        "REFINEMENT_HODGE_GROUPS_REFINED": summary["hodge_groups_refined"],
        "REFINEMENT_WITNESS_FIRST_ID": str(first["id"]),
        "REFINEMENT_WITNESS_SECOND_ID": str(second["id"]),
        "REFINEMENT_WITNESS_FIRST_SIGNATURE": "(" + ",".join(str(first[key]) for key in INVARIANTS) + ")",
        "REFINEMENT_WITNESS_SECOND_SIGNATURE": "(" + ",".join(str(second[key]) for key in INVARIANTS) + ")",
    }
    return {
        "schema_version": 1,
        "dataset": catalog.dataset,
        "archive_sha256": catalog.sha256,
        "dataset_sha256": catalog.member_sha256,
        "integral_receipt_sha256": sha256(reference_bytes).hexdigest(),
        "scope": "Image of the ambient integral divisor lattice for archived non-product CICY3 configurations",
        "reference": {"doi": "10.1162/99608f92.b56a4380", "equation": "2.11"},
        "signature_order": list(INVARIANTS),
        "summary": summary,
        "checks": {
            "record_bindings_and_prior_contents": len(rows),
            "value_based_d2_and_d3": len(rows),
            "divisibility_chain": len(rows),
            "diagonal_riemann_roch": len(rows),
        },
        "marginals": {
            key: [{"value": value, "count": count} for value, count in sorted(distribution.items())]
            for key, distribution in distributions.items()
        },
        "joint": [{"signature": list(signature), "count": count} for signature, count in sorted(joint.items())],
        "witness": [first, second],
        "diagonal_witness": [diagonal_first, diagonal_second],
        "manuscript_values": variables,
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "cubic-refinement.json")
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    args = parser.parse_args()
    report = compute_cubic_refinement(args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
