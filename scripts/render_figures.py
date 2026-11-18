#!/usr/bin/env python3
"""Render analytical manuscript figures from the bundled, validated CIPro release."""

import argparse
from contextlib import contextmanager
from collections import Counter
from itertools import accumulate
import json
from math import log10
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import PercentFormatter
import numpy as np

from py_cipro.catalog import get_catalog

from manuscript_analysis import archive_analysis, manuscript_analysis

INK = "#172d42"
MUTED = "#4d6273"
GRID = "#d8e0e6"
TEAL = "#087c76"
PURPLE = "#755391"
ORANGE = "#b85420"
LIGHT = "#e3eaf0"
NEUTRAL = "#536979"


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


@contextmanager
def canvas(title, *, height=3.95, bottom=0.17, widths=(1, 1), spacing=0.36):
    with plt.rc_context({
        "font.family": "DejaVu Sans",
        "font.size": 9,
        "text.color": INK,
        "axes.labelcolor": INK,
        "axes.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": MUTED,
        "axes.linewidth": 0.6,
        "grid.color": GRID,
        "grid.linewidth": 0.55,
        "axes.axisbelow": True,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "mathtext.fontset": "dejavusans",
        "pdf.fonttype": 42,
    }):
        fig, axes = plt.subplots(1, 2, figsize=(7.8, height), gridspec_kw={"width_ratios": widths})
        fig.subplots_adjust(left=0.088, right=0.97, bottom=bottom, top=0.79, wspace=spacing)
        fig.text(0.088, 0.928, title, fontsize=15.5, fontweight="bold", va="top")
        fig.add_artist(Line2D([0.088, 0.97], [0.862, 0.862], transform=fig.transFigure, color=GRID, lw=0.7))
        try:
            yield fig, axes
        finally:
            plt.close(fig)


def _panel(ax, letter, title):
    ax.set_title(f"{letter}   {title}", loc="left", fontsize=10, pad=8)


def _note(ax, text, xy, offset, **kwargs):
    ax.annotate(
        text, xy, textcoords="offset points", xytext=offset, fontsize=7.5, color=INK,
        arrowprops={"arrowstyle": "-", "color": MUTED, "linewidth": 0.65, "shrinkB": 3},
        **kwargs,
    )


def _save(fig, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"Creator": "py-CIPro manuscript analysis", "CreationDate": None, "ModDate": None}
    if path.suffix == ".png":
        metadata = {"Software": "py-CIPro manuscript analysis"}
    fig.savefig(path, dpi=320, facecolor="white", metadata=metadata)


