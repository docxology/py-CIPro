#!/usr/bin/env python3
"""Render the catalogue witness and audit counts on the manuscript cover."""

import argparse
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
COVER_STUDY_IDS = ("integral-invariants", "cubic-refinement", "index-divisibility")
FIGSIZE = (7.0, 4.7)
PAPER = "#f7f5ef"
INK = "#16282e"
MUTED = "#4c6061"
RULE = "#d4dad3"
TEAL = "#155a53"
TEAL_PALE = "#e5eee7"
RUST = "#863f25"
RUST_PALE = "#f4e7de"


def load_studies(directory):
    raw = {name: (directory / f"{name}.json").read_bytes() for name in COVER_STUDY_IDS}
    studies = {name: json.loads(data) for name, data in raw.items()}
    digests = {name: sha256(data).hexdigest() for name, data in raw.items()}
    source_ids = {(study["archive_sha256"], study["dataset_sha256"]) for study in studies.values()}
    if (
        len(source_ids) != 1
        or studies["cubic-refinement"]["integral_receipt_sha256"] != digests["integral-invariants"]
        or studies["index-divisibility"]["cubic_refinement_sha256"] != digests["cubic-refinement"]
    ):
        raise ValueError("The graphical abstract requires three linked receipts from one CICY3 archive.")
    return studies, digests


def cover_evidence(studies):
    integral, cubic, index = (studies[name] for name in COVER_STUDY_IDS)
    pairs = set()
    signatures = set()
    extended = Counter()
    hodge_signatures = defaultdict(set)
    counts = Counter()
    records = {}
    for original, refined, fixed in zip(integral["rows"], cubic["rows"], index["rows"], strict=True):
        record_id = original["id"]
        pair = original["cubic_content"], original["chern_content"]
        signature = tuple(refined[key] for key in ("d1", "d2", "d3", "dp"))
        divisor = fixed["index_divisor"]
        if (
            record_id in records
            or record_id != refined["id"]
            or record_id != fixed["id"]
            or (signature[0], signature[3]) != pair
        ):
            raise ValueError(f"Cover source data disagree on record {record_id}.")
        pairs.add(pair)
        signatures.add(signature)
        extended[(*signature, divisor)] += 1
        hodge_signatures[tuple(original["hodge"]), signature].add(divisor)
        counts[divisor] += 1
        records[record_id] = original, signature, divisor

    totals = len(pairs), len(signatures), len(extended)
    summary = index["summary"]
    nonunit = len(records) - counts[1]
    refined_hodge = {hodge for (hodge, _), divisors in hodge_signatures.items() if len(divisors) > 1}
    if (
        totals != (integral["summary"]["joint_pairs"], cubic["summary"]["joint_quadruples"], summary["signatures_after"])
        or totals[1] != summary["signatures_before"]
        or len(records) != summary["records"]
        or nonunit != summary["nonunit_records"]
        or len(refined_hodge) != summary["hodge_groups_refined"]
        or extended != {tuple(row["signature"]): row["count"] for row in index["joint"]}
        or counts != {row["value"]: row["count"] for row in index["distribution"]}
    ):
        raise ValueError("The cohort totals do not match the cover study receipts.")

    first, second = index["witness"]
    for witness in (first, second):
        source, signature, divisor = records[witness["id"]]
        if (
            tuple(witness["signature"]) != signature
            or witness["index_divisor"] != divisor
            or any(witness[key] != source[key] for key in ("hodge", "euler", "hyperplane_indices"))
        ):
            raise ValueError(f"The cover witness disagrees with record {witness['id']}.")
    if (
        any(first[key] != second[key] for key in ("hodge", "euler", "signature"))
        or (first["index_divisor"], second["index_divisor"]) != (2, 1)
        or not any(value % 2 for value in second["hyperplane_indices"])
    ):
        raise ValueError("The cover requires a matched witness with an even and an odd-capable index.")
    return first, second, totals, len(records), counts


def box(fig, x, y, width, height, fill, edge="none", radius=.012):
    fig.add_artist(FancyBboxPatch(
        (x, y), width, height, transform=fig.transFigure,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=fill, edgecolor=edge, linewidth=.6, zorder=0,
    ))


def text(fig, x, y, label, size, *, color=INK, weight="normal", **options):
    return fig.text(x, y, label, fontsize=size, color=color, weight=weight, va="center", **options)


def rule(fig, x0, x1, y0, y1, color=RULE):
    fig.add_artist(Line2D((x0, x1), (y0, y1), transform=fig.transFigure, color=color, lw=.75))


def tuple_label(values):
    return "(" + ", ".join(str(value) for value in values) + ")"


