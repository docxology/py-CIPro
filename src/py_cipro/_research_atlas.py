"""Exact weights and finite-archive statistics for the CICY3 manuscript."""

from collections import Counter, defaultdict
from fractions import Fraction
from itertools import accumulate

from .catalog import MEMBER


def _fraction(value):
    return [value.numerator, value.denominator]


def _percent(value):
    return f"{100 * float(value):.2f}"


def _signed_points(value):
    return f"{100 * float(value):+.2f}"


def atlas_comparison(catalog):
    """Compute the weighted finite-archive statistics with rational arithmetic."""
    pairs = defaultdict(list)
    ranks = defaultdict(list)
    for record in catalog.records:
        if not record.product:
            key = (record.h11, record.h21)
            pairs[key].append(record)
            ranks[len(record.ambient_dimensions)].append(record)
    pair_count = len(pairs)
    record_count = sum(map(len, pairs.values()))

    pair_rows = []
    euler_records = Counter()
    euler_pairs = Counter()
    for (h11, h21), rows in sorted(pairs.items()):
        euler = 2 * (h11 - h21)
        if any(row.euler != euler for row in rows):
            raise ValueError(f"Archive Euler mismatch at Hodge pair {(h11, h21)}")
        euler_records[euler] += len(rows)
        euler_pairs[euler] += 1
        pair_rows.append({
            "h11": h11, "h21": h21, "record_count": len(rows),
            "flagged_count": sum(row.favourable for row in rows),
            "ambient_factor_counts": sorted({len(row.ambient_dimensions) for row in rows}),
        })

    eulers = sorted(euler_records)
    record_cdf = list(accumulate(euler_records[e] for e in eulers))
    pair_cdf = list(accumulate(euler_pairs[e] for e in eulers))
    cdf = [
        {"euler": euler, "record_count_le": n, "pair_count_le": p}
        for euler, n, p in zip(eulers, record_cdf, pair_cdf)
    ]
    record_median = next(row["euler"] for row in cdf if row["record_count_le"] * 2 >= record_count)
    pair_median = next(row["euler"] for row in cdf if row["pair_count_le"] * 2 >= pair_count)

    def gap(row):
        return abs(Fraction(row["pair_count_le"], pair_count) - Fraction(row["record_count_le"], record_count))

    peak_gap = max(cdf, key=gap)
    rank_rows = []
    composition = within = Fraction()
    flagged_total = 0
    pair_flagged_total = Fraction()
    for m, records in sorted(ranks.items()):
        count = len(records)
        flagged = sum(row.favourable for row in records)
        keys = Counter((row.h11, row.h21) for row in records)
        flagged_keys = Counter((row.h11, row.h21) for row in records if row.favourable)
        pair_mass = sum((Fraction(n, len(pairs[key])) for key, n in keys.items()), Fraction())
        flagged_pair_mass = sum((Fraction(n, len(pairs[key])) for key, n in flagged_keys.items()), Fraction())
        w, w_star = Fraction(count, record_count), pair_mass / pair_count
        f, f_star = Fraction(flagged, count), flagged_pair_mass / pair_mass
        composition += (w_star - w) * (f + f_star) / 2
        within += (w + w_star) * (f_star - f) / 2
        flagged_total += flagged
        pair_flagged_total += flagged_pair_mass
        rank_rows.append({
            "ambient_factors": m, "record_count": count, "flagged_count": flagged,
            "pair_count": len(keys), "presentation_mass": _fraction(w), "pair_balanced_mass": _fraction(w_star),
            "presentation_flagged_share": _fraction(f), "pair_balanced_flagged_share": _fraction(f_star),
            "pair_balanced_flagged_mass": _fraction(flagged_pair_mass / pair_count),
        })
    flagged = Fraction(flagged_total, record_count)
    balanced_flagged = pair_flagged_total / pair_count
    difference = balanced_flagged - flagged
    if difference != composition + within:
        raise ValueError("Ambient-rank decomposition does not close")

    flag_statuses = Counter(
        "mixed" if 0 < row["flagged_count"] < row["record_count"] else
        "all_flagged" if row["flagged_count"] else "all_unflagged"
        for row in pair_rows
    )
    modal_pair = max(pair_rows, key=lambda row: row["record_count"])
    ranks_with_decrease = [
        row["ambient_factors"] for row in rank_rows
        if Fraction(*row["pair_balanced_flagged_share"]) < Fraction(*row["presentation_flagged_share"])
    ]
    variables = {
        "ATLAS_PRESENTATION_MEDIAN": str(record_median),
        "ATLAS_PAIR_MEDIAN": str(pair_median),
        "ATLAS_MAX_CDF_GAP_PP": _percent(gap(peak_gap)),
        "ATLAS_MAX_CDF_GAP_EULER": str(peak_gap["euler"]),
        "ATLAS_CDF_PRESENTATION_SHARE": _percent(Fraction(peak_gap["record_count_le"], record_count)),
        "ATLAS_CDF_PAIR_SHARE": _percent(Fraction(peak_gap["pair_count_le"], pair_count)),
        "ATLAS_PRESENTATION_FLAGGED": _percent(flagged),
        "ATLAS_PAIR_FLAGGED": _percent(balanced_flagged),
        "ATLAS_FLAGGED_DIFF_PP": _signed_points(difference),
        "ATLAS_RANK_COMPOSITION_PP": _signed_points(composition),
        "ATLAS_WITHIN_RANK_PP": _signed_points(within),
        "ATLAS_MIXED_PAIRS": str(flag_statuses["mixed"]),
        "ATLAS_MIXED_PAIRS_SHARE": _percent(Fraction(flag_statuses["mixed"], pair_count)),
        "ATLAS_ALL_FLAGGED_PAIRS": str(flag_statuses["all_flagged"]),
        "ATLAS_ALL_UNFLAGGED_PAIRS": str(flag_statuses["all_unflagged"]),
        "ATLAS_MODAL_PAIR": f"({modal_pair['h11']},{modal_pair['h21']})",
        "ATLAS_MODAL_PAIR_FLAGGED": str(modal_pair["flagged_count"]),
        "ATLAS_MODAL_PAIR_COUNT": str(modal_pair["record_count"]),
        "ATLAS_MODAL_PAIR_FACTOR_RANGE": f"{min(modal_pair['ambient_factor_counts'])}–{max(modal_pair['ambient_factor_counts'])}",
        "ATLAS_RANKS_WITH_DECREASE": ", ".join(map(str, ranks_with_decrease)),
        "ATLAS_LARGEST_FACTOR_GROUP_N": str(rank_rows[-1]["record_count"]),
    }
    return {
        "schema_version": 1,
        "dataset": catalog.dataset,
        "dataset_member": MEMBER,
        "archive_sha256": catalog.sha256,
        "dataset_sha256": catalog.member_sha256,
        "release": catalog.release,
        "population": {"non_product_presentations": record_count, "distinct_non_product_hodge_pairs": pair_count},
        "euler_cdf": cdf,
        "hodge_pairs": pair_rows,
        "ambient_factor_groups": rank_rows,
        "summary": {
            "median_euler": {"presentation": record_median, "equal_pair": pair_median},
            "largest_cdf_gap": {**peak_gap, "absolute_share": _fraction(gap(peak_gap))},
            "presentation_flagged_share": _fraction(flagged),
            "pair_balanced_flagged_share": _fraction(balanced_flagged),
            "flag_status_by_pair": dict(sorted(flag_statuses.items())),
            "flagged_share_change": {
                "composition": _fraction(composition), "within_rank": _fraction(within),
                "total": _fraction(difference),
            },
        },
        "manuscript_values": variables,
    }