def plot_atlas(path: Path, analysis=None) -> None:
    if analysis is None:
        release = get_catalog()
        analysis = {
            "catalog": archive_analysis(release),
            "fixtures": {"quintic": release.record(7890).summary(), "bicubic": release.record(7884).summary()},
        }
    catalog = analysis["catalog"]
    pairs = sorted(catalog["hodge_pairs"], key=lambda row: row["records"])
    eulers = catalog["euler_counts"]

    with canvas("The CICY threefold archive", height=3.86, bottom=0.25) as (fig, (hodge, euler)):
        hodge.grid(True)
        points = hodge.scatter(
            [row["h11"] for row in pairs], [row["h21"] for row in pairs],
            c=[row["records"] for row in pairs], s=[14 + 9 * log10(row["records"]) for row in pairs],
            cmap="cividis", norm=LogNorm(vmin=1, vmax=max(row["records"] for row in pairs)),
            linewidths=0.25, edgecolors=INK, zorder=2,
        )
        for name, position in (("Quintic", (10, -2)), ("Bicubic", (12, 2))):
            fixture = analysis["fixtures"][name.lower()]
            _note(hodge, name, (fixture["h11"], fixture["h21"]), position)
        modal = pairs[-1]
        _note(hodge, f'({modal["h11"]}, {modal["h21"]}) · {modal["records"]}',
              (modal["h11"], modal["h21"]), (8, 22),
              bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.94, "pad": 1})
        hodge.set(
            xlim=(-0.1, 20), ylim=(12, 107), xlabel=r"$h^{1,1}$", ylabel=r"$h^{2,1}$",
            xticks=(0, 5, 10, 15, 20), yticks=(20, 40, 60, 80, 100),
        )
        _panel(hodge, "A", "Hodge pairs of nonproducts")
        width = hodge.get_position().width
        left = hodge.get_position().x0
        scale = fig.add_axes([left + width * 0.08, 0.105, width * 0.84, 0.022])
        colorbar = fig.colorbar(points, cax=scale, orientation="horizontal")
        colorbar.solids.set_rasterized(False)
        colorbar.set_ticks([1, 4, 16, 64, 256], labels=["1", "4", "16", "64", "256"])
        colorbar.minorticks_off()
        colorbar.set_label("Records per pair (log scale)", fontsize=8)
        colorbar.ax.tick_params(labelsize=7.5, length=2, pad=2)
        colorbar.outline.set_linewidth(0.4)

        x = [row["euler"] for row in eulers]
        nonproducts = [row["nonproducts"] for row in eulers]
        products = [row["products"] for row in eulers]
        euler.bar(x, nonproducts, width=1.7, color=TEAL)
        euler.bar(x, products, bottom=nonproducts, width=1.7, color=ORANGE, hatch="////",
                  edgecolor=INK, linewidth=0.3, zorder=3)
        midpoint = catalog["median_euler"]
        mode = max(eulers, key=lambda row: row["nonproducts"] + row["products"])
        euler.axvline(midpoint, color=NEUTRAL, linestyle=(0, (3, 3)), lw=0.9)
        _note(euler, f'{mode["euler"]} · {mode["nonproducts"] + mode["products"]}',
              (mode["euler"], mode["nonproducts"] + mode["products"]), (-35, 9))
        euler.set(
            xlim=(-204, 5), ylim=(0, 700), xlabel=r"Euler characteristic $\chi$", ylabel="Archive records",
            xticks=(-200, -150, -100, -50, 0), yticks=(0, 200, 400, 600),
        )
        euler.grid(True, axis="y")
        euler.legend(
            handles=[
                Patch(facecolor=TEAL, label="Nonproducts"),
                Patch(facecolor=ORANGE, hatch="////", edgecolor=INK, linewidth=0.3, label="Products"),
                Line2D([0], [0], color=NEUTRAL, lw=0.9, ls=(0, (3, 3)), label="Median"),
            ],
            loc="upper center", bbox_to_anchor=(0.5, -0.17), ncols=3, frameon=False, fontsize=7.5,
            columnspacing=0.9, handlelength=1.45, handletextpad=0.45,
        )
        _panel(euler, "B", "Euler characteristic counts")
        _save(fig, path)


def plot_structure(path: Path, analysis) -> None:
    catalog = analysis["catalog"]
    shapes = catalog["shape_counts"]
    factors = max(row["factors"] for row in shapes)
    codimensions = max(row["codimension"] for row in shapes)
    matrix = np.zeros((codimensions, factors), dtype=int)
    for row in shapes:
        matrix[row["codimension"] - 1, row["factors"] - 1] = row["records"]
    rate_rows = catalog["favourability"]
    positions = [row["factors"] for row in rate_rows]
    fractions = [row["favourable"] / row["records"] for row in rate_rows]

    with canvas("Configuration size and archive favourability", height=4.45, bottom=0.235,
                spacing=0.34) as (fig, (shape, favour)):
        heatmap = shape.pcolormesh(
            np.arange(factors + 1) + .5, np.arange(codimensions + 1) + .5,
            np.ma.masked_equal(matrix, 0), shading="flat",
            cmap="Blues", norm=LogNorm(vmin=1, vmax=matrix.max()),
        )
        shape.set_facecolor("#eff3f6")
        shape.set(
            xlabel="Ambient projective factors", ylabel="Defining equations (codimension)",
            xticks=(1, 3, 5, 7, 9, 11, 12), yticks=(1, 3, 5, 7, 9, 11, 13, 15),
        )
        for row in sorted(shapes, key=lambda row: row["records"], reverse=True)[:3]:
            shape.text(row["factors"], row["codimension"], f'{row["records"]}', ha="center", va="center",
                       fontsize=6.9, color="white", fontweight="bold")
        _panel(shape, "A", "Recorded configuration sizes")
        width = shape.get_position().width
        left = shape.get_position().x0
        scale = fig.add_axes([left + width * 0.07, 0.102, width * 0.86, 0.022])
        colorbar = fig.colorbar(heatmap, cax=scale, orientation="horizontal")
        colorbar.solids.set_rasterized(False)
        colorbar.set_ticks([1, 5, 25, 125, 500], labels=["1", "5", "25", "125", "500"])
        colorbar.minorticks_off()
        colorbar.set_label("Records per cell (log scale)", fontsize=8)
        colorbar.ax.tick_params(labelsize=7.5, length=2, pad=2)
        colorbar.outline.set_linewidth(0.4)

        favour.barh(positions, [1] * len(positions), height=0.62, color=LIGHT)
        favour.barh(positions, fractions, height=0.62, color=TEAL)
        for row in rate_rows:
            favour.text(1.03, row["factors"], f'{row["favourable"]:,}/{row["records"]:,}',
                        fontsize=7.3, va="center", color=MUTED)
        favour.set(
            xlabel="Share of nonproduct records marked Favour", ylabel="Ambient projective factors",
            xlim=(0, 1.34), ylim=(factors + 0.6, 0.4), xticks=(0, 0.25, 0.5, 0.75, 1),
            yticks=positions,
        )
        favour.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        favour.tick_params(axis="both", labelsize=8)
        favour.grid(True, axis="x")
        _panel(favour, "B", "Favour by ambient factors")
        _save(fig, path)


