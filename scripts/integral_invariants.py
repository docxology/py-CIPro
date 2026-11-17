#!/usr/bin/env python3
"""Audit cubic and second Chern content in the released ambient divisor lattices."""

import argparse
from collections import Counter, defaultdict
import json
from math import prod
from pathlib import Path

from py_cipro._research_integral import integral_invariants
from py_cipro.catalog import _cicy3_source_rows, get_catalog


WITNESS_IDS = (7878, 7879)


def cohort_cells(groups):
    return [
        {
            "cubic_content": g3,
            "chern_content": g2,
            "count": len(ids),
            "record_ids": ids,
        }
        for (g3, g2), ids in sorted(groups.items())
    ]


def compute_integral_invariants():
    catalog = get_catalog()
    rows = []
    joint = defaultdict(list)
    hodge = defaultdict(lambda: defaultdict(list))
    euler = defaultdict(lambda: defaultdict(list))
    witness = []

    for record, source in zip(catalog.records, _cicy3_source_rows(), strict=True):
        if record.product:
            continue
        row = integral_invariants(record, source)
        rows.append(row)
        pair = (row["cubic_content"], row["chern_content"])
        joint[pair].append(record.id)
        hodge[tuple(row["hodge"])][pair].append(record.id)
        euler[row["euler"]][pair].append(record.id)
        if record.id in WITNESS_IDS:
            dimension, = record.ambient_dimensions
            degrees, = record.configuration
            if min(degrees) <= 0 or dimension - len(degrees) != 3 or sum(degrees) != dimension + 1:
                raise ValueError(f"Rank-one ample witness has invalid degrees for record {record.id}")
            if row["cubic_content"] != prod(degrees):
                raise ValueError(f"Cubic content disagrees with the product of degrees for record {record.id}")
            c2_numerator = sum(degree**2 for degree in degrees) - (dimension + 1)
            if 2 * row["chern_content"] != c2_numerator * prod(degrees):
                raise ValueError(f"Chern content disagrees with the projective formula for record {record.id}")
            witness.append({**row, "ambient_dimension": dimension, "degrees": list(degrees)})

    if tuple(item["id"] for item in witness) != WITNESS_IDS:
        raise ValueError("Missing an integral-lattice witness")
    first, second = witness
    if first["hodge"] != second["hodge"] or first["euler"] != second["euler"]:
        raise ValueError("Integral-lattice witnesses no longer have the same Hodge and Euler data")
    if first["cubic_content"] == second["cubic_content"]:
        raise ValueError("Integral-lattice witnesses no longer have different cubic content")

    modal = min(hodge, key=lambda pair: (-sum(map(len, hodge[pair].values())), pair))
    summary = {
        "records": len(rows),
        "joint_pairs": len(joint),
        "cubic_contents": len({g3 for g3, _ in joint}),
        "chern_contents": len({g2 for _, g2 in joint}),
        "hodge_groups": len(hodge),
        "split_hodge_groups": sum(len(cells) > 1 for cells in hodge.values()),
        "euler_groups": len(euler),
        "split_euler_groups": sum(len(cells) > 1 for cells in euler.values()),
        "c2_pairings_checked": sum(row["ambient_factors"] for row in rows),
        "pairwise_congruences_checked": sum(
            row["ambient_factors"] * (row["ambient_factors"] - 1) // 2 for row in rows
        ),
        "modal_hodge": list(modal),
        "modal_records": sum(map(len, hodge[modal].values())),
        "modal_pairs": len(hodge[modal]),
        "witness_count": len(witness),
    }
    variables = {
        "INTEGRAL_RECORD_COUNT": f"{summary['records']:,}",
        "INTEGRAL_PAIR_COUNT": str(summary["joint_pairs"]),
        "INTEGRAL_CUBIC_CONTENTS": str(summary["cubic_contents"]),
        "INTEGRAL_CHERN_CONTENTS": str(summary["chern_contents"]),
        "INTEGRAL_HODGE_SPLIT": str(summary["split_hodge_groups"]),
        "INTEGRAL_HODGE_GROUPS": str(summary["hodge_groups"]),
        "INTEGRAL_EULER_SPLIT": str(summary["split_euler_groups"]),
        "INTEGRAL_EULER_GROUPS": str(summary["euler_groups"]),
        "INTEGRAL_C2_CHECKS": f"{summary['c2_pairings_checked']:,}",
        "INTEGRAL_PAIRWISE_CHECKS": f"{summary['pairwise_congruences_checked']:,}",
        "INTEGRAL_MODAL_HODGE": f"({modal[0]},{modal[1]})",
        "INTEGRAL_MODAL_RECORDS": f"{summary['modal_records']:,}",
        "INTEGRAL_MODAL_PAIRS": str(summary["modal_pairs"]),
        "INTEGRAL_WITNESS_FIRST_ID": str(first["id"]),
        "INTEGRAL_WITNESS_SECOND_ID": str(second["id"]),
        "INTEGRAL_WITNESS_HODGE": f"({first['hodge'][0]},{first['hodge'][1]})",
        "INTEGRAL_WITNESS_EULER": str(first["euler"]),
        "INTEGRAL_WITNESS_FIRST_CUBIC": str(first["cubic_content"]),
        "INTEGRAL_WITNESS_SECOND_CUBIC": str(second["cubic_content"]),
        "INTEGRAL_WITNESS_FIRST_CHERN": str(first["chern_content"]),
        "INTEGRAL_WITNESS_SECOND_CHERN": str(second["chern_content"]),
    }
    return {
        "dataset": catalog.dataset,
        "dataset_sha256": catalog.member_sha256,
        "archive_sha256": catalog.sha256,
        "cohort": "non-product configurations",
        "summary": summary,
        "joint": cohort_cells(joint),
        "hodge": [{"hodge": list(pair), "cells": cohort_cells(cells)} for pair, cells in sorted(hodge.items())],
        "euler": [{"euler": value, "cells": cohort_cells(cells)} for value, cells in sorted(euler.items())],
        "witness": witness,
        "manuscript_values": variables,
        "rows": rows,
    }


