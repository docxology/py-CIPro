"""Exact intersection contractions for the all-ones ambient polarization."""

from collections import Counter
from itertools import product
from math import factorial, prod


def polarized_invariants(record):
    """Contract Newton's quadratic power sum and the ambient polarization."""
    dimensions = record.ambient_dimensions
    columns = [
        tuple((i, degree) for i, degree in enumerate(column) if degree)
        for column in zip(*record.configuration)
    ]
    cycle = {(0,) * len(dimensions): 1}
    for column in sorted(columns, key=len):
        updated = Counter()
        for powers, coefficient in cycle.items():
            for axis, degree in column:
                if powers[axis] < dimensions[axis]:
                    raised = powers[:axis] + (powers[axis] + 1,) + powers[axis + 1:]
                    updated[raised] += coefficient * degree
        cycle = updated

    def cubic(indices):
        residual = list(dimensions)
        for axis in indices:
            residual[axis] -= 1
        return cycle.get(tuple(residual), 0)

    weights = Counter()
    for column in columns:
        for (i, first), (j, second) in product(column, repeat=2):
            weights[i, j] += first * second
    for i, dimension in enumerate(dimensions):
        weights[i, i] -= dimension + 1

    pairings = []
    for axis in range(len(dimensions)):
        doubled = sum(weight * cubic((i, j, axis)) for (i, j), weight in weights.items())
        pairing, remainder = divmod(doubled, 2)
        if remainder or (2 * cubic((axis,) * 3) + pairing) % 12:
            raise ValueError(f"Failed integral Chern or Riemann–Roch check at record {record.id}")
        pairings.append(pairing)

    volume = sum(
        6 * coefficient // prod(factorial(n - k) for k, n in zip(powers, dimensions))
        for powers, coefficient in cycle.items()
    )
    contraction = sum(pairings)
    index, remainder = divmod(2 * volume + contraction, 12)
    if volume < 1 or remainder:
        raise ValueError(f"Failed ample polarization volume or index check at record {record.id}")
    return pairings, volume, contraction, index