def plot_multiplicity(path: Path, analysis) -> None:
    catalog = analysis["catalog"]
    pairs = catalog["hodge_pairs"]
    ranks = list(range(1, len(pairs) + 1))
    size = catalog["nonproduct_records"]
    share = [count / size for count in accumulate(row["records"] for row in pairs)]
    bins = catalog["multiplicity_bins"]
    bin_labels = [
        f'{row["min"]}+' if row["max"] is None else
        f'{row["min"]}' if row["min"] == row["max"] else f'{row["min"]}–{row["max"]}'
        for row in bins
    ]

    with canvas("How heavily do recorded Hodge pairs repeat?", height=3.95, bottom=0.205) as (fig, axes):
        cumulative, spectrum = axes
        cumulative.plot(ranks, share, color=TEAL, lw=2.2)
        cumulative.plot(ranks, [rank / len(ranks) for rank in ranks], color=NEUTRAL,
                        lw=1.05, ls=(0, (3, 3)), label="Equal record count per pair")
        half_rank = catalog["pairs_to_half"]
        cumulative.scatter([10, half_rank], [share[9], share[half_rank - 1]], s=20, color=TEAL, zorder=3)
        cumulative.axhline(0.5, color=GRID, lw=0.7)
        _note(cumulative, f"10 pairs · {share[9]:.1%}", (10, share[9]), (8, -9))
        _note(cumulative, f"{half_rank} pairs · {share[half_rank - 1]:.1%}",
              (half_rank, share[half_rank - 1]), (8, -6))
        cumulative.set(
            xscale="log", xlabel="Hodge-pair rank (log scale)", ylabel="Cumulative share of records",
            xlim=(1, len(pairs) + 12), ylim=(0, 1.04),
            xticks=(1, 5, 10, half_rank, 50, 100, len(pairs)),
            xticklabels=("1", "5", "10", str(half_rank), "50", "100", str(len(pairs))),
            yticks=(0, 0.25, 0.5, 0.75, 1),
        )
        cumulative.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        cumulative.tick_params(axis="x", labelsize=8)
        cumulative.grid(True, axis="y")
        cumulative.legend(loc="upper left", fontsize=7.5, frameon=False, handlelength=1.9)
        _panel(cumulative, "A", "Concentration by rank")

        counts = [row["pairs"] for row in bins]
        bars = spectrum.bar(range(len(bins)), counts, color=[ORANGE] + [TEAL] * (len(bins) - 1), width=0.72)
        spectrum.bar_label(bars, padding=3, fontsize=8, color=INK)
        spectrum.set(
            xlabel="Configurations per Hodge pair", ylabel="Distinct pairs",
            xticks=range(len(bins)), xticklabels=bin_labels,
            ylim=(0, max(counts) * 1.19),
        )
        spectrum.tick_params(axis="x", labelrotation=35, labelsize=7.7)
        spectrum.grid(True, axis="y")
        _panel(spectrum, "B", "Multiplicity distribution")
        _save(fig, path)


