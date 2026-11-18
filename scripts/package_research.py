"""Stage previously validated manuscript and figure exports for the dashboard."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
STUDY_IDS = ("chern-audit", "atlas-comparison", "bicubic-exact", "integral-invariants", "cubic-refinement")
FIGURE_IDS = (
    "chern-audit", "cicy3-atlas", "cicy3-multiplicity", "cicy3-structure",
    "atlas-comparison", "integral-invariants", "line-bundle-cohomology", "bicubic-exact",
)
COVER_NAMES = ("graphical-abstract.pdf", "graphical-abstract.png")
ASSETS = {
    "manuscript.pdf": "pdf/py-CIPro-manuscript.pdf",
    **{name: f"cover/{name}" for name in COVER_NAMES},
    **{f"{name}.json": f"data/{name}.json" for name in ("manuscript-analysis", "index-divisibility", *STUDY_IDS)},
    **{f"{figure}.pdf": f"figures/{figure}.pdf" for figure in FIGURE_IDS},
}


def package_research(export, destination, template_commit, manuscript_title, manuscript_pages):
    if not re.fullmatch(r"[a-f0-9]{40}", template_commit):
        raise ValueError("Supply the template's full commit hash")
    checksums = {}
    for line in (export / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
        if not re.fullmatch(r"[a-f0-9]{64}", digest) or path in checksums:
            raise ValueError(f"Invalid or repeated checksum for {path}")
        checksums[path] = digest

    def checked(path):
        content = (export / path).read_bytes()
        if sha256(content).hexdigest() != checksums.get(path):
            raise ValueError(f"Export checksum mismatch for {path}")
        return content

    checks = json.loads(checked("reports/validation_report.json"))["checks"]
    if not checks or not all(value is True for value in checks.values()):
        raise ValueError("The template validation report contains a failed check")

    assets = {name: checked(path) for name, path in ASSETS.items()}
    digests = {name: sha256(content).hexdigest() for name, content in assets.items()}
    source = json.loads(checked("data/software_and_analysis.json"))
    manifest = json.loads(checked("reports/artifact_manifest.json"))
    output_digests = {entry["path"]: entry["sha256"] for entry in manifest["entries"]}
    if not any(digest == digests["manuscript.pdf"] for path, digest in output_digests.items()
               if path.startswith("output/pdf/") and path.endswith("_combined.pdf")):
        raise ValueError("The manuscript PDF is absent from the template artifact receipt")
    if source["manuscript"]["title"] != manuscript_title or not source["manuscript"]["author"].strip():
        raise ValueError("The PDF title or author record disagrees with the manuscript metadata")
    cover = source["cover"]
    cover_inputs = cover["inputs_sha256"]
    if (not cover["alt_text"].strip() or not cover_inputs
            or any(digests.get(f"{name}.json") != digest or digest is None
                   for name, digest in cover_inputs.items())
            or any(cover["outputs_sha256"][name] != digests[name]
                   or output_digests.get(f"output/cover/{name}") != digests[name] for name in COVER_NAMES)):
        raise ValueError("The graphical abstract disagrees with the study or render receipts")
    for name, source_path in ASSETS.items():
        if name.endswith(".json") and assets[name] != (ROOT / source_path).read_bytes():
            raise ValueError(f"The exported analysis differs from the source data for {name}")
    registry = json.loads(checked("figures/figure_registry.json"))
    figure_metadata = {Path(item["filename"]).stem: item for item in registry["figures"]}
    if set(FIGURE_IDS) != figure_metadata.keys() or len(FIGURE_IDS) != len(registry["figures"]):
        raise ValueError("The exported figure registrations differ from the dashboard inventory")
    for figure in FIGURE_IDS:
        filename = figure_metadata[figure]["filename"]
        if source["figures_sha256"][filename] != output_digests.get(f"output/figures/{filename}"):
            raise ValueError(f"The rendered figure image disagrees with the source receipt for {figure}")
    upstream = source["software"]["upstream"]
    provenance = {
        "schema_version": 1,
        "manuscript_title": manuscript_title,
        "manuscript_author": source["manuscript"]["author"],
        "manuscript_pages": manuscript_pages,
        "source_commit": source["source_commit"],
        "template_version": source["template_version"],
        "template_commit": template_commit,
        "archive_sha256": upstream["archive_sha256"],
        "dataset_sha256": upstream["member_sha256"],
        "assets_sha256": digests,
        "cover": {"alt_text": cover["alt_text"], "studies_sha256": cover["inputs_sha256"]},
        "figures": {
            figure: {
                "caption": figure_metadata[figure]["caption"],
                "alt_text": figure_metadata[figure]["metadata"]["alt_text"],
            }
            for figure in FIGURE_IDS
        },
    }
    if "publication" in source:
        provenance["publication"] = source["publication"]
    destination.mkdir(parents=True, exist_ok=True)
    for name, content in assets.items():
        (destination / name).write_bytes(content)
    (destination / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path, help="Validated manuscript export with SHA256SUMS")
    parser.add_argument("--template-commit", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--pages", required=True, type=int)
    args = parser.parse_args()
    if args.pages < 1 or not args.title.strip():
        parser.error("Supply the title and positive page count from the PDF")
    package_research(args.export, ROOT / "src" / "py_cipro" / "research_data",
                     args.template_commit, args.title, args.pages)


if __name__ == "__main__":
    main()