def shared_invariants(fig, first):
    box(fig, .045, .732, .910, .104, INK)
    for x, label, value in (
        (.067, r"Shared Hodge numbers $(h^{1,1},h^{2,1})$", tuple_label(first["hodge"])),
        (.391, r"Euler characteristic", str(first["euler"]).replace("-", "−")),
        (.625, "Cubic and Chern gcds", tuple_label(first["signature"])),
    ):
        text(fig, x, .803, label, 8.25, color="#d6e1da")
        text(fig, x, .759, value, 12.8, color="white", weight="bold")
    rule(fig, .363, .363, .749, .817, color="#61736f")
    rule(fig, .598, .598, .749, .817, color="#61736f")


def configuration(fig, x, witness, accent, pale):
    text(fig, x, .611, "Configuration degrees", 7.7, color=MUTED)
    for i, (dimension, row) in enumerate(zip(witness["ambient_dimensions"], witness["configuration"], strict=True)):
        y = .558 - .054 * i
        text(fig, x, y, rf"$\mathbb{{P}}^{{{dimension}}}$", 8.6, color=MUTED)
        for j, degree in enumerate(row):
            left = x + .047 + .027 * j
            box(fig, left, y - .019, .024, .038, pale if degree else PAPER, radius=.003)
            text(fig, left + .012, y, str(degree), 8.1, ha="center", color=accent if degree else MUTED)


def witness_panel(fig, x, witness, accent, pale, outcome):
    box(fig, x, .333, .442, .365, "white", RULE)
    x += .020
    text(fig, x, .660, f"CICY3 record {witness['id']}", 11.6, weight="bold")
    configuration(fig, x, witness, accent, pale)
    rule(fig, x + .189, x + .189, .428, .592)
    text(fig, x + .205, .611, r"Indices on $H_1,H_2,H_3$", 7.7, color=MUTED)
    for i, value in enumerate(witness["hyperplane_indices"]):
        left = x + .208 + .049 * i
        box(fig, left, .529, .042, .057, accent if value % 2 else pale, radius=.008)
        text(fig, left + .021, .558, str(value), 11.5, ha="center", weight="bold",
             color="white" if value % 2 else accent)
    text(fig, x + .205, .474, fr"Index gcd $d_\chi={witness['index_divisor']}$", 10.8, weight="bold")
    rule(fig, x, x + .402, .420, .420)
    text(fig, x, .376, outcome, 9.1, color=accent, weight="bold")


def cohort_panel(fig, totals, records, counts):
    text(fig, .046, .277, f"Signatures across {records:,} non-product records", 9.4, weight="bold")
    labels = ("Cubic and Chern", "+ repeated and diagonal", "+ the index gcd")
    for x, total, label in zip((.114, .308, .509), totals, labels, strict=True):
        text(fig, x, .183, str(total), 23, weight="bold", ha="center", color=TEAL)
        text(fig, x, .115, label, 8.4, color=MUTED, ha="center")
    for x in (.205, .406):
        text(fig, x, .183, "→", 17, color=MUTED, ha="center")
    rule(fig, .632, .632, .094, .285)
    nonunit = sorted((divisor, count) for divisor, count in counts.items() if divisor > 1)
    largest_count = max((count for _, count in nonunit), default=1)
    text(fig, .666, .277, fr"{records - counts[1]:,} records with $d_\chi>1$", 9.4, weight="bold", color=RUST)
    text(fig, .667, .242, r"$d_\chi$", 7.5, color=MUTED, ha="center")
    text(fig, .955, .242, "Records", 7.5, color=MUTED, ha="right")
    for i, (divisor, count) in enumerate(nonunit):
        y = .213 - .027 * i
        text(fig, .667, y, str(divisor), 8.0, ha="center")
        rule(fig, .704, .704 + .203 * count / largest_count, y, y, color=RUST)
        text(fig, .955, y, f"{count:,}", 8.0, color=RUST, ha="right", weight="bold")
    rule(fig, .045, .955, .076, .076)
    text(fig, .045, .041, "CIPro v1.0 CICY3 archive · Exact Python audit of the ambient divisor lattices",
         7.4, color=MUTED)


def render(studies, pdf, png):
    first, second, totals, records, counts = cover_evidence(studies)
    odd_axis = next(i for i, value in enumerate(second["hyperplane_indices"], start=1) if value % 2)
    odd_value = second["hyperplane_indices"][odd_axis - 1]
    with matplotlib.rc_context({"font.family": "DejaVu Sans", "pdf.fonttype": 42}):
        fig = Figure(figsize=FIGSIZE, facecolor=PAPER)
        text(fig, .044, .931, "Same Hodge numbers, different index gcds", 18, weight="bold")
        text(fig, .046, .872, "The Riemann–Roch line-bundle index separates two matched CICY threefold records.",
             9.3, color=MUTED)
        shared_invariants(fig, first)
        witness_panel(fig, .045, first, TEAL, TEAL_PALE, "All ambient line-bundle indices are even")
        witness_panel(fig, .513, second, RUST, RUST_PALE,
                      fr"Odd index at $H_{odd_axis}$ · $\chi(X,\mathcal{{O}}_X(H_{odd_axis}))={odd_value}$")
        cohort_panel(fig, totals, records, counts)
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