def plot_cohomology(path: Path, analysis) -> None:
    quintic = analysis["cohomology"]["quintic"]
    bicubic = analysis["cohomology"]["bicubic"]
    charges = [row["k"] for row in quintic["rows"]]
    h0 = [row["dimensions"][0] for row in quintic["rows"]]
    h3 = [-row["dimensions"][3] for row in quintic["rows"]]
    index = [row["index"] for row in quintic["rows"]]

    with canvas("Exact line-bundle calculations on two threefolds", height=4.27, bottom=0.23,
                widths=(1.04, 1), spacing=0.39) as (fig, (degree, lattice)):
        degree.axhline(0, color=NEUTRAL, linewidth=0.65)
        degree.plot(charges, index, color=NEUTRAL, lw=0.9, ls=(0, (3, 2)), zorder=1)
        for values, color, marker in ((h0, TEAL, "o"), (h3, PURPLE, "^")):
            samples = [(k, h) for k, h in zip(charges, values) if h]
            degree.scatter(*zip(*samples), marker=marker, color=color, s=21, zorder=2)
        _note(degree, r"$h^0=h^3=1$", (0, 1), (17, 12))
        ticks = (-875, -100, -10, -1, 0, 1, 10, 100, 875)
        degree.set(
            yscale="symlog", xlabel=r"Quintic charge $k$", ylabel="Signed dimension or index",
            xlim=(-10.7, 10.7), ylim=(-1400, 1400), xticks=(-10, -5, 0, 5, 10),
            yticks=ticks, yticklabels=[f"{value}" for value in ticks],
        )
        degree.grid(True, axis="y")
        degree.legend(
            handles=[
                Line2D([0], [0], marker="o", lw=0, color=TEAL, label=r"$h^0$"),
                Line2D([0], [0], marker="^", lw=0, color=PURPLE, label=r"$-h^3$"),
                Line2D([0], [0], color=NEUTRAL, lw=0.9, ls=(0, (3, 2)), label=r"Index $\chi$"),
            ],
            loc="upper center", bbox_to_anchor=(0.5, -0.16), ncols=3, frameon=False, fontsize=8,
            columnspacing=1, handlelength=1.4, handletextpad=0.45,
        )
        _panel(degree, "A", "Quintic dimensions and index")

        lower, upper = bicubic["charge_range_per_axis"]
        marker_styles = {
            "unsupported": {"marker": "x", "color": "#8697a4", "linewidths": 0.7},
            "acyclic": {"marker": "s", "facecolors": "white", "edgecolors": INK, "linewidths": 0.85},
            "h0_only": {"marker": "o", "color": TEAL, "linewidths": 0},
            "h3_only": {"marker": "^", "color": PURPLE, "linewidths": 0},
        }
        for status, style in marker_styles.items():
            sample = [row for row in bicubic["rows"] if row["status"] == status]
            lattice.scatter(
                [row["a"] for row in sample], [row["b"] for row in sample],
                s=[6 + 9 * log10(sum(row["dimensions"])) if status in {"h0_only", "h3_only"} else 10
                   for row in sample],
                **style,
            )
        lattice.axhline(0, color=GRID, linewidth=0.8, zorder=0)
        lattice.axvline(0, color=GRID, linewidth=0.8, zorder=0)
        lattice.set(
            aspect="equal", xlim=(lower - 0.55, upper + 0.55), ylim=(lower - 0.55, upper + 0.55),
            xticks=(lower, -4, 0, 4, upper), yticks=(lower, -4, 0, 4, upper),
            xlabel=r"Bicubic charge $a$", ylabel=r"Bicubic charge $b$",
        )
        lattice.legend(
            handles=[
                Line2D([0], [0], marker="o", lw=0, color=TEAL, label=r"$H^0$ only"),
                Line2D([0], [0], marker="^", lw=0, color=PURPLE, label=r"$H^3$ only"),
                Line2D([0], [0], marker="s", lw=0, color=INK, markerfacecolor="white", label="Acyclic"),
                Line2D([0], [0], marker="x", lw=0, color="#8697a4", label="Unsupported"),
            ],
            loc="upper center", bbox_to_anchor=(0.5, -0.16), ncols=2, frameon=False, fontsize=7.8,
            columnspacing=1, handlelength=1.4, handletextpad=0.45,
        )
        _panel(lattice, "B", "Bicubic native coverage")
        _save(fig, path)


FIGURES = {
    "cicy3-atlas": plot_atlas,
    "cicy3-structure": plot_structure,
    "cicy3-multiplicity": plot_multiplicity,
    "line-bundle-cohomology": plot_cohomology,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("manuscript/figures/cicy3-atlas.png"),
                        help="single atlas output (PNG or PDF)")
    parser.add_argument("--summary", type=Path, help="also write the archived readback summary as JSON")
    parser.add_argument("--suite", action="store_true", help="render all manuscript figures and write the analysis JSON")
    parser.add_argument("--format", choices=("png", "pdf"), default="png", help="file format for the figure suite")
    parser.add_argument("--figures-dir", type=Path, default=Path("manuscript/figures"), help="suite figure directory")
    parser.add_argument("--data-dir", type=Path, default=Path("data"), help="suite analysis JSON directory")
    args = parser.parse_args()
    if args.suite:
        analysis = manuscript_analysis()
        for name, plot in FIGURES.items():
            plot(args.figures_dir / f"{name}.{args.format}", analysis)
        args.data_dir.mkdir(parents=True, exist_ok=True)
        (args.data_dir / "manuscript-analysis.json").write_text(
            json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
    else:
        plot_atlas(args.output)
    if args.summary is not None:
        write_summary(args.summary)


if __name__ == "__main__":
    main()
