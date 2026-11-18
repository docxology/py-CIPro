"""Exact cubic and second Chern divisibilities on the supplied CICY3 lattice."""

from itertools import combinations, combinations_with_replacement, product
from math import gcd

from ._research_chern import ambient_intersections
from .catalog import _cicy3_source_rows, get_catalog


SIGNATURE_KEYS = ("d1", "d2", "d3", "dp")


def _valid_signature(signature):
    d1, d2, d3, dp = signature
    return (
        all(type(value) is int for value in signature)
        and min(d1, d2, d3) > 0 and dp >= 0
        and d2 % d1 == 0 and d3 % d2 == 0
        and 2 * d1 % d2 == 0 and 6 * d1 % d3 == 0
        and dp % gcd(2 * d3, 12) == 0
    )


def _checked_intersections(record, archived_pairings):
    if record.product:
        raise ValueError("Select an archived non-product CICY3 record.")
    cycle, cubic, pairings, indices = ambient_intersections(record)
    if tuple(pairings) != archived_pairings:
        raise ValueError(f"Second Chern pairings disagree with the archive at record {record.id}.")
    return cycle, cubic, pairings, indices


def _record_signature(record, archived_pairings):
    _, triple, pairings, _ = _checked_intersections(record, archived_pairings)
    rank = len(record.ambient_dimensions)
    tensor = {ijk: triple(ijk) for ijk in combinations_with_replacement(range(rank), 3)}
    d1 = gcd(*tensor.values())
    squares = [tensor[tuple(sorted((i, i, j)))] for i, j in product(range(rank), repeat=2)]
    diagonal = [tensor[i, i, i] for i in range(rank)]
    for i, j in combinations(range(rank), 2):
        a, b = tensor[i, i, j], tensor[i, j, j]
        diagonal.extend((3 * (a + b), 3 * (a - b)))
    signature = (d1, gcd(2 * d1, *squares), gcd(6 * d1, *diagonal), gcd(*pairings))
    if not _valid_signature(signature):
        raise ValueError(f"Cubic content or Riemann–Roch check failed at record {record.id}.")
    return {"id": record.id, **dict(zip(SIGNATURE_KEYS, signature, strict=True))}, tensor, pairings


def _index_divisor_details(cubic, indices, d1):
    """Return the fixed divisor and mixed quadratic coefficients in the binomial basis."""
    paired = []
    for i, j in combinations(range(len(indices)), 2):
        coefficient, remainder = divmod(cubic((i, i, j)) + cubic((i, j, j)), 2)
        if remainder:
            raise ValueError("Nonintegral mixed index coefficient.")
        paired.append(coefficient)
    return gcd(d1, *indices, *paired), paired


def _archived_record_and_pairings(record_id):
    try:
        record = get_catalog().record(record_id)
    except KeyError:
        raise ValueError("Select an archived non-product CICY3 record by integer ID.") from None
    return record, _cicy3_source_rows()[record.id - 1]["C"][1]


def cubic_signature(record_id: int) -> dict[str, int]:
    """Recompute d1, d2, d3, and dp from one pinned non-product CICY3 configuration.

    The result describes the ambient integral divisor lattice and includes the
    one-based archive ID. Raise ValueError for IDs outside the non-product cohort.
    """
    result, _, _ = _record_signature(*_archived_record_and_pairings(record_id))
    return result


def ambient_index_divisor(record_id: int) -> int:
    """Recompute the gcd of all ambient line-bundle indices on one CICY3 lattice.

    Supply the one-based archive ID of a non-product configuration. Invalid
    IDs and product records raise ValueError.
    """
    cycle, cubic, _, indices = _checked_intersections(*_archived_record_and_pairings(record_id))
    divisor, _ = _index_divisor_details(cubic, indices, gcd(*cycle.values()))
    return divisor
