#!/usr/bin/env python3
"""Render the Cicy3 atlas figure from the bundled, validated archive."""

import argparse
from collections import Counter
import json
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.ticker import FixedLocator

from py_cipro.catalog import get_catalog

INK = "#142a3d"
MUTED = "#486173"
GRID = "#ced9df"
TEAL = "#087b76"
PRODUCT = "#64666b"


def _counts(records):
    return (
        Counter((record.h11, record.h21) for record in records),
        Counter(record.euler for record in records),
    )


def write_summary(path: Path) -> None:
    catalog = get_catalog()
    records = catalog.records
    pairs, eulers = _counts(records)
    product_pairs = {(record.h11, record.h21) for record in records if record.product}
    mode, mode_count = eulers.most_common(1)[0]
    summary = {
        "dataset": catalog.dataset,
        "release": catalog.release,
        "archive_sha256": catalog.sha256,
        "dataset_sha256": catalog.member_sha256,
        "record_count": len(records),
        "hodge_pair_count": len(pairs),
        "non_product_hodge_pair_count": len({(r.h11, r.h21) for r in records if not r.product}),
        "most_frequent_hodge_pairs": [
            {"h11": pair[0], "h21": pair[1], "record_count": count}
            for pair, count in pairs.most_common(2)
        ],
        "product_count": sum(record.product for record in records),
        "product_hodge_pairs": sorted(product_pairs),
        "favourable_count": sum(record.favourable for record in records),
        "euler": {
            "min": min(eulers),
            "max": max(eulers),
            "median": median(record.euler for record in records),
            "mode": mode,
            "mode_count": mode_count,
            "value_count": len(eulers),
            "zero_count": eulers[0],
            "hodge_identity_matches": sum(r.euler == 2 * (r.h11 - r.h21) for r in records),
        },
        "fixtures": {"bicubic": catalog.record(7884).summary(), "quintic": catalog.record(7890).summary()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def plot_atlas(path: Path) -> None:
    catalog = get_catalog()
    records = catalog.records
    pairs = Counter((record.h11, record.h21) for record in records if not record.product)
    eulers = Counter(record.euler for record in records)
    ordered_pairs = sorted(pairs, key=pairs.get)

    with plt.rc_context({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.45,
        "axes.axisbelow": True,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "mathtext.default": "regular",
        "pdf.fonttype": 42,
    }):
        fig, (hodge, euler) = plt.subplots(
            1, 2, figsize=(8.4, 4.3), gridspec_kw={"width_ratios": [1.05, 1.0]}
        )
        fig.subplots_adjust(left=0.085, right=0.98, bottom=0.265, top=0.77, wspace=0.31)
        fig.text(0.085, 0.925, "CICY threefold configurations", fontsize=17, weight="bold")
        fig.text(
            0.085, 0.87,
            f"CIPro v1.0 Cicy3 archive · {len(records):,} recorded configurations",
            color=MUTED, fontsize=9,
        )

        dots = hodge.scatter(
            [pair[0] for pair in ordered_pairs],
            [pair[1] for pair in ordered_pairs],
            c=[pairs[pair] for pair in ordered_pairs],
            cmap="viridis", norm=LogNorm(vmin=1, vmax=max(pairs.values())),
            s=10, linewidths=0.22, edgecolors="white",
        )
        hodge.scatter(0, 0, marker="x", color=PRODUCT, s=32, linewidth=1.2, zorder=4)
        hodge.annotate(
            "Product placeholder", (0, 0), (2.1, 4), fontsize=7.3, color=PRODUCT,
            arrowprops={"arrowstyle": "-", "color": PRODUCT, "linewidth": 0.65},
        )
        for name, record_id, label in (("Quintic", 7890, (4.5, 101)),
                                         ("Bicubic", 7884, (5.3, 83))):
            record = catalog.record(record_id)
            hodge.annotate(
                name, (record.h11, record.h21), label, fontsize=8,
                arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.65},
            )
        hodge.set(
            xlim=(-1, 20), ylim=(-4, 108), xlabel=r"$h^{1,1}$", ylabel=r"$h^{2,1}$",
            xticks=(0, 5, 10, 15, 20), yticks=(0, 20, 40, 60, 80, 100),
        )
        hodge.set_title("Recorded Hodge pairs", loc="left", pad=10)
        legend_axis = fig.add_axes([0.115, 0.12, 0.32, 0.028])
        colorbar = fig.colorbar(dots, cax=legend_axis, orientation="horizontal")
        colorbar.set_ticks([1, 10, 100, 300], labels=["1", "10", "100", "300"])
        colorbar.minorticks_off()
        colorbar.set_label("Configurations per pair (log scale)", size=8, color=MUTED)
        colorbar.ax.tick_params(labelsize=7, length=2)
        colorbar.outline.set_linewidth(0.5)

        x = sorted(eulers)
        euler.bar(x, [eulers[value] for value in x], width=1.5, color=TEAL)
        midpoint = median(record.euler for record in records)
        euler.axvline(midpoint, color=INK, linestyle=(0, (3, 3)), lw=0.8)
        euler.annotate(
            f"Median {midpoint:g}", (midpoint, 510), xytext=(-111, 540),
            fontsize=8, arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.65},
        )
        euler.set(
            xlim=(-205, 5), ylim=(0, 670),
            xlabel=r"Euler characteristic $\chi$", ylabel="Configurations",
        )
        euler.xaxis.set_major_locator(FixedLocator([-200, -150, -100, -50, 0]))
        euler.yaxis.set_major_locator(FixedLocator([0, 200, 400, 600]))
        euler.grid(False, axis="x")
        euler.set_title("Euler counts", loc="left", pad=10)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=300, facecolor="white")
        finally:
            plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("manuscript/figures/cicy3-atlas.png"))
    parser.add_argument("--summary", type=Path, help="also write the archived readback summary as JSON")
    args = parser.parse_args()
    plot_atlas(args.output)
    if args.summary is not None:
        write_summary(args.summary)


if __name__ == "__main__":
    main()
