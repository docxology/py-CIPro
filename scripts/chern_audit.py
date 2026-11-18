"""Audit ambient Chern pairings and polarized indices over the CIPro census."""

import argparse
from collections import Counter
import json
from pathlib import Path

from py_cipro.catalog import _cicy3_source_rows, get_catalog
from py_cipro._research_chern import polarized_invariants


def compute_chern_audit():
    catalog = get_catalog()
    rows = []
    pairings_checked = 0
    mismatches = []
    for record, source in zip(catalog.records, _cicy3_source_rows(), strict=True):
        pairings, volume, contraction, index = polarized_invariants(record)
        archived = source["C"][1]
        pairings_checked += len(pairings)
        if tuple(pairings) != archived:
            mismatches.append({"id": record.id, "computed": pairings, "archived": list(archived)})
        rows.append({
            "id": record.id, "product": record.product, "hodge": [record.h11, record.h21],
            "c2": pairings, "volume": volume, "c2_polarized": contraction, "index": index,
        })

    modal_hodge = Counter(tuple(r["hodge"]) for r in rows if not r["product"]).most_common(1)[0][0]
    modal = [r for r in rows if not r["product"] and tuple(r["hodge"]) == modal_hodge]
    lo = min(modal, key=lambda row: (row["index"], row["id"]))
    hi = max(modal, key=lambda row: (row["index"], -row["id"]))
    return {
        "dataset_sha256": catalog.member_sha256,
        "archive_sha256": catalog.sha256,
        "rows": rows,
        "mismatches": mismatches,
        "summary": {
            "records": len(rows),
            "ambient_pairings": pairings_checked,
            "matched_records": len(rows) - len(mismatches),
            "modal_hodge": list(modal_hodge),
            "modal_records": len(modal),
            "modal_signatures": len({(row["volume"], row["c2_polarized"]) for row in modal}),
            "modal_low_id": lo["id"],
            "modal_low_index": lo["index"],
            "modal_low_volume": lo["volume"],
            "modal_low_contraction": lo["c2_polarized"],
            "modal_high_id": hi["id"],
            "modal_high_index": hi["index"],
            "modal_high_volume": hi["volume"],
            "modal_high_contraction": hi["c2_polarized"],
        },
    }


def plot(payload, output):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm
    from matplotlib.ticker import StrMethodFormatter

    summary = payload["summary"]
    rows = [row for row in payload["rows"] if not row["product"]]
    modal = [row for row in rows if row["hodge"] == summary["modal_hodge"]]
    sites = Counter((row["volume"], row["c2_polarized"]) for row in modal)
    ink, accent, pale = "#173348", "#ba512d", "#dbe5ed"
    with plt.rc_context({
        "font.family": "DejaVu Sans", "font.size": 10, "text.color": ink,
        "axes.labelcolor": ink, "axes.titlecolor": ink, "axes.titleweight": "bold",
        "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": "#8094a3",
        "axes.axisbelow": True, "grid.color": pale, "xtick.color": ink, "ytick.color": ink,
        "mathtext.default": "regular", "pdf.fonttype": 42,
    }):
        figure, (population, selected) = plt.subplots(1, 2, figsize=(10.8, 5.1))
        figure.subplots_adjust(left=.085, right=.983, bottom=.22, top=.765, wspace=.27)
        figure.text(.085, .925, "Polarized degrees and Chern pairings", fontsize=20, weight="bold")
        figure.text(.085, .864, "Exact ambient degree and second Chern pairing for the all-ones polarization",
                    fontsize=10.5, color="#3b596c")
        density = population.hexbin(
            [row["volume"] for row in rows], [row["c2_polarized"] for row in rows],
            xscale="log", gridsize=26, norm=LogNorm(), mincnt=1, cmap="YlGnBu",
            edgecolors="white", linewidth=.27,
        )
        population.set_title(f"A   {len(rows):,} non-product archive records", loc="left", pad=11)
        population.set_xlabel(r"Polarized degree $V$ (log scale)")
        population.set_ylabel(r"Chern pairing $T$")
        population.grid(alpha=.7)

        x, y = zip(*sites, strict=True)
        markers = selected.scatter(x, y, c=list(sites.values()), s=[16 + 10 * n**.5 for n in sites.values()],
                                   cmap="YlGnBu", norm=LogNorm(), linewidth=.35, edgecolor="#425a6b", alpha=.92)
        pair = tuple(summary["modal_hodge"])
        selected.set_title(f"B   {len(modal):,} records at Hodge pair {pair}", loc="left", pad=11)
        selected.set_xlabel(r"Polarized degree $V$")
        selected.set_ylabel(r"Chern pairing $T$")
        selected.grid(alpha=.7)
        selected.xaxis.set_major_formatter(StrMethodFormatter("{x:,.0f}"))
        selected.margins(x=.12, y=.19)
        for kind, offset, align in (("low", (9, 11), "left"), ("high", (-12, 12), "right")):
            x = summary[f"modal_{kind}_volume"]
            y = summary[f"modal_{kind}_contraction"]
            chosen = summary[f"modal_{kind}_id"]
            index = summary[f"modal_{kind}_index"]
            selected.scatter([x], [y], s=106, facecolors="none", edgecolors=accent, linewidth=1.4, zorder=4)
            selected.annotate(f"#{chosen}   index {index}", (x, y), xytext=offset, textcoords="offset points",
                              ha=align, color=accent, fontsize=8.5, weight="bold",
                              bbox={"facecolor": "white", "edgecolor": "none", "alpha": .86, "pad": 2})
        for plot, artist, legend, ticks in (
            (population, density, "Records per occupied hexagon", (1, 10, 100)),
            (selected, markers, "Records per occupied point", (1, 2, 4, 8)),
        ):
            bounds = plot.get_position()
            bar = figure.colorbar(artist, cax=figure.add_axes([bounds.x0, .099, bounds.width, .018]),
                                  orientation="horizontal", ticks=ticks, format=StrMethodFormatter("{x:g}"))
            bar.solids.set_rasterized(False)
            bar.minorticks_off()
            bar.set_label(legend, labelpad=3, fontsize=8.5)
            bar.ax.tick_params(labelsize=8, length=2)
            bar.outline.set_visible(False)
        output.parent.mkdir(parents=True, exist_ok=True)
        metadata = {"CreationDate": None, "ModDate": None} if output.suffix == ".pdf" else None
        figure.savefig(output, dpi=250, facecolor="white", metadata=metadata)
        plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data/chern-audit.json"))
    parser.add_argument("--figure", type=Path, default=Path("manuscript/figures/chern-audit.png"))
    args = parser.parse_args()
    report = compute_chern_audit()
    args.data.parent.mkdir(parents=True, exist_ok=True)
    args.data.write_text(json.dumps(report, separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    plot(report, args.figure)
    print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    main()
