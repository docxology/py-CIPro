#!/usr/bin/env python3
"""Compare presentation and equal-Hodge-pair measures on the CIPro census."""

import argparse
from fractions import Fraction
import json
from pathlib import Path

from py_cipro.catalog import get_catalog
from py_cipro._research_atlas import atlas_comparison


ROOT = Path(__file__).resolve().parents[1]


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
    parser.add_argument("--figure", type=Path, default=ROOT / "docs/manuscript" / "figures" / "atlas-comparison.png")
    parser.add_argument("--vector", type=Path, help="Also save a vector PDF")
    args = parser.parse_args()
    analysis = atlas_comparison(get_catalog())
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(analysis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plot_atlas_comparison(analysis, [args.figure, *([args.vector] if args.vector else [])])


if __name__ == "__main__":
    main()
