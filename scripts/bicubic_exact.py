#!/usr/bin/env python3
"""Compute and plot exact cohomology dimensions on a specified smooth bicubic."""

import argparse
from hashlib import sha256
import json
from pathlib import Path

from py_cipro._research_bicubic import (
    COEFFICIENTS,
    GENERIC_REFERENCE,
    bicubic_study_row,
    smoothness_minors,
)


ROOT = Path(__file__).resolve().parents[1]


def analysis(reference_path):
    reference_bytes = reference_path.read_bytes()
    prior = json.loads(reference_bytes)
    baseline = prior["cohomology"]["bicubic"]
    rows = []
    for native in baseline["rows"]:
        a, b = native["a"], native["b"]
        supported = native["dimensions"] is not None
        row = bicubic_study_row(a, b, supported)
        if native["index"] != row["index"]:
            raise ValueError(f"Index mismatch at {(a, b)}")
        if supported and native["dimensions"] != row["h"]:
            raise ValueError(f"Exact cohomology disagrees with native Python at {(a, b)}")
        rows.append(row)
    by_charge = {(row["a"], row["b"]): row for row in rows}
    lower, upper = baseline["charge_range_per_axis"]
    if set(by_charge) != {(a, b) for a in range(lower, upper + 1) for b in range(lower, upper + 1)}:
        raise ValueError("The native receipt does not cover the claimed charge square")
    for (a, b), row in by_charge.items():
        if row["h"] != by_charge[-a, -b]["h"][::-1]:
            raise ValueError(f"Serre duality mismatch at {(a, b)}")
    witness = by_charge[3, -3]
    if witness["ambient_h2"] != [10, 10] or witness["rank_h2"] != 3:
        raise ValueError("The matrix-rank witness disagrees with the analytic rank proof")
    maximum = max(rows, key=lambda row: row["h"][1] + row["h"][2])
    return {
        "archive_sha256": prior["catalog"]["archive_sha256"],
        "dataset_sha256": prior["catalog"]["dataset_sha256"],
        "native_receipt_sha256": sha256(reference_bytes).hexdigest(),
        "record": baseline["record"],
        "charge_range_per_axis": [lower, upper],
        "coefficient_matrix": COEFFICIENTS,
        "equation": "sum A[i,j] * x[i]^3 * y[j]^3",
        "square_minor_determinants": smoothness_minors(),
        "generic_reference": GENERIC_REFERENCE,
        "summary": {
            "points": len(rows),
            "native_supported_matches": sum(row["native_supported"] for row in rows),
            "native_unsupported_resolved": sum(not row["native_supported"] for row in rows),
            "native_index_matches": len(rows),
            "mixed_nonzero": sum(row["a"] * row["b"] < 0 and bool(row["h"][1] + row["h"][2]) for row in rows),
            "jumping_points": sum(row["paired_excess"] > 0 for row in rows),
            "max_intermediate_total": maximum["h"][1] + maximum["h"][2],
            "max_intermediate_charge": [maximum["a"], maximum["b"]],
            "max_paired_excess": max(row["paired_excess"] for row in rows),
            "witness_paired_excess": witness["paired_excess"],
        },
        "rows": rows,
    }


