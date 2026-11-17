#!/usr/bin/env python3
"""Render the manuscript's compact graphical abstract from its study data."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
STUDIES = ("chern-audit", "atlas-comparison", "bicubic-exact", "integral-invariants")
FIGSIZE = (7.0, 3.8)
INK = "#172a3a"
MUTED = "#486173"
PALE = "#e0e8ed"
TEAL = "#087267"
PURPLE = "#755299"
ORANGE = "#96471c"


def load_studies(directory):
    raw = {name: (directory / f"{name}.json").read_bytes() for name in STUDIES}
    studies = {name: json.loads(data) for name, data in raw.items()}
    archive_ids = {
        (record["archive_sha256"], record["dataset_sha256"]) for record in studies.values()
    }
    if len(archive_ids) != 1:
        raise ValueError("The cover studies must use the same archived CICY3 inputs.")
    return studies, {name: sha256(data).hexdigest() for name, data in raw.items()}


def minus(number):
    return str(number).replace("-", "−")


def rounded_box(fig, x, y, width, height, color, edge="none"):
    fig.add_artist(FancyBboxPatch(
        (x, y), width, height, transform=fig.transSubfigure,
        boxstyle="round,pad=0,rounding_size=.015",
        facecolor=color, edgecolor=edge, linewidth=.65, zorder=0,
    ))


def text(fig, x, y, label, size, *, color=INK, weight="normal", **options):
    return fig.text(x, y, label, fontsize=size, color=color, weight=weight, **options)


def panel(fig, x, accent, title, metric, description):
    rounded_box(fig, x, .032, .31, .728, "#f8fafb", "#d9e3e9")
    text(fig, x + .02, .719, title, 8.9, color=accent, weight="bold", va="center")
    text(fig, x + .019, .632, metric, 18, weight="bold", va="center")
    text(fig, x + .02, .532, description, 7.0, color=MUTED, va="center", linespacing=1.35)


def axes_style(ax):
    ax.set_facecolor("#f8fafb")
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=PALE, linewidth=.55)
    ax.tick_params(length=2, width=.6, pad=2, labelsize=5.9, colors=MUTED)
    ax.spines[["top", "right"]].set_visible(False)
    for name in ("left", "bottom"):
        ax.spines[name].set_color("#9aacb8")
        ax.spines[name].set_linewidth(.6)
    ax.xaxis.label.set_color(MUTED)
    ax.yaxis.label.set_color(MUTED)


def geometry(fig, x, data):
    summary = data["summary"]
    rows = data["rows"]
    if (len(rows) != summary["records"] or data["mismatches"]
            or summary["matched_records"] != len(rows)
            or sum(len(row["c2"]) for row in rows) != summary["ambient_pairings"]):
        raise ValueError("The Chern audit counts do not match its record data.")
    modal = summary["modal_hodge"]
    points = Counter((row["volume"], row["c2_polarized"]) for row in rows
                     if not row["product"] and row["hodge"] == modal)
    if not points or len(points) != summary["modal_signatures"]:
        raise ValueError("The modal Hodge group does not match the Chern audit.")
    panel(fig, x, TEAL, "Chern pairing audit", f"{summary['ambient_pairings']:,}",
          f"Second Chern pairings recovered\nacross {summary['records']:,} configurations")

    ax = fig.add_axes([x + .064, .232, .217, .216])
    axes_style(ax)
    cloud = sorted(points, key=points.get, reverse=True)
    volumes, pairings = zip(*cloud, strict=True)
    ax.scatter(volumes, pairings, c=TEAL, s=[3 + 2 * points[p] ** .5 for p in cloud],
               alpha=.60, linewidths=0, zorder=3)
    for key in ("modal_low_id", "modal_high_id"):
        row = rows[summary[key] - 1]
        ax.scatter(row["volume"], row["c2_polarized"], s=22, facecolor="#f8fafb",
                   edgecolor=ORANGE, linewidth=.95, zorder=4)
    ax.margins(x=.10, y=.16)
    ax.set_xticks([500, 1000, 1500, 2000])
    ax.set_yticks([150, 200, 250, 300])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.set_xlabel("Polarized degree V", fontsize=6.1, labelpad=2)
    ax.set_ylabel("Chern pairing T", fontsize=6.1, labelpad=2)
    text(fig, x + .155, .087,
         f"{len(points):,} distinct (V, T) at Hodge pair ({modal[0]}, {modal[1]})",
         6.4, color=MUTED, ha="center", va="center")


def weighting(fig, x, data):
    medians = data["summary"]["median_euler"]
    population = data["population"]
    cdf = data["euler_cdf"]
    groups = (
        ("presentation", "record_count_le", "non_product_presentations", TEAL, "-", "Per record"),
        ("equal_pair", "pair_count_le", "distinct_non_product_hodge_pairs", PURPLE, "--", "Per Hodge pair"),
    )
    panel(fig, x, PURPLE, "Catalog weighting",
          f"{minus(medians['presentation'])} → {minus(medians['equal_pair'])}",
          "Median Euler characteristic\nunder two exact weighting rules")

    ax = fig.add_axes([x + .061, .232, .22, .216])
    axes_style(ax)
    threshold = [row["euler"] for row in cdf]
    ax.axhline(.5, color="#a8b4be", linewidth=.6, zorder=1)
    for median_key, count_key, total_key, color, style, _ in groups:
        total = population[total_key]
        if cdf[-1][count_key] != total:
            raise ValueError("The weighted Euler distribution does not end at its population.")
        median_index = next(i for i, point in enumerate(cdf) if point[count_key] * 2 >= total)
        if threshold[median_index] != medians[median_key]:
            raise ValueError("The reported Euler median does not match its cumulative distribution.")
        share = [row[count_key] / total for row in cdf]
        ax.step(threshold, share, where="post", color=color, linewidth=1.25, linestyle=style, zorder=3)
        ax.plot(medians[median_key], share[median_index], marker="o", color=color,
                markeredgecolor="white", markeredgewidth=.55, markersize=4, zorder=4)
    ax.set_xlim(threshold[0] - 5, threshold[-1] + 4)
    ax.set_ylim(-.03, 1.06)
    ax.set_xticks([-200, -100, 0])
    ax.set_yticks([0, .5, 1], ["0%", "50%", "100%"])
    ax.set_xlabel("Euler characteristic χ", fontsize=6.1, labelpad=2)
    ax.set_ylabel("Cumulative share", fontsize=6.1, labelpad=2)
    handles = [Line2D([], [], color=color, linestyle=style, label=label, linewidth=1.35)
               for _, _, _, color, style, label in groups]
    legend = fig.legend(handles=handles, loc="center", bbox_to_anchor=(x + .156, .087),
                        frameon=False, ncols=2, fontsize=6.3, handlelength=1.4,
                        columnspacing=1, handletextpad=.35)
    for label in legend.get_texts():
        label.set_color(MUTED)


def bicubic(fig, x, data):
    summary = data["summary"]
    low, high = data["charge_range_per_axis"]
    values = {(row["a"], row["b"]): row["paired_excess"] for row in data["rows"]}
    grid = list(range(low, high + 1))
    if (len(values) != summary["points"] or len(values) != len(grid) ** 2
            or sum(value > 0 for value in values.values()) != summary["jumping_points"]):
        raise ValueError("The cohomology grid does not match its summary.")
    panel(fig, x, ORANGE, "Bicubic cohomology",
          f"{summary['jumping_points']:,} of {summary['points']:,}",
          "Charge pairs with a jump on the\nspecified smooth bicubic")

    ax = fig.add_axes([x + .075, .226, .133, .244])
    axes_style(ax)
    ax.grid(False)
    excess = [[values[a, b] for a in grid] for b in grid]
    color = LinearSegmentedColormap.from_list("jump", ["#edf0f2", "#e59d6e", "#813b24"])
    edges = [point - .5 for point in range(low, high + 2)]
    maximum = max(values.values())
    if maximum != summary["max_paired_excess"] or values[3, -3] != summary["witness_paired_excess"]:
        raise ValueError("The cohomology grid does not match its reported maximum and witness.")
    image = ax.pcolormesh(edges, edges, excess, vmin=0, vmax=maximum,
                          cmap=color, shading="flat", antialiased=False)
    ax.set_aspect("equal")
    ax.plot([low, high], [high, low], color="#6e5149", alpha=.85,
            linewidth=.55, linestyle="--")
    ax.scatter(3, -3, s=19, facecolors="none", edgecolors=INK, linewidths=.75, zorder=4)
    ax.set_xticks([low, 0, high])
    ax.set_yticks([low, 0, high])
    ax.set_xlabel("Charge a", fontsize=6.1, labelpad=2)
    ax.set_ylabel("Charge b", fontsize=6.1, labelpad=2)
    cax = fig.add_axes([x + .218, .248, .012, .185])
    bar = fig.colorbar(image, cax=cax, ticks=[0, maximum])
    bar.solids.set_rasterized(False)
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, pad=2, labelsize=5.8, colors=MUTED)
    text(fig, x + .155, .087, "Excess dimension in each middle degree",
         6.4, color=MUTED, ha="center", va="center")


def integral_split(fig, split, total):
    rounded_box(fig, .02, .12, .96, .76, "#eef4f4", "#d2e0e1")
    text(fig, .039, .5, f"{split:,} of {total:,}", 10.8, color=TEAL, weight="bold", va="center")
    text(fig, .189, .5, "Non-product Hodge groups split by two ambient lattice gcd invariants",
         7.55, color=INK, va="center")
    for width, color in ((.14, "#ccdade"), (.14 * split / total, TEAL)):
        fig.add_artist(Rectangle((.815, .40), width, .20, transform=fig.transSubfigure,
                                 facecolor=color, edgecolor="none", zorder=1))


def integral_totals(data, atlas, chern):
    joint_by_hodge = defaultdict(set)
    records = {}
    for row in data["rows"]:
        hodge = tuple(row["hodge"])
        records[row["id"]] = hodge
        joint_by_hodge[hodge].add((row["cubic_content"], row["chern_content"]))
    non_product = {row["id"]: tuple(row["hodge"]) for row in chern["rows"] if not row["product"]}
    population = atlas["population"]
    split = sum(len(joint) > 1 for joint in joint_by_hodge.values())
    total = len(joint_by_hodge)
    summary = data["summary"]
    if (records != non_product or len(data["rows"]) != len(records)
            or len(records) != summary["records"]
            or len(records) != population["non_product_presentations"]
            or total != population["distinct_non_product_hodge_pairs"]
            or (split, total) != (summary["split_hodge_groups"], summary["hodge_groups"])):
        raise ValueError("The integral-invariant audit does not match its reported non-product cohort.")
    return split, total


def render(studies, pdf, png):
    chern = studies["chern-audit"]
    atlas = studies["atlas-comparison"]
    split, total = integral_totals(studies["integral-invariants"], atlas, chern)
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42}):
        fig = Figure(figsize=FIGSIZE, facecolor="white")
        body, footer = fig.subfigures(2, 1, height_ratios=[3.50, .30], hspace=0)
        rounded_box(body, .02, .794, .96, .188, INK)
        text(body, .047, .915, "Exact studies of CICY threefolds", 16,
             color="white", weight="bold", va="center")
        text(body, .048, .835, "Archived configurations, catalog weights, and a specified smooth bicubic",
             7.4, color="#cfdee8", va="center")
        geometry(body, .02, chern)
        weighting(body, .345, atlas)
        bicubic(body, .67, studies["bicubic-exact"])
        integral_split(footer, split, total)
        pdf.parent.mkdir(parents=True, exist_ok=True)
        png.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(pdf, format="pdf", metadata={
            "Title": "py-CIPro graphical abstract",
            "Creator": "py-CIPro",
            "CreationDate": None,
            "ModDate": None,
        })
        fig.savefig(png, format="png", dpi=300, metadata={"Software": "py-CIPro"})


def render_graphical_abstract(data_dir: Path, pdf: Path, png: Path) -> dict:
    """Render both cover formats and return the size and data bindings."""
    if pdf.resolve() == png.resolve():
        raise ValueError("The PDF and PNG outputs require distinct paths.")
    studies, inputs = load_studies(data_dir)
    render(studies, pdf, png)
    return {"data_sha256": inputs, "size_inches": FIGSIZE, "pdf": str(pdf), "png": str(png)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--pdf", type=Path, default=ROOT / "output/cover/graphical-abstract.pdf")
    parser.add_argument("--png", type=Path, default=ROOT / "output/cover/graphical-abstract.png")
    args = parser.parse_args()
    print(json.dumps(render_graphical_abstract(args.data_dir, args.pdf, args.png), sort_keys=True))


if __name__ == "__main__":
    main()
