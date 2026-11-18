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
from matplotlib.patches import FancyBboxPatch
from matplotlib.ticker import FuncFormatter


ROOT = Path(__file__).resolve().parents[1]
STUDIES = ("chern-audit", "atlas-comparison", "bicubic-exact", "integral-invariants", "cubic-refinement")
FIGSIZE = (7.0, 4.7)
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
    digests = {name: sha256(data).hexdigest() for name, data in raw.items()}
    if studies["cubic-refinement"]["integral_receipt_sha256"] != digests["integral-invariants"]:
        raise ValueError("The cubic refinement must bind this integral-invariants receipt.")
    return studies, digests


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


def panel(fig, x, y, accent, title, metric, description):
    rounded_box(fig, x, y, .465, .35, "#f8fafb", "#d9e3e9")
    text(fig, x + .021, y + .308, title, 9.0, color=accent, weight="bold", va="center")
    text(fig, x + .021, y + .218, metric, 16.4, weight="bold", va="center")
    text(fig, x + .022, y + .146, description, 7.2, color=MUTED, va="center", linespacing=1.36)


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


def geometry(fig, x, y, data):
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
    panel(fig, x, y, TEAL, "Chern pairing audit", f"{summary['ambient_pairings']:,}",
          f"Second Chern pairings\non {summary['records']:,} archive records")

    ax = fig.add_axes([x + .247, y + .097, .195, .168])
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
    ax.set_xticks([500, 1250, 2000])
    ax.set_yticks([150, 225, 300])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.0f}"))
    ax.set_xlabel("Polarized degree V", fontsize=6.1, labelpad=2)
    text(fig, x + .247, y + .281, "Chern pairing T", 6.1, color=MUTED, va="center")
    text(fig, x + .022, y + .032,
         f"{len(points):,} distinct pairs at Hodge ({modal[0]}, {modal[1]})",
         6.7, color=MUTED, va="center")


def weighting(fig, x, y, data):
    medians = data["summary"]["median_euler"]
    population = data["population"]
    cdf = data["euler_cdf"]
    groups = (
        ("presentation", "record_count_le", "non_product_presentations", TEAL, "-", "Per record"),
        ("equal_pair", "pair_count_le", "distinct_non_product_hodge_pairs", PURPLE, "--", "Per Hodge pair"),
    )
    panel(fig, x, y, PURPLE, "Catalogue weighting",
          f"{minus(medians['presentation'])} → {minus(medians['equal_pair'])}",
          "Median Euler\ncharacteristic by weight")

    ax = fig.add_axes([x + .247, y + .097, .195, .168])
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
    text(fig, x + .247, y + .281, "Cumulative share", 6.1, color=MUTED, va="center")
    handles = [Line2D([], [], color=color, linestyle=style, label=label, linewidth=1.35)
               for _, _, _, color, style, label in groups]
    legend = fig.legend(handles=handles, loc="center left", bbox_to_anchor=(x + .018, y + .033),
                        frameon=False, ncols=2, fontsize=6.3, handlelength=1.4,
                        columnspacing=1, handletextpad=.35)
    for label in legend.get_texts():
        label.set_color(MUTED)


def bicubic(fig, x, y, data):
    summary = data["summary"]
    low, high = data["charge_range_per_axis"]
    values = {(row["a"], row["b"]): row["paired_excess"] for row in data["rows"]}
    grid = list(range(low, high + 1))
    if (len(values) != summary["points"] or len(values) != len(grid) ** 2
            or sum(value > 0 for value in values.values()) != summary["jumping_points"]):
        raise ValueError("The cohomology grid does not match its summary.")
    panel(fig, x, y, ORANGE, "Bicubic cohomology",
          f"{summary['jumping_points']:,} of {summary['points']:,}",
          "Charge pairs with a jump\non one smooth bicubic")

    ax = fig.add_axes([x + .237, y + .099, .176, .170])
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
    cax = fig.add_axes([x + .404, y + .110, .015, .148])
    bar = fig.colorbar(image, cax=cax, ticks=[0, maximum])
    bar.solids.set_rasterized(False)
    bar.outline.set_visible(False)
    bar.ax.tick_params(length=0, pad=2, labelsize=5.8, colors=MUTED)
    text(fig, x + .022, y + .035, "Extra classes in H¹ and H²",
         6.7, color=MUTED, va="center")


