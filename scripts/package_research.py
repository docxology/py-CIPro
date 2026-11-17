"""Stage previously validated manuscript and figure exports for the dashboard."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
FIGURE_IDS = ("cicy3-atlas", "cicy3-structure", "cicy3-multiplicity", "line-bundle-cohomology")
ASSETS = {
    "manuscript.pdf": "pdf/py-CIPro-manuscript.pdf",
    "manuscript-analysis.json": "data/manuscript-analysis.json",
    **{f"{figure}.pdf": f"figures/{figure}.pdf" for figure in FIGURE_IDS},
}


def package_research(export, destination, template_commit, manuscript_title, manuscript_pages):
    if not re.fullmatch(r"[a-f0-9]{40}", template_commit):
        raise ValueError("Supply the template's full commit hash")
    checksums = {}
    for line in (export / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        digest, path = line.split("  ", 1)
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
    source = json.loads(checked("data/software_and_analysis.json"))
    manifest = json.loads(checked("reports/artifact_manifest.json"))
    if not any(entry["sha256"] == sha256(assets["manuscript.pdf"]).hexdigest()
               for entry in manifest["entries"] if entry["path"].endswith("_combined.pdf")):
        raise ValueError("The manuscript PDF is absent from the template artifact receipt")
    canonical = ROOT / "data" / "manuscript-analysis.json"
    if assets["manuscript-analysis.json"] != canonical.read_bytes():
        raise ValueError("The exported analysis differs from the source data")
    registry = json.loads(checked("figures/figure_registry.json"))
    figure_metadata = {Path(item["filename"]).stem: item for item in registry["figures"]}
    if not set(FIGURE_IDS) <= figure_metadata.keys():
        raise ValueError("The export is missing a dashboard figure registration")
    upstream = source["software"]["upstream"]
    provenance = {
        "schema_version": 1,
        "manuscript_title": manuscript_title,
        "manuscript_pages": manuscript_pages,
        "source_commit": source["source_commit"],
        "template_version": source["template_version"],
        "template_commit": template_commit,
        "archive_sha256": upstream["archive_sha256"],
        "dataset_sha256": upstream["member_sha256"],
        "assets_sha256": {name: sha256(content).hexdigest() for name, content in assets.items()},
        "figures": {
            figure: {
                "caption": figure_metadata[figure]["caption"],
                "alt_text": figure_metadata[figure]["metadata"]["alt_text"],
            }
            for figure in FIGURE_IDS
        },
    }
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
