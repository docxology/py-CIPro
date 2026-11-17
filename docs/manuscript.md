# Render the manuscript

The manuscript source is in `manuscript/`. It uses
[docxology/template v5.0.2](https://github.com/docxology/template/releases/tag/v5.0.2),
commit `9bebe79195b8f6be4a3da02838fcd296b3012a56`. The template's
[private project workflow](https://github.com/docxology/template/blob/v5.0.2/docs/maintenance/private-projects-repo.md)
links a private project into a local renderer checkout. PDF rendering needs
Python 3.14 or later, uv, Pandoc, and XeLaTeX. The manuscript and atlas figure
can be reproduced offline from the bundled release. Native calculations in
the dashboard use Python. Wolfram calculations use an activated kernel.

From the py-CIPro checkout, prepare a dedicated template checkout and a local
sidecar for this project. The provenance check reads indexed project sources.
Commit or stage the manuscript, figure and figure generator before running it.
The template expects figure inputs in `output/figures/`, so the build below
stages a copy of the checked-in figure there.

To regenerate the figure from the validated `Cicy3` data, install py-CIPro and
the plotting dependency into your project environment, then run the generator.

```sh
python -m pip install . 'matplotlib==3.11.2'
python scripts/render_figures.py --summary data/cicy3-summary.json
python scripts/check_intersections.py
python scripts/render_figures.py --output output/figures/cicy3-atlas.pdf
```

The default output is the 300 dpi `manuscript/figures/cicy3-atlas.png` used in
the manuscript. The optional PDF is a standalone vector figure. The JSON summary binds the
plotted release digest and the manuscript counts to the same parsed records. The independent analytic check emits
`data/analytic-checks.json` using exact integer polynomial arithmetic.

```sh
py_cipro_root="$(pwd -P)"
mkdir -p output/figures
cp manuscript/figures/cicy3-atlas.png output/figures/cicy3-atlas.png
project_name="$(basename "$py_cipro_root")"
render_root="$(mktemp -d "${TMPDIR:-/tmp}/py-cipro-render.XXXXXX")"
git clone --branch v5.0.2 --single-branch --depth 1 \
  https://github.com/docxology/template.git "$render_root/template"
cd "$render_root/template"
test "$(git rev-parse HEAD)" = 9bebe79195b8f6be4a3da02838fcd296b3012a56 || exit 1
mkdir -p "$render_root/private/working"
ln -s "$py_cipro_root" "$render_root/private/working/$project_name"
export TEMPLATE_PRIVATE_PROJECTS_ROOT="$render_root/private"
uv sync --locked
uv run --no-sync python -m infrastructure.orchestration link-projects --dry-run
uv run --no-sync python -m infrastructure.orchestration link-projects
uv run --no-sync python scripts/pipeline/stage_03_render.py --project "working/$project_name"
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project "working/$project_name"
```

Find the combined manuscript at `output/pdf/<checkout-name>_combined.pdf`
inside the py-CIPro checkout. The template writes its verification report under
`output/reports/`.
