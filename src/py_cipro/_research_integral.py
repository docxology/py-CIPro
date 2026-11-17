"""Exact ambient divisor-lattice invariants for a CICY3 source record."""

from itertools import combinations
from math import gcd

from ._research_chern import ambient_intersections


def integral_invariants(record, source):
    """Recompute the integral study row from the configuration and check its archived pairing."""
    if record.product or source["Num"] != record.id:
        raise ValueError("Select the matching source row for a non-product CICY3 record.")
    cycle, cubic, pairings, indices = ambient_intersections(record)
    if tuple(pairings) != source["C"][1]:
        raise ValueError(f"Second Chern pairings disagree with the archive for record {record.id}")

    # Exponent complements identify cycle coefficients with the nonzero cubic evaluations.
    g3, g2 = gcd(*cycle.values()), gcd(*pairings)
    if g2 % gcd(2 * g3, 12):
        raise ValueError(f"Riemann–Roch divisibility failed for record {record.id}")
    rank = len(record.ambient_dimensions)
    if any((cubic((i, i, j)) + cubic((i, j, j))) % 2 for i, j in combinations(range(rank), 2)):
        raise ValueError(f"Riemann–Roch pairwise parity failed for record {record.id}")
    return {
        "id": record.id,
        "ambient_factors": rank,
        "favourable": record.favourable,
        "hodge": [record.h11, record.h21],
        "euler": record.euler,
        "cubic_content": g3,
        "chern_content": g2,
        "c2": pairings,
        "hyperplane_indices": indices,
    }
