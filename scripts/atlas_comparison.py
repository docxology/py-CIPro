#!/usr/bin/env python3
"""Compare presentation and equal-Hodge-pair measures on the CIPro census."""

import argparse
from collections import Counter, defaultdict
from fractions import Fraction
from itertools import accumulate
import json
from pathlib import Path

from py_cipro.catalog import MEMBER, get_catalog


ROOT = Path(__file__).resolve().parents[1]


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


def plot_atlas_comparison(analysis, outputs):
    """Render the figure directly from the recorded comparison statistics."""
    from render_figures import GRID, INK, MUTED, ORANGE, PURPLE, TEAL, _save, plt
    from matplotlib.lines import Line2D
    from matplotlib.ticker import PercentFormatter

    counts = analysis["population"]
    cdf, ranks = analysis["euler_cdf"], analysis["ambient_factor_groups"]
    summary = analysis["summary"]
    fmt = PercentFormatter(1, decimals=0)
    presentation_label = f"Presentations · n={counts['non_product_presentations']:,}"
    pair_label = f"Equal Hodge pairs · n={counts['distinct_non_product_hodge_pairs']:,}"
    style = {
        "font.family": "DejaVu Sans", "font.size": 9, "text.color": INK, "axes.labelcolor": INK,
        "axes.titleweight": "bold", "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": MUTED, "axes.axisbelow": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.linewidth": 0.7, "xtick.color": MUTED, "ytick.color": MUTED,
        "pdf.fonttype": 42,
    }
    with plt.rc_context(style):
        fig, ((euler, mix), (flag, change)) = plt.subplots(2, 2, figsize=(9.0, 6.05))
        fig.subplots_adjust(left=.105, right=.972, top=.795, bottom=.095, wspace=.37, hspace=.54)
        fig.text(.105, .953, "What changes when each Hodge pair counts equally?",
                 fontsize=17, weight="bold", va="top")
        fig.legend(
            handles=[
                Line2D([], [], lw=2, color=TEAL, marker="o", markersize=4, label=presentation_label),
                Line2D([], [], lw=2, color=PURPLE, linestyle="--", marker="D", markersize=4, label=pair_label),
            ],
            loc="upper left", bbox_to_anchor=(.10, .897), frameon=False, ncol=2,
            columnspacing=2.35, borderpad=0, labelspacing=.3,
        )
        fig.add_artist(Line2D([.105, .972], [.842, .842], transform=fig.transFigure, color=GRID, lw=.8))

        panels = (
            (euler, "A", "Euler distributions"), (mix, "B", "Weight by ambient factor count"),
            (flag, "C", "Favour share within each count"), (change, "D", "Decomposition of pooled change"),
        )
        for ax, letter, label in panels:
            ax.set_title(f"{letter}   {label}", loc="left", fontsize=10.5, pad=9)
            ax.grid(axis="y")

        e = [cdf[0]["euler"] - 5, *(row["euler"] for row in cdf)]
        p0 = [0, *(row["record_count_le"] / counts["non_product_presentations"] for row in cdf)]
        p1 = [0, *(row["pair_count_le"] / counts["distinct_non_product_hodge_pairs"] for row in cdf)]
        euler.step(e, p0, where="post", color=TEAL, lw=1.9)
        euler.step(e, p1, where="post", color=PURPLE, linestyle="--", lw=1.9)
        peak = summary["largest_cdf_gap"]
        x = peak["euler"]
        low, high = sorted((peak["record_count_le"] / counts["non_product_presentations"],
                            peak["pair_count_le"] / counts["distinct_non_product_hodge_pairs"]))
        euler.annotate("", (x, low), (x, high),
                       arrowprops={"arrowstyle": "|-|", "linewidth": 1.1, "color": INK, "mutation_scale": 4})
        euler.annotate(f'{100 * float(Fraction(*peak["absolute_share"])):.2f} pp',
                       xy=(x, (low + high) / 2), xytext=(-17, 4), textcoords="offset points",
                       va="center", ha="right", fontsize=8.3, color=INK)
        euler.set(xlim=(e[0], 3), ylim=(0, 1.02), xlabel="Euler characteristic χ", ylabel="Cumulative share up to χ")
        euler.yaxis.set_major_formatter(fmt)

        m = [row["ambient_factors"] for row in ranks]
        for ax, first, second in (
            (mix, "presentation_mass", "pair_balanced_mass"),
            (flag, "presentation_flagged_share", "pair_balanced_flagged_share"),
        ):
            ax.plot(m, [float(Fraction(*row[first])) for row in ranks], color=TEAL, lw=1.7, marker="o", ms=3.8)
            ax.plot(m, [float(Fraction(*row[second])) for row in ranks], color=PURPLE,
                    lw=1.7, linestyle="--", marker="D", ms=3.5)
            ax.set(xlim=(m[0] - .3, m[-1] + .3), xticks=m, xlabel="Ambient projective factors")
            ax.yaxis.set_major_formatter(fmt)
        mix.set(ylabel="Share of total weight", ylim=(0, .265), yticks=[0, .05, .10, .15, .20, .25])
        flag.set(ylabel="Flagged share", ylim=(0, 1.04), yticks=[0, .25, .5, .75, 1])

        effects = summary["flagged_share_change"]
        values = [100 * float(Fraction(*effects[key])) for key in ("composition", "within_rank", "total")]
        positions = [0, 1, 2]
        change.barh(positions, values, height=.52, color=["#287c9d", ORANGE, INK], zorder=2)
        change.axvline(0, color=MUTED, lw=.74, zorder=3)
        change.set_yticks(positions, ["Composition", "Within group", "Net change"])
        change.invert_yaxis()
        change.tick_params(axis="y", length=0, pad=5)
        change.set(xlabel="Change (percentage points)", xlim=(min(values) - 5, max(values) + 4))
        change.grid(axis="y", visible=False)
        change.grid(axis="x", visible=True)
        for rank, value in zip(positions, values):
            offset = .7 if value >= 0 else -.7
            change.text(value + offset, rank, f"{value:+.2f}", va="center",
                        ha="left" if value >= 0 else "right", weight="bold", fontsize=8.8)
        for output in outputs:
            _save(fig, output)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "atlas-comparison.json")
    parser.add_argument("--figure", type=Path, default=ROOT / "manuscript" / "figures" / "atlas-comparison.png")
    parser.add_argument("--vector", type=Path, help="Also save a vector PDF")
    args = parser.parse_args()
    analysis = atlas_comparison(get_catalog())
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plot_atlas_comparison(analysis, [args.figure, *([args.vector] if args.vector else [])])


if __name__ == "__main__":
    main()
