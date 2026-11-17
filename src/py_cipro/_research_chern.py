"""Exact intersection contractions for the all-ones ambient polarization."""

from collections import Counter
from itertools import combinations_with_replacement
from math import factorial, prod


def ambient_intersections(record):
    """Compute the fundamental class, cubic evaluations, and second Chern pairings."""
    dimensions = record.ambient_dimensions
    columns = [
        tuple((i, degree) for i, degree in enumerate(column) if degree)
        for column in zip(*record.configuration, strict=True)
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

    weights = Counter({(i, i): -(dimension + 1) for i, dimension in enumerate(dimensions)})
    for column in columns:
        for (i, first), (j, second) in combinations_with_replacement(column, 2):
            weights[i, j] += first * second * (1 if i == j else 2)
    weights = [(i, j, weight) for (i, j), weight in weights.items() if weight]

    pairings = []
    indices = []
    for axis in range(len(dimensions)):
        doubled = sum(weight * cubic((i, j, axis)) for i, j, weight in weights)
        pairing, remainder = divmod(doubled, 2)
        index, index_remainder = divmod(2 * cubic((axis,) * 3) + pairing, 12)
        if remainder or index_remainder:
            raise ValueError(f"Failed integral Chern or Riemann–Roch check at record {record.id}")
        pairings.append(pairing)
        indices.append(index)
    return cycle, cubic, pairings, indices


def polarized_invariants(record):
    """Contract the cubic form and second Chern functional at the all-ones polarization."""
    cycle, _, pairings, _ = ambient_intersections(record)
    volume = sum(
        6 * coefficient // prod(factorial(n - k) for k, n in zip(powers, record.ambient_dimensions))
        for powers, coefficient in cycle.items()
    )
    contraction = sum(pairings)
    index, remainder = divmod(2 * volume + contraction, 12)
    if volume < 1 or remainder:
        raise ValueError(f"Failed ample polarization volume or index check at record {record.id}")
    return pairings, volume, contraction, index
