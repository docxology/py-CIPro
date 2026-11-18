#!/usr/bin/env python3
"""Audit the fixed divisor of the Riemann–Roch index on each CICY3 ambient lattice."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path

from py_cipro._research_chern import ambient_intersections
from py_cipro._research_cubic import _index_divisor_details
from py_cipro.catalog import _cicy3_source_rows, get_catalog


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "cubic-refinement.json"
CUBIC_SIGNATURE = ("d1", "d2", "d3", "dp")
WITNESS_IDS = (7626, 7635)


def signed_index_values(cubic, pairings):
    """Evaluate the index on single, signed-pair, and triple probes."""
    def evaluate(charge):
        cube = sum(
            a * b * c * cubic((i, j, k))
            for (i, a), (j, b), (k, c) in product(charge, repeat=3)
        )
        chern = sum(value * pairings[axis] for axis, value in charge)
        result, remainder = divmod(2 * cube + chern, 12)
        if remainder:
            raise ValueError(f"Nonintegral line-bundle index at charge {charge}.")
        return result

    units = [(axis, 1) for axis in range(len(pairings))]
    yield from (evaluate((unit,)) for unit in units)
    yield from (evaluate(((axis, 2),)) for axis in range(len(pairings)))
    for first, second in combinations(units, 2):
        yield evaluate((first, second))
        yield evaluate((first, (second[0], -1)))
    yield from (evaluate(triple) for triple in combinations(units, 3))


def prime_to_six_part(value):
    """Return the factor of a positive integer supported at primes above three."""
    for prime in (2, 3):
        while value % prime == 0:
            value //= prime
    return value


def compute_index_divisibility(reference_path=REFERENCE):
    """Compute the exact value gcd and compare it with the source-bound cubic audit."""
    catalog = get_catalog()
    reference_bytes = reference_path.read_bytes()
    reference = json.loads(reference_bytes)
    if (
        reference["archive_sha256"] != catalog.sha256
        or reference["dataset_sha256"] != catalog.member_sha256
        or tuple(reference["signature_order"]) != CUBIC_SIGNATURE
    ):
        raise ValueError("The cubic refinement receipt does not match the bundled CICY3 archive.")

    distribution = Counter()
    joint = Counter()
    quadruples = defaultdict(set)
    hodge_quadruples = defaultdict(set)
    hodge_before = defaultdict(set)
    hodge_after = defaultdict(set)
    witness = {}
    rows = []
    evaluated_probes = 0
    sources = _cicy3_source_rows()
    records = (record for record in catalog.records if not record.product)

    for record, prior in zip(records, reference["rows"], strict=True):
        cycle, cubic, pairings, indices = ambient_intersections(record)
        signature = tuple(prior[key] for key in CUBIC_SIGNATURE)
        d1, _, _, dp = signature
        if (
            prior["id"] != record.id
            or tuple(pairings) != sources[record.id - 1]["C"][1]
            or (d1, dp) != (gcd(*cycle.values()), gcd(*pairings))
        ):
            raise ValueError(f"Archive or cubic content mismatch for record {record.id}.")

        index_divisor, paired_coefficients = _index_divisor_details(cubic, indices, d1)
        probe_values = tuple(signed_index_values(cubic, pairings))
        evaluated_probes += len(probe_values)
        if index_divisor != gcd(*probe_values):
            raise ValueError(f"Signed index evaluations disagree for record {record.id}.")

        upper_divisor = gcd(d1, dp)
        if (
            index_divisor < 1
            or upper_divisor % index_divisor
            or prime_to_six_part(index_divisor) != prime_to_six_part(upper_divisor)
        ):
            raise ValueError(f"Fixed-divisor constraint failed for record {record.id}.")

        extended_signature = (*signature, index_divisor)
        hodge = (record.h11, record.h21)
        row = {"id": record.id, "index_divisor": index_divisor}
        rows.append(row)
        distribution[index_divisor] += 1
        joint[extended_signature] += 1
        quadruples[signature].add(index_divisor)
        hodge_quadruples[hodge, signature].add(index_divisor)
        hodge_before[hodge].add(signature)
        hodge_after[hodge].add(extended_signature)
        if record.id in WITNESS_IDS:
            witness[record.id] = {
                **row,
                "signature": list(signature),
                "hodge": list(hodge),
                "euler": record.euler,
                "ambient_dimensions": list(record.ambient_dimensions),
                "configuration": [list(degrees) for degrees in record.configuration],
                "favourable": record.favourable,
                "hyperplane_indices": indices,
                "paired_index_coefficients": paired_coefficients,
            }

    first, second = (witness[record_id] for record_id in WITNESS_IDS)
    if (
        any(first[key] != second[key] for key in ("hodge", "euler", "signature", "favourable"))
        or first["index_divisor"] == second["index_divisor"]
    ):
        raise ValueError("The matched records must have distinct index fixed divisors.")

    summary = {
        "records": len(rows),
        "nonunit_records": len(rows) - distribution[1],
        "signatures_before": len(quadruples),
        "signatures_after": len(joint),
        "quadruples_refined": sum(len(values) > 1 for values in quadruples.values()),
        "hodge_groups": len(hodge_before),
        "hodge_groups_split_before": sum(len(values) > 1 for values in hodge_before.values()),
        "hodge_groups_split_after": sum(len(values) > 1 for values in hodge_after.values()),
        "hodge_groups_refined": sum(
            len(hodge_after[key]) > len(values) for key, values in hodge_before.items()
        ),
        "hodge_quadruple_cells_refined": sum(len(values) > 1 for values in hodge_quadruples.values()),
    }
    return {
        "schema_version": 1,
        "dataset": catalog.dataset,
        "archive_sha256": catalog.sha256,
        "dataset_sha256": catalog.member_sha256,
        "cubic_refinement_sha256": sha256(reference_bytes).hexdigest(),
        "scope": "Fixed divisor of the Riemann–Roch index on each non-product ambient divisor image",
        "signature_order": [*CUBIC_SIGNATURE, "index_divisor"],
        "summary": summary,
        "checks": {
            "archive_and_prior_content": len(rows),
            "signed_index_gcds": len(rows),
            "signed_index_probes": evaluated_probes,
            "fixed_divisor_constraints": len(rows),
        },
        "distribution": [
            {"value": value, "count": count} for value, count in sorted(distribution.items())
        ],
        "joint": [
            {"signature": list(signature), "count": count} for signature, count in sorted(joint.items())
        ],
        "witness": [first, second],
        "manuscript_values": {
            "INDEX_DIVISIBILITY_NONUNIT": summary["nonunit_records"],
            "INDEX_DIVISIBILITY_SIGNATURES": summary["signatures_after"],
            "INDEX_DIVISIBILITY_HODGE_REFINED": summary["hodge_groups_refined"],
            "INDEX_DIVISIBILITY_WITNESS_FIRST_ID": str(first["id"]),
            "INDEX_DIVISIBILITY_WITNESS_SECOND_ID": str(second["id"]),
            "INDEX_DIVISIBILITY_WITNESS_FIRST_VALUE": first["index_divisor"],
            "INDEX_DIVISIBILITY_WITNESS_SECOND_VALUE": second["index_divisor"],
        },
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "index-divisibility.json")
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    args = parser.parse_args()
    report = compute_index_divisibility(args.reference)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
