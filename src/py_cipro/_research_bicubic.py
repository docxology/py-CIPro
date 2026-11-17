"""Exact line-bundle cohomology of the manuscript's specified smooth bicubic."""

from collections import defaultdict
from functools import lru_cache
from itertools import combinations
from math import comb

from sympy import Matrix, QQ
from sympy.polys.matrices import DomainMatrix


COEFFICIENTS = ((1, 1, 1), (1, 2, 4), (1, 3, 9))
GENERIC_REFERENCE = "Constantin and Lukas, arXiv:1808.09992v2, equations (2.4)–(2.5)"


@lru_cache(maxsize=None)
def monomials(degree):
    return tuple((a, b, degree - a - b) for a in range(degree + 1) for b in range(degree - a + 1))


def p2_sections(degree):
    return comb(degree + 2, 2) if degree >= 0 else 0


def ambient_dimensions(a, b):
    a0, a2 = p2_sections(a), p2_sections(-a - 3)
    b0, b2 = p2_sections(b), p2_sections(-b - 3)
    return (a0 * b0, 0, a0 * b2 + a2 * b0, 0, a2 * b2)


def bicubic_index(a, b):
    numerator = 3 * (a + b) * (a * b + 2)
    if numerator % 2:
        raise ValueError(f"Nonintegral bicubic index at {(a, b)}")
    return numerator // 2


def smoothness_minors():
    """Check every square minor used in the support-matrix smoothness proof."""
    selected = list(range(3))
    minors = {}
    for size in (1, 2, 3):
        choices = tuple(combinations(selected, size))
        values = [int(Matrix([[COEFFICIENTS[i][j] for j in cols] for i in rows]).det())
                  for rows in choices for cols in choices]
        if not all(values):
            raise ValueError("Bicubic coefficient matrix has a zero square minor")
        minors[str(size)] = values
    return minors


def residue_classes(a, b):
    groups = defaultdict(list)
    for x in monomials(a):
        for y in monomials(b):
            groups[tuple(value % 3 for value in (*x, *y))].append((x, y))
    return groups


def mixed_factor_rank(a, b, coefficients):
    """Rank on H^0(P², O(a-3)) tensor H^2(P², O(b-3))."""
    source_classes = residue_classes(a - 3, -b)
    target_classes = residue_classes(a, -b - 3)
    ranks = []
    for residue, source in sorted(source_classes.items()):
        target = target_classes.get(residue)
        if not target:
            continue
        target_indices = {term: i for i, term in enumerate(target)}
        entries = {}
        for column, (x, y) in enumerate(source):
            for i in range(3):
                raised_x = x[:i] + (x[i] + 3,) + x[i + 1:]
                for j in range(3):
                    if y[j] >= 3:
                        lowered_y = y[:j] + (y[j] - 3,) + y[j + 1:]
                        row = target_indices[raised_x, lowered_y]
                        entries[(row, column)] = QQ(coefficients[i][j])
        rank = DomainMatrix.from_dok(entries, (len(target), len(source)), QQ).rank()
        ranks.append(int(rank))
    return sum(ranks)


def exact_dimensions(a, b):
    source = ambient_dimensions(a - 3, b - 3)
    target = ambient_dimensions(a, b)
    rank2 = mixed_factor_rank(a, b, COEFFICIENTS) + mixed_factor_rank(b, a, tuple(zip(*COEFFICIENTS)))
    # H^0 multiplication is injective and H^4 multiplication is surjective by duality.
    ranks = (source[0], 0, rank2, 0, target[4])
    if any(rank > min(s, t) for rank, s, t in zip(ranks, source, target, strict=True)):
        raise ValueError(f"Invalid ranks for ambient multiplication at {(a, b)}")
    dimensions = [
        target[q] - ranks[q] + source[q + 1] - ranks[q + 1]
        for q in range(4)
    ]
    return dimensions, source[2], target[2], rank2


def generic_dimensions(a, b):
    """Evaluate the published generic bicubic formula and its Serre dual."""
    def lower_degrees(x, y):
        x, y = sorted((x, y))
        index = bicubic_index(x, y)
        if x > 0:
            return (index, 0)
        if x == 0:
            return (p2_sections(y), p2_sections(y - 3))
        if y > -x:
            return (0, -index)
        return (0, 0)

    h0, h1 = lower_degrees(a, b)
    h3, h2 = lower_degrees(-a, -b)
    return [h0, h1, h2, h3]


def bicubic_study_row(a, b, native_supported):
    """Recompute one charge using the precise equation and generic benchmark."""
    exact, domain, codomain, rank = exact_dimensions(a, b)
    generic = generic_dimensions(a, b)
    index = bicubic_index(a, b)
    if exact[0] - exact[1] + exact[2] - exact[3] != index:
        raise ValueError(f"Index mismatch at {(a, b)}")
    if any(dimension < generic_value for dimension, generic_value in zip(exact, generic, strict=True)):
        raise ValueError(f"Violation of the published generic dimension floor at {(a, b)}")
    extra = exact[1] - generic[1]
    if extra != exact[2] - generic[2] or exact[0] != generic[0] or exact[3] != generic[3]:
        raise ValueError(f"Dimension change is inconsistent with a paired jump at {(a, b)}")
    return {"a": a, "b": b, "h": exact, "generic_h": generic, "index": index,
            "native_supported": native_supported, "ambient_h2": [domain, codomain],
            "rank_h2": rank, "paired_excess": extra}