def plot(payload, outputs):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from matplotlib.patches import Rectangle
    from matplotlib.ticker import StrMethodFormatter

    summary = payload["summary"]
    counts = {(cell["cubic_content"], cell["chern_content"]): cell["count"] for cell in payload["joint"]}
    cubic_axis = sorted({g3 for g3, _ in counts})
    chern_axis = sorted({g2 for _, g2 in counts})
    ink, subdued, border = "#172f43", "#405b6c", "#d6e1e8"
    cmap = plt.get_cmap("Blues")
    norm = LogNorm(1, 10 ** (len(str(max(counts.values())))))
    with plt.rc_context({
        "font.family": "DejaVu Sans", "font.size": 11, "text.color": ink,
        "axes.labelcolor": ink, "xtick.color": subdued, "ytick.color": subdued,
        "mathtext.default": "regular", "pdf.fonttype": 42, "svg.fonttype": "none",
        "svg.hashsalt": "py-cipro-integral-invariants",
    }):
        fig = plt.figure(figsize=(11, 5.4), facecolor="white")
        fig.text(.075, .932, "Integral content of cubic and Chern data", fontsize=22, weight="bold")
        fig.text(.075, .872,
                 f"{summary['joint_pairs']} observed content pairs across the {summary['records']:,} non-product configurations",
                 fontsize=11.5, color=subdued)
        matrix = fig.add_axes((.10, .21, .58, .57))
        matrix.set_title("A   Joint archive distribution", loc="left", fontsize=12, weight="bold", pad=12)
        for y, g2 in enumerate(chern_axis):
            for x, g3 in enumerate(cubic_axis):
                count = counts.get((g3, g2))
                color = cmap(norm(count)) if count else "#f2f5f7"
                matrix.add_patch(Rectangle((x, y), 1, 1, facecolor=color, edgecolor="white", linewidth=.9))
                if count:
                    matrix.text(x + .5, y + .5, f"{count:,}", ha="center", va="center",
                                fontsize=8.5, weight="bold" if count >= 100 else "normal",
                                color="white" if norm(count) >= .64 else ink)
        matrix.set(xlim=(0, len(cubic_axis)), ylim=(0, len(chern_axis)),
                   xticks=[i + .5 for i in range(len(cubic_axis))], xticklabels=cubic_axis,
                   yticks=[i + .5 for i in range(len(chern_axis))], yticklabels=chern_axis,
                   xlabel=r"Cubic content $g_3$", ylabel=r"Second Chern content $g_2$")
        matrix.tick_params(length=0, labelsize=9)
        for spine in matrix.spines.values():
            spine.set_visible(False)
        legend = fig.add_axes((.102, .075, .44, .022))
        scale = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=legend,
                             orientation="horizontal", ticks=(1, 10, 100, 1000), format=StrMethodFormatter("{x:,.0f}"))
        scale.solids.set_rasterized(False)
        scale.minorticks_off()
        scale.outline.set_visible(False)
        scale.ax.tick_params(labelsize=8, length=2)
        fig.text(.56, .075, "Records per cell", fontsize=9, color=subdued)

        side = fig.add_axes((.715, .21, .245, .57))
        side.set_axis_off()
        side.set_title("B   Equal Hodge numbers", loc="left", fontsize=12, weight="bold", pad=12)
        first = payload["witness"][0]
        h11, h21 = first["hodge"]
        side.text(0, .969, rf"$(h^{{1,1}},h^{{2,1}})=({h11},{h21})$   ·   $\chi={first['euler']}$",
                  fontsize=11, va="top", color=subdued)
        for row, bottom, accent, background in zip(
            payload["witness"], (.505, .075), ("#1b628e", "#99471d"), ("#ecf5fb", "#fff2e9"), strict=True,
        ):
            side.add_patch(Rectangle((0, bottom), 1, .37, facecolor=background, edgecolor=border, linewidth=.7))
            side.text(.07, bottom + .275, f"Record #{row['id']}", fontsize=12, weight="bold", color=accent)
            degrees = ",".join(map(str, row["degrees"]))
            side.text(.07, bottom + .179, rf"Degrees $({degrees})$ in $\mathbf{{P}}^{{{row['ambient_dimension']}}}$",
                      fontsize=9.5)
            side.text(.07, bottom + .055, rf"$g_3={row['cubic_content']}$" + "     " + rf"$g_2={row['chern_content']}$",
                      fontsize=15, weight="bold")
        for output in outputs:
            output.parent.mkdir(parents=True, exist_ok=True)
            metadata = {"CreationDate": None, "ModDate": None} if output.suffix == ".pdf" else None
            fig.savefig(output, dpi=250, metadata=metadata)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/integral-invariants.json"))
    parser.add_argument("--figure", action="append", type=Path)
    args = parser.parse_args()
    report = compute_integral_invariants()
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    plot(report, args.figure or [Path("manuscript/figures/integral-invariants.png")])
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
