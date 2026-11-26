# Render the research manuscript

The [canonical manuscript](manuscript/README.md) renders with
[Template at commit `87704fe`](https://github.com/docxology/template/tree/87704feae0a4490ef7dad9c931d268e8c30273c2).
Use Python 3.14, uv, Pandoc 3.14, a compatible pandoc-crossref, XeLaTeX,
BibTeX, and Poppler. The analysis and render use the bundled CIPro release
and run without a Wolfram kernel. The packaged dashboard PDF and vector
figures retain their [original release provenance](../src/py_cipro/research_data/provenance.json)
from Template 5.0.2.

## What the build reads

| Input | Role |
| --- | --- |
| [`pyproject.toml`](../pyproject.toml) and the release, dispatch and preset registries | Package version, license, Python requirement, entry points, pinned CIPro identity, and the method inventory |
| [`data/cicy3-summary.json`](../data/cicy3-summary.json) | Release digests and whole-catalog summary |
| [`data/analytic-checks.json`](../data/analytic-checks.json) | Independent integer recomputation of the Euler characteristic of every configuration and two exact Chern and intersection fixtures |
| [`data/manuscript-analysis.json`](../data/manuscript-analysis.json) | Plot data, finite-catalog denominators, native cohomology charge-by-charge outcomes, and independent checks |
| [`data/chern-audit.json`](../data/chern-audit.json) | Ambient second Chern pairings and polarized Hilbert data for the full archive |
| [`data/atlas-comparison.json`](../data/atlas-comparison.json) | Exact presentation and Hodge-pair weights, Euler distributions, and decomposition of favorability shares |
| [`data/bicubic-exact.json`](../data/bicubic-exact.json) | Equation coefficients, smoothness minors, and rational map ranks with exact cohomology in the finite charge grid |
| [`data/integral-invariants.json`](../data/integral-invariants.json) | Record-level divisibilities of the cubic form and Chern functional on the ambient divisor lattice, grouped by Hodge numbers |
| [`data/cubic-refinement.json`](../data/cubic-refinement.json) | Repeated and diagonal cubic divisibility across the same archive, with matched record witnesses |
| [`data/index-divisibility.json`](../data/index-divisibility.json) | Fixed divisors of the ambient line-bundle index, signed evaluation checks, and record-level results |
| [`references.bib`](manuscript/references.bib) | Primary geometry, software, and dataset citations |

Numbered definitions, propositions, lemmas, corollaries, examples,
equations, figures, and tables use stable source labels. The template
resolves cross-references and emits the numbers. To update the prose,
edit the source Markdown. Change numerical or software claims at their
source and regenerate the output.

## Set up the pinned renderer

Start in a clean, committed py-CIPro checkout. Put a second checkout under
the pinned renderer's `projects/working/` so its source revision and
output provenance identify the exact render.

```sh
set -e
source_checkout="$(pwd -P)"
source_commit="$(git rev-parse HEAD)"
render_root="$(mktemp -d "${TMPDIR:-/tmp}/py-cipro-render.XXXXXX")"
renderer="$render_root/template"
git clone https://github.com/docxology/template.git "$renderer"
git -C "$renderer" checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
project_name=py-CIPro
py_cipro_root="$renderer/projects/working/$project_name"
mkdir -p "$renderer/projects/working"
git clone "$source_checkout" "$py_cipro_root"
git -C "$py_cipro_root" checkout --detach "$source_commit"
cd "$renderer"
uv sync --locked
uv pip install --python .venv/bin/python 'sympy==1.14.0' 'wolframclient==1.4.0' 'requests>=2.32,<3'
```

Use this dedicated renderer environment for the analysis and manuscript.

## Recompute the results and figures

Generate all eight figures, the graphical abstract, and the typed result
tables into an ignored output directory. The comparisons should produce
no output.

```sh
renderer_python="$(pwd -P)/.venv/bin/python"
cd "$py_cipro_root"
export PYTHONPATH="$py_cipro_root/src"
mkdir -p output/replay/data
"$renderer_python" scripts/check_intersections.py \
  --output output/replay/data/analytic-checks.json
"$renderer_python" scripts/render_figures.py --suite \
  --figures-dir output/replay/figures --data-dir output/replay/data
"$renderer_python" scripts/chern_audit.py --data output/replay/data/chern-audit.json \
  --figure output/replay/figures/chern-audit.png
"$renderer_python" scripts/atlas_comparison.py --data output/replay/data/atlas-comparison.json \
  --figure output/replay/figures/atlas-comparison.png
"$renderer_python" scripts/bicubic_exact.py --data output/replay/data/bicubic-exact.json \
  --figure output/replay/figures/bicubic-exact.png
"$renderer_python" scripts/integral_invariants.py --data output/replay/data/integral-invariants.json \
  --figure output/replay/figures/integral-invariants.png
"$renderer_python" scripts/cubic_refinement.py --reference output/replay/data/integral-invariants.json \
  --output output/replay/data/cubic-refinement.json
"$renderer_python" scripts/index_divisibility.py --reference output/replay/data/cubic-refinement.json \
  --output output/replay/data/index-divisibility.json
for name in analytic-checks manuscript-analysis chern-audit atlas-comparison bicubic-exact integral-invariants cubic-refinement index-divisibility; do
  diff -u "data/$name.json" "output/replay/data/$name.json" || exit 1
done
"$renderer_python" scripts/render_graphical_abstract.py --data-dir output/replay/data \
  --pdf output/replay/cover/graphical-abstract.pdf --png output/replay/cover/graphical-abstract.png
```

The tracked PNGs are the manuscript's figure inputs. Run the same
generators without output overrides to refresh them. Use
`render_figures.py --suite --format pdf --figures-dir DIR` for vector
exports of the four release-dashboard figures. Pass a PDF path as
`--figure` to each additional generator to export the remaining manuscript
figures as vectors. The plots and color keys in these exports are geometric
paths or text. Use `pdfimages -list` to confirm that they contain no raster
objects. The older `--summary` and `--output` options retain the single-atlas
workflow.

## Hydrate, render and validate

From the template checkout, run the project producer with the renderer
environment. It validates required placeholders, stages registered figures,
renders the graphical abstract, writes structured outputs, and creates the
resolved manuscript in `output/manuscript/`. Run the producer explicitly before
Stage 03, then tell the renderer to use that resolved result. Stage 04 checks
the figures, source composition, and evidence. Install `tocbibind` in a minimal TeX setup for the
linked bibliography entry.

```sh
cd "$renderer"
PYTHONPATH="$py_cipro_root/src:$renderer" \
  uv run --no-sync python "$py_cipro_root/scripts/z_generate_manuscript_variables.py"
uv run --no-sync python scripts/pipeline/stage_03_render.py \
  --skip-manuscript-hydration --project "working/$project_name"
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project "working/$project_name"
```

Find the combined PDF at `output/pdf/py-CIPro_combined.pdf`, HTML at
`output/web/index.html`, and validation and provenance reports at
`output/reports/` in the isolated py-CIPro checkout. The project preamble sets the same red
for internal references, citations, and external links. Use
`pdfinfo -url` and `pdfinfo -dests` to inspect the resolved targets.
The authored variables resolve into
`output/data/manuscript_variables.json`, and
`output/data/software_and_analysis.json` binds the machine-readable software
record to the input, figure, and cover SHA-256 digests. Figure captions and
alt text are registered in `output/figures/figure_registry.json`. The cover
art is in `output/cover/`, and the template reads its image and description
from `paper.cover` in `docs/manuscript/config.yaml`.

## Refresh the dashboard's manuscript assets

Stage the verified render and regenerated figures and data in an export
directory. Generate `SHA256SUMS` in that directory with relative paths.

- `pdf/py-CIPro-manuscript.pdf` contains the template's combined PDF.
- `cover/` contains the rendered `graphical-abstract.pdf` and `graphical-abstract.png`.
- `figures/` contains all eight named PDF exports and `figure_registry.json`.
- `data/` contains all nine tracked analysis files, `manuscript_variables.json`, and the renderer's `software_and_analysis.json`.
- `reports/` contains `validation_report.json` and `artifact_manifest.json`.

The Figure 6 controls use the cubic refinement receipt. The graphical abstract
also uses the integral-lattice and fixed-divisor receipts. The dashboard compares
the two cover witnesses in Figure 6 and links to `index-divisibility.json`.

Run `python scripts/package_research.py EXPORT --template-commit COMMIT
--title TITLE --pages PAGES` from the project checkout. Use the full
renderer commit and the values reported by `pdfinfo` for the PDF title and
page count. The script checks the export digests, template validation, and
the bindings between the cover, the study data, and the rendered assets before updating
the files in
`src/py_cipro/research_data/`. Rebuild and test the wheel to check the
packaged routes. [Dashboard guide](dashboard.md)

## Cite and archive a version

The render writes the GitHub tag URL into the manuscript and validates it
against `CITATION.cff` and `.zenodo.json`. For a Zenodo deposit, reserve a
production **version DOI** on the draft, then set the identifier in both
`publication.doi` in `docs/manuscript/config.yaml` and `doi` in
`CITATION.cff`. The template prints it as a clickable link on the cover.
Render and package again, check the visible DOI and both PDF links, and
archive the exact tested files. Zenodo registers the DOI when the record
is published. [Zenodo DOI reservation](https://help.zenodo.org/docs/deposit/describe-records/reserve-doi/)

Use the related GitHub tag URL in `.zenodo.json` for the deposit. After the
DOI resolves, link it from the tagged GitHub release notes and the repository
citation section. Use one Zenodo record for that version. If the GitHub
tag has already been released, retain its artifact checksums and attach
or publish the resulting archival revision with its own provenance.
Zenodo publishes record metadata and lets depositors restrict file access.
[Zenodo record access and versioning](https://help.zenodo.org/docs/deposit/about-records/)