def plot(output, result):
    if output.suffix not in (".png", ".pdf"):
        raise ValueError("The figure path must end in .png or .pdf")
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import AsinhNorm, LinearSegmentedColormap
    from matplotlib.lines import Line2D
    import numpy as np

    ink, secondary, grid = "#172d42", "#4d6273", "#d8e0e6"
    teal, purple, gold = "#087c76", "#755391", "#a65320"
    ramp = LinearSegmentedColormap.from_list("bicubic_excess", ("#f3f6f8", "#8ab9be", "#12616c", "#17344b"))
    lower, upper = result["charge_range_per_axis"]
    edges = np.arange(lower, upper + 2) - .5
    width = upper - lower + 1
    excess = np.zeros((width, width), dtype=int)
    row_by_charge = {}
    for row in result["rows"]:
        a, b = row["a"], row["b"]
        excess[b - lower, a - lower] = row["paired_excess"]
        row_by_charge[a, b] = row
    largest = result["summary"]["max_paired_excess"]
    normalization = AsinhNorm(linear_width=3, vmin=0, vmax=largest)
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 9, "text.color": ink,
                         "axes.labelcolor": ink, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": secondary, "xtick.color": secondary, "ytick.color": secondary,
                         "axes.axisbelow": True, "grid.color": grid, "grid.linewidth": .55, "pdf.fonttype": 42}):
        fig, (left, right) = plt.subplots(1, 2, figsize=(8.1, 4.05), gridspec_kw={"width_ratios": (1, 1.12)})
        fig.subplots_adjust(left=.09, right=.973, bottom=.245, top=.755, wspace=.48)
        fig.text(.088, .947, "Cohomology jumps at fixed index",
                 fontweight="bold", fontsize=16, va="top")
        fig.text(.088, .869, "A specified smooth bicubic compared with the published generic dimensions",
                 fontsize=9, color=secondary, va="top")
        fig.add_artist(Line2D([.088, .973], [.825, .825], transform=fig.transFigure, color=grid, lw=.7))
        left.set_title("A   Excess in each middle degree", loc="left", fontsize=10, fontweight="bold", pad=8)
        mesh = left.pcolormesh(edges, edges, excess, shading="flat", cmap=ramp, norm=normalization)
        left.set_aspect("equal")
        left.axhline(0, color=secondary, lw=.55, alpha=.5)
        left.axvline(0, color=secondary, lw=.55, alpha=.5)
        left.plot([lower, upper], [upper, lower], linestyle="--", color=gold, linewidth=1)
        left.scatter(3, -3, color="white", edgecolor=gold, linewidth=1.7, s=38, zorder=4)
        left.set(xlabel="Charge a", ylabel="Charge b", xticks=range(lower, upper + 1, 4), yticks=range(lower, upper + 1, 4))
        key_axis = fig.add_axes((.135, .105, .275, .026))
        key = fig.colorbar(mesh, cax=key_axis, orientation="horizontal")
        key.solids.set_rasterized(False)
        ticks = sorted({0, 7, round(largest / 3), largest})
        key.set_ticks(ticks, labels=[str(tick) for tick in ticks])
        key.minorticks_off()
        key.outline.set_visible(False)
        key.set_label("Additional classes in each of H¹ and H²", fontsize=8, labelpad=3)

        right.set_title("B   Cancellation along b = −a", loc="left", fontsize=10, fontweight="bold", pad=8)
        charges = np.arange(1, upper + 1)
        h1 = [row_by_charge[int(a), -int(a)]["h"][1] for a in charges]
        h2 = [row_by_charge[int(a), -int(a)]["h"][2] for a in charges]
        right.bar(charges, h2, color=teal, width=.69, label="H² contributes +h²")
        right.bar(charges, [-size for size in h1], color=purple, width=.69, label="H¹ contributes −h¹")
        right.axhline(0, color=ink, linewidth=.95, linestyle="--")
        right.grid(axis="y")
        right.set(xlabel="Charge a along the dashed slice", ylabel="Signed contribution to the index", xticks=charges)
        right.legend(loc="lower center", bbox_to_anchor=(.5, -.36), ncols=2, frameon=False, fontsize=7.8)
        right.annotate(f"{h2[2]} in each degree\nat (3, −3)", (3, h2[2]), xytext=(-39, 33), textcoords="offset points",
                       color=gold, fontsize=8, ha="left",
                       arrowprops={"arrowstyle": "-", "color": gold, "lw": .8, "shrinkB": 3})
        output.parent.mkdir(parents=True, exist_ok=True)
        metadata = ({"Software": "py-CIPro bicubic analysis"} if output.suffix == ".png" else
                    {"Creator": "py-CIPro bicubic analysis", "CreationDate": None, "ModDate": None})
        fig.savefig(output, dpi=320, facecolor="white", metadata=metadata)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, default=ROOT / "data" / "manuscript-analysis.json")
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "bicubic-exact.json")
    parser.add_argument("--figure", type=Path, default=ROOT / "docs/manuscript" / "figures" / "bicubic-exact.png")
    args = parser.parse_args()
    result = analysis(args.reference)
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plot(args.figure, result)
    print(json.dumps(result["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
