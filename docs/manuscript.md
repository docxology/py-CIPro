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

Generate the four figures and the typed result tables into an ignored
output directory. The first two `diff` calls should produce no output.

```sh
renderer_python="$(pwd -P)/.venv/bin/python"
cd "$py_cipro_root"
export PYTHONPATH="$py_cipro_root/src"
mkdir -p output/replay/data
"$renderer_python" scripts/check_intersections.py \
  --output output/replay/data/analytic-checks.json
"$renderer_python" scripts/render_figures.py --suite \
  --figures-dir output/replay/figures --data-dir output/replay/data
diff -u data/analytic-checks.json output/replay/data/analytic-checks.json
diff -u data/manuscript-analysis.json output/replay/data/manuscript-analysis.json
```

The tracked PNGs are the manuscript's figure inputs. To regenerate an
updated figure set, run `scripts/render_figures.py --suite` without the
output overrides and review the data alongside the plots. Pass
`--format pdf` and a separate `--figures-dir` to export the same figures
as standalone vectors. The older `--summary` and `--output` options retain
the single-atlas workflow.

## Hydrate, render and validate

From the template checkout, run the project producer with the renderer
environment. It validates required placeholders, stages registered figures,
writes the structured outputs, and calls the template's manuscript injection
function. The private project lives outside the renderer's project custody
root, so run the producer explicitly before Stage 03. Stage 03 consumes the
hydrated result while retaining its pre-render and publication checks.

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
record and the input and figure SHA-256 digests. Figure captions and alt text
are registered in `output/figures/figure_registry.json`.

## Refresh the dashboard's manuscript assets

The installed dashboard includes the validated manuscript PDF, four
standalone vector figures, and the data behind the plots. To refresh the
bundle after a verified render, collect these files in an export directory
and generate `SHA256SUMS` there with relative paths.

- `pdf/py-CIPro-manuscript.pdf` contains the template's combined PDF.
- `figures/` contains the four named PDF exports and `figure_registry.json`.
- `data/` contains `manuscript-analysis.json` and `software_and_analysis.json`.
- `reports/` contains `validation_report.json` and `artifact_manifest.json`.

Run `python scripts/package_research.py EXPORT --template-commit COMMIT
--title TITLE --pages PAGES` from the project checkout. Use the full
renderer commit and the values reported by `pdfinfo` for the PDF title and
page count. The script checks the export digests, green template validation,
and the match to the tracked analysis before updating the files in
`src/py_cipro/research_data/`. Rebuild and test the wheel to check the
packaged routes. [Dashboard guide](dashboard.md)
