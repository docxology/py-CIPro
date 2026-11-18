#!/usr/bin/env python3
"""Prepare the py-CIPro manuscript for docxology/template Stage 03."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import yaml

from infrastructure.documentation.generated_figure_registry import publish_generated_figures
from infrastructure.rendering.manuscript_injection import (
    substitute_manuscript_text,
    write_resolved_manuscript_tree,
)

from manuscript_variables import build_variables, validate_tokens
from render_graphical_abstract import render_graphical_abstract


@dataclass(frozen=True)
class Figure:
    label: str
    filename: str
    caption: str
    alt_text: str
    generated_by: str = "scripts/render_figures.py --suite"


def figures_from_source(root, variables):
    descriptions = {
        "fig:cicy3_atlas": "Hodge-pair scatter with multiplicities and a frequency chart of Euler characteristics.",
        "fig:cicy3_structure": "Configuration matrix shape heatmap beside favorability fractions by ambient rank.",
        "fig:cicy3_multiplicity": "Rank concentration of Hodge-pair frequencies and pair counts by multiplicity.",
        "fig:line_bundle_cohomology": "Quintic line-bundle dimensions and supported and unsupported charge regions of the bicubic.",
        "fig:chern_audit": "Hexagonal count plot of polarized Chern pairings and a scatter plot highlighting index extremes at one Hodge pair.",
        "fig:atlas_comparison": "Two Euler distribution steps, two ambient-factor profiles, and a signed decomposition of the change in archived favorability.",
        "fig:bicubic_exact": "Exact bicubic cohomology in a specified smooth member and its excess over the generic formula.",
        "fig:integral_invariants": "Logarithmic heatmap of cubic and second Chern content across the archive. A solid outline marks the cell (9, 54) for record 7878 and a dashed outline marks (12, 60) for record 7879. Adjacent cards show their common Hodge pair and distinct rank-one invariants.",
    }
    generated_by = {
        "fig:chern_audit": "scripts/chern_audit.py",
        "fig:atlas_comparison": "scripts/atlas_comparison.py",
        "fig:bicubic_exact": "scripts/bicubic_exact.py",
        "fig:integral_invariants": "scripts/integral_invariants.py",
    }
    pattern = re.compile(
        r"^!\[(.+)\]\(\.\./output/figures/([a-z0-9-]+\.png)\)\{#(fig:[a-z0-9_]+)\b[^}]*\}",
        re.MULTILINE,
    )
    specs = []
    for source in sorted((root / "manuscript").glob("*.md")):
        text, _ = substitute_manuscript_text(source.read_text(encoding="utf-8"), variables)
        for caption, filename, label in pattern.findall(text):
            specs.append(Figure(label, filename, caption, descriptions[label],
                                generated_by.get(label, "scripts/render_figures.py --suite")))
    if len(specs) != len(descriptions) or {spec.label for spec in specs} != descriptions.keys():
        raise ValueError("Manuscript figure captions do not match the generated figure set")
    return specs


def main():
    root = Path(__file__).resolve().parents[1]
    variables, evidence = build_variables(root)
    validate_tokens(root, variables)
    config = yaml.safe_load((root / "manuscript" / "config.yaml").read_text(encoding="utf-8"))
    citation = yaml.safe_load((root / "CITATION.cff").read_text(encoding="utf-8"))
    doi = config.get("publication", {}).get("doi")
    github_release = variables["GITHUB_RELEASE_URL"]
    if citation["version"] != variables["PACKAGE_VERSION"] or citation["url"] != github_release or citation.get("doi") != doi:
        raise ValueError("Citation and manuscript publication identifiers must describe the same release")
    zenodo = json.loads((root / ".zenodo.json").read_text(encoding="utf-8"))
    if zenodo["version"] != variables["PACKAGE_VERSION"] or not any(
        item["identifier"] == github_release for item in zenodo["related_identifiers"]
    ):
        raise ValueError("Zenodo metadata must point to the same GitHub release as the manuscript")
    evidence["publication"] = {"github_release": github_release}
    if doi:
        if not re.fullmatch(r"10\.5281/zenodo\.[1-9][0-9]*", doi):
            raise ValueError("Use the version DOI issued by production Zenodo")
        evidence["publication"]["doi"] = doi
        evidence["publication"]["doi_url"] = f"https://doi.org/{doi}"
    evidence["manuscript"] = {
        "title": config["paper"]["title"],
        "author": ", ".join(author["name"] for author in config["authors"]),
    }
    specs = figures_from_source(root, variables)
    publish_generated_figures(
        root / "output" / "figures",
        specs,
        [root / "manuscript" / "figures" / spec.filename for spec in specs],
        schema_version="py-cipro-figures/v1",
    )
    cover = root / "output" / "cover"
    cover_pdf = cover / "graphical-abstract.pdf"
    cover_png = cover / "graphical-abstract.png"
    cover_record = render_graphical_abstract(root / "data", cover_pdf, cover_png)
    evidence["cover"] = {
        "alt_text": config["paper"]["cover"]["alt"],
        "inputs_sha256": cover_record["data_sha256"],
        "size_inches": cover_record["size_inches"],
        "outputs_sha256": {
            path.name: sha256(path.read_bytes()).hexdigest() for path in (cover_pdf, cover_png)
        },
    }
    data = root / "output" / "data"
    data.mkdir(parents=True, exist_ok=True)
    for name, payload in (("manuscript_variables.json", variables), ("software_and_analysis.json", evidence)):
        destination = data / name
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_resolved_manuscript_tree(root, variables)
    print(f"Hydrated {len(variables)} manuscript variables and staged {len(specs)} figures.", file=sys.stderr)


if __name__ == "__main__":
    main()