def integral_totals(data, refinement, atlas, chern):
    pairs_by_hodge = defaultdict(set)
    refined_by_hodge = defaultdict(set)
    original = {}
    for row in data["rows"]:
        hodge = tuple(row["hodge"])
        pair = row["cubic_content"], row["chern_content"]
        original[row["id"]] = hodge, pair
        pairs_by_hodge[hodge].add(pair)
    for row in refinement["rows"]:
        hodge, pair = original[row["id"]]
        signature = row["d1"], row["d2"], row["d3"], row["dp"]
        if (signature[0], signature[3]) != pair:
            raise ValueError("A refined signature has changed its original integral cell.")
        refined_by_hodge[hodge].add(signature)
    non_product = {row["id"]: tuple(row["hodge"]) for row in chern["rows"] if not row["product"]}
    population = atlas["population"]
    split = sum(len(joint) > 1 for joint in pairs_by_hodge.values())
    refined = sum(len(joint) > 1 for joint in refined_by_hodge.values())
    total = len(pairs_by_hodge)
    pairs = len(set().union(*pairs_by_hodge.values()))
    quadruples = len(set().union(*refined_by_hodge.values()))
    summary = data["summary"]
    refinement_summary = refinement["summary"]
    if ({key: hodge for key, (hodge, _) in original.items()} != non_product
            or len(data["rows"]) != len(original)
            or len(original) != summary["records"]
            or len(original) != population["non_product_presentations"]
            or total != population["distinct_non_product_hodge_pairs"]
            or (split, total) != (summary["split_hodge_groups"], summary["hodge_groups"])
            or {row["id"] for row in refinement["rows"]} != original.keys()
            or len(refinement["rows"]) != len(original)
            or (pairs, quadruples, split, refined, total) != (
                refinement_summary["joint_pairs"], refinement_summary["joint_quadruples"],
                refinement_summary["split_by_pair"], refinement_summary["split_by_quadruple"],
                refinement_summary["hodge_groups"],
            )):
        raise ValueError("The integral-invariant audit does not match its reported non-product cohort.")
    return pairs, quadruples, split, refined, total


def integral_panel(fig, x, y, counts):
    pairs, quadruples, split, refined, total = counts
    panel(fig, x, y, TEAL, "Integral cubic refinement",
          f"{pairs:,} → {quadruples:,}", "Ambient signatures\nwith two added cubic gcds")
    ax = fig.add_axes([x + .247, y + .103, .180, .151])
    ax.set_xlim(0, total)
    ax.set_ylim(-.5, 1.5)
    ax.set_axis_off()
    ax.barh([1, 0], [total, total], height=.34, color="#dfe8ed", linewidth=0)
    ax.barh([1, 0], [split, refined], height=.34, color=["#587288", TEAL], linewidth=0)
    for row, value, label in ((1, split, "Pair"), (0, refined, "Four")):
        ax.text(3, row + .27, label, fontsize=6.8, color=MUTED, va="bottom")
        ax.text(value + 5, row, f"{value}", fontsize=7.0, color=INK, va="center")
    text(fig, x + .022, y + .045, f"Hodge groups split out of {total}", 6.7, color=MUTED, va="center")


def render(studies, pdf, png):
    chern = studies["chern-audit"]
    atlas = studies["atlas-comparison"]
    counts = integral_totals(studies["integral-invariants"], studies["cubic-refinement"], atlas, chern)
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42}):
        fig = Figure(figsize=FIGSIZE, facecolor="white")
        rounded_box(fig, .02, .825, .96, .158, INK)
        text(fig, .045, .930, "Exact studies of CICY threefolds", 16.0,
             color="white", weight="bold", va="center")
        text(fig, .046, .867, "Configurations, catalogue weights, cohomology, and integral divisor lattices",
             7.8, color="#cfdee8", va="center")
        geometry(fig, .02, .454, chern)
        weighting(fig, .515, .454, atlas)
        bicubic(fig, .02, .077, studies["bicubic-exact"])
        integral_panel(fig, .515, .077, counts)
        text(fig, .022, .035, "CIPro v1.0 archive · Exact native Python calculations", 7.2, color=MUTED, va="center")
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
