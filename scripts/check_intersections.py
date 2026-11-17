#!/usr/bin/env python3
"""Compute exact Chern and intersection fixtures for the quintic and bicubic."""

import argparse
from itertools import combinations_with_replacement
import json
from math import comb
from pathlib import Path

from py_cipro.catalog import get_catalog


def multiply(left, right, dimensions, limit=None):
    result = {}
    for left_power, left_coefficient in left.items():
        for right_power, right_coefficient in right.items():
            power = tuple(a + b for a, b in zip(left_power, right_power))
            if any(a > b for a, b in zip(power, dimensions)):
                continue
            if limit is not None and sum(power) > limit:
                continue
            result[power] = result.get(power, 0) + left_coefficient * right_coefficient
    return {power: coefficient for power, coefficient in result.items() if coefficient}


def analytic_fixture(record):
    dimensions = record.ambient_dimensions
    rank = len(dimensions)
    zero = (0,) * rank
    units = tuple(tuple(int(i == j) for j in range(rank)) for i in range(rank))
    degree = sum(dimensions) - len(record.configuration[0])
    if degree != 3 or len(record.configuration[0]) != 1 or any(
        row[0] <= 0 for row in record.configuration
    ):
        raise ValueError("The Hodge fixtures require an ample hypersurface of complex dimension 3")

    chern = {zero: 1}
    for dimension, unit in zip(dimensions, units):
        factor = {
            tuple(n * exponent for exponent in unit): comb(dimension + 1, n)
            for n in range(min(degree, dimension) + 1)
        }
        chern = multiply(chern, factor, dimensions, degree)

    divisor = {unit: row[0] for unit, row in zip(units, record.configuration)}
    divisor_power = {zero: 1}
    inverse = {zero: 1}
    for exponent in range(1, degree + 1):
        divisor_power = multiply(divisor_power, divisor, dimensions, degree)
        inverse.update({power: (-1) ** exponent * value for power, value in divisor_power.items()})
    chern = multiply(chern, inverse, dimensions, degree)
    c2 = {power: coefficient for power, coefficient in chern.items() if sum(power) == 2}
    c3 = {power: coefficient for power, coefficient in chern.items() if sum(power) == 3}
    if any(sum(power) == 1 for power in chern):
        raise ValueError(f"Nonzero first Chern class for record {record.id}")

    def integrate(poly):
        return multiply(poly, divisor, dimensions).get(dimensions, 0)

    euler = integrate(c3)
    h11 = rank  # Weak Lefschetz for these smooth ample hypersurfaces
    h21 = h11 - euler // 2
    expected = (h11, h21, euler)
    archived = (record.h11, record.h21, record.euler)
    if expected != archived:
        raise ValueError(f"Analytic values {expected} differ from archived values {archived}")

    triples = []
    for indices in combinations_with_replacement(range(rank), 3):
        power = tuple(indices.count(i) for i in range(rank))
        triples.append({"indices": [i + 1 for i in indices], "integral": integrate({power: 1})})

    return {
        "record": record.id,
        "ambient_dimensions": dimensions,
        "configuration": record.configuration,
        "h11": h11,
        "h21": h21,
        "euler": euler,
        "c2": [{"exponents": powers, "value": value} for powers, value in sorted(c2.items())],
        "c3": [{"exponents": powers, "value": value} for powers, value in sorted(c3.items())],
        "c2_against_hyperplanes": [integrate(multiply(c2, {unit: 1}, dimensions)) for unit in units],
        "triple_intersections": triples,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/analytic-checks.json"))
    args = parser.parse_args()
    catalog = get_catalog()
    payload = {
        "method": "Ambient truncated integer polynomial ring, adjunction and weak Lefschetz",
        "dataset": catalog.dataset,
        "dataset_sha256": catalog.member_sha256,
        "fixtures": {
            "quintic": analytic_fixture(catalog.record(7890)),
            "bicubic": analytic_fixture(catalog.record(7884)),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
