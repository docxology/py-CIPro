# Render the research manuscript

The sources in [`manuscript/`](../manuscript/) use
[`docxology/template` v5.0.2](https://github.com/docxology/template/releases/tag/v5.0.2)
at commit `9bebe79195b8f6be4a3da02838fcd296b3012a56`. The PDF needs
Python 3.14 or later, uv, Pandoc, pandoc-crossref, XeLaTeX, and BibTeX.
The analysis and render use the bundled CIPro release and run without a
Wolfram kernel.

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
| [`manuscript/references.bib`](../manuscript/references.bib) | Primary geometry, software, and dataset citations |

Numbered definitions, propositions, lemmas, corollaries, examples,
equations, figures, and tables use stable source labels. The template
resolves cross-references and emits the numbers. To update the prose,
edit the source Markdown. Change numerical or software claims at their
source and regenerate the output.

## Set up the pinned renderer

Start in a clean, committed py-CIPro checkout so the revision and indexed
source provenance correspond to the PDF. Use a dedicated renderer checkout
and the template's [private project workflow](https://github.com/docxology/template/blob/v5.0.2/docs/maintenance/private-projects-repo.md).

```sh
py_cipro_root="$(pwd -P)"
project_name="$(basename "$py_cipro_root")"
render_root="$(mktemp -d "${TMPDIR:-/tmp}/py-cipro-render.XXXXXX")"
git clone --branch v5.0.2 --single-branch --depth 1 \
  https://github.com/docxology/template.git "$render_root/template"
cd "$render_root/template"
test "$(git rev-parse HEAD)" = 9bebe79195b8f6be4a3da02838fcd296b3012a56 || exit 1
mkdir -p "$render_root/private/working"
ln -s "$py_cipro_root" "$render_root/private/working/$project_name"
export TEMPLATE_PRIVATE_PROJECTS_ROOT="$render_root/private"
uv sync --locked --no-dev
uv pip install --python .venv/bin/python 'sympy==1.14.0' 'wolframclient==1.4.0'
uv run --no-sync python -m infrastructure.orchestration link-projects --dry-run
uv run --no-sync python -m infrastructure.orchestration link-projects
```

The locked template environment includes Matplotlib 3.11.2. You can use
the same interpreter for the analysis and manuscript.

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
renders the graphical abstract, writes structured outputs, and calls the
template's manuscript injection function. The private project lives outside
the renderer's project custody root, so run the producer explicitly before
Stage 03. Stage 03 consumes the hydrated result while retaining its pre-render
and publication checks. Install `tocbibind` in a minimal TeX setup for the
linked bibliography entry.

```sh
cd "$render_root/template"
PYTHONPATH="$py_cipro_root/src:$render_root/template" \
  uv run --no-sync python "$py_cipro_root/scripts/z_generate_manuscript_variables.py"
uv run --no-sync python scripts/pipeline/stage_03_render.py \
  --skip-manuscript-hydration --project "working/$project_name"
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project "working/$project_name"
```

The combined PDF is in `output/pdf/` inside the py-CIPro checkout. The
template names it from the checkout directory. Its validation and provenance
reports are in `output/reports/`. The authored variables resolve into
`output/data/manuscript_variables.json`, and
`output/data/software_and_analysis.json` binds the machine-readable software
record to the input, figure, and cover SHA-256 digests. Figure captions and
alt text are registered in `output/figures/figure_registry.json`. The cover
art is in `output/cover/`, and the template reads its image and description
from `paper.cover` in `manuscript/config.yaml`.

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
