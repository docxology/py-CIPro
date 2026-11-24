# py-CIPro

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24352379.svg)](https://doi.org/10.5281/zenodo.24352379)

Zenodo: [10.5281/zenodo.24352380](https://doi.org/10.5281/zenodo.24352380) (version 0.9.3) · [10.5281/zenodo.24352379](https://doi.org/10.5281/zenodo.24352379) (all versions)

Python bindings and native equivalents for CIPro v1.0, the Wolfram Language package for complete intersections in products of projective spaces. Choose the original Wolfram kernel interface or compute the supported native domains in Python with SymPy.

## Installation

Install Python 3.11 or later. The default Wolfram backend uses an activated [Wolfram Engine or Mathematica](https://support.wolfram.com/46070). Set `backend="python"` on `CIPro` for native computation. Set `WOLFRAM_KERNEL` to the executable if automatic discovery cannot find it. The constructor also accepts `kernel=`. Some upstream cohomology routines use Wolfram’s [legacy Combinatorica package](https://reference.wolfram.com/language/Combinatorica/ref/Compositions.html), which must be available to the kernel.

```sh
python -m pip install .
export WOLFRAM_KERNEL='/path/to/WolframKernel'
```

## Explore the released threefolds

```sh
py-cipro-dashboard
```

Open [the local dashboard](http://127.0.0.1:8765/). It reads the verified `Cicy3` member and links the Hodge plot, Euler distribution, record table, and configuration-matrix inspector across all 7,890 archived rows. Filter or select a point to see its contributing records. The 22 archived product rows use `(0, 0)` placeholders for their Hodge pair. The explorer identifies those rows separately. The archive view runs offline.

Open **Manuscript** to read the paper and explore all eight interactive figures. Drill down to the archive records behind a plotted group or rerun the Chern audit, catalogue weighting, and line-bundle calculations in Python. Each figure has a vector PDF download. [Research dashboard](docs/dashboard.md#read-and-reproduce-the-manuscript-figures)

Python is the dashboard default. Recalculate `CIDim`, `CY`, and `Euler` for an archived configuration or use the **Method lab** to run any of the 148 native method entries. Every native entry includes a runnable example. Choose Wolfram for an activated local kernel, or Auto to try Python first and use Wolfram when the native domain is unsupported. `py-cipro-dashboard --kernel` selects Wolfram as the initial backend. [Dashboard guide](docs/dashboard.md) · [Research guide](docs/research.md) · [Wolfram API guide](docs/wolfram-api.md)

With a private Wolfram Cloud deployment configured, `py-cipro-dashboard --cloud` selects it for archived record properties. The method lab and manuscript replays continue to run locally. The `py-cipro-cloud` command supports deployment, status, and qualification. [Wolfram API guide](docs/wolfram-api.md)

The **Manuscript** view includes a graphical abstract, eight interactive figures, and source-record links. In the integral-lattice figure, select a cubic and second Chern gcd pair and rerun a record's exact calculation in Python. The PDF includes a notation table and a methods concordance. [Manuscript build](docs/manuscript.md)

The **Cubic refinement** panel breaks the selected cell into four-part
signatures. The **Index-divisibility audit** puts cover records 7626 and 7635
side by side, with links to the source configurations and exact Python reruns.
Native `cubic_signature` and `ambient_index_divisor` calls also
recompute individual records for research notebooks. [Python examples](docs/python/api.md#recompute-cubic-and-index-divisibility) · [Archive studies](docs/research.md#recompute-the-ambient-divisibility-studies)

## Use

```python
from py_cipro import CIPro

quintic = {"DimPs": [4], "Conf": [[5]]}
with CIPro(backend="python") as ci:
    assert ci.property(quintic, "Euler", Format="Short") == -200
```

Use `backend="auto"` to try supported native operations first and route unavailable operations to Wolfram. Use the default `CIPro()` for the released Wolfram implementation and WXF results.

```python
from py_cipro import CIPro

quintic = {"DimPs": [4], "Conf": [[5]]}

with CIPro() as ci:
    result = ci.property(quintic, ["CIDim", "CY", "Euler"])
    print(result["CIDim"], result["CY"], result["Euler"])
    print(ci.Data("Cicy3", "Length"))
    help_result = ci.call_result("CIProp", "Keys")
    print(*help_result.output, sep="\n")
```

- `ci.call("Name", ...)` and `ci.Name(...)` invoke the same public Wolfram symbol. `ci.functions` lists the available names. `ci.property` and `ci.modify` dispatch to the selected backend with the released `CIProp` and `CIMod` keys.
- Lists and dictionaries become Wolfram lists and associations. Keyword arguments are Wolfram string-keyed rules such as `Format="Medium"`. Pass explicit `wl.Rule(...)` arguments for other rule types. Python strings are Wolfram strings. Use `wl` or `wlexpr` to build expressions from trusted code, for instance `ci.Data("Cicy3", wlexpr('#["Euler"] == -200 &'))`. Numeric and symbolic results use the Wolfram client's WXF representations, with exact results also available as bytes.
- Wolfram `call_result` and `evaluate_result` return the value, WXF bytes, kernel status, messages and printed output. `call` and `evaluate` raise `EvaluationError` on kernel failures or messages. The exception's `detail` retains diagnostics. Startup diagnostics are available as `ci.startup`.
- One client owns a persistent kernel and a fresh temporary copy of the package data. `SaveData` writes to that session copy by default. To retain a dataset, export it to your chosen path before closing the client. `DeleteData` uses upstream interactive input, and opening notebooks with `CIExample` requires a compatible notebook front end. Check the result diagnostics for these calls when using a headless kernel.
- Startup and evaluation have time limits. Pass `startup_timeout=` or `evaluation_timeout=` in seconds, or `evaluation_timeout=None` for long-running computations. A timeout closes the kernel and clears its session-local state.

See the [method concordance](docs/concordance.md) and the [Python](docs/python/api.md) and [Wolfram Language](docs/wolfram/api.md) API guides for all exported functions, dispatch keys, and dataset formats. See [manuscript rendering](docs/manuscript.md) to reproduce the PDF using the pinned `docxology/template` engine.

## Upstream source and reproduction

The Git history descends from [JamesGray-Physics/CIPro](https://github.com/JamesGray-Physics/CIPro) `main` at `964037b9e7680c5fcd245e130cd6026da86ffbf2`, with upstream tag `v1.0` at `1533b83cf87c4741e60b4d3233745439a4eee094`. The GitHub release asset differs from the archives in the Git history. `src/py_cipro/vendor/CIProPackage.zip` preserves the complete [v1.0 release asset](https://github.com/JamesGray-Physics/CIPro/releases/tag/v1.0) byte for byte, including `CIPro.m`, auxiliary code, eight built-in datasets, examples and manuals. Its SHA-256 is `39223db768893c958be776071bcbf86d0ef5692f92e1ab153ef1ce8d3440dd53`.

On startup the wrapper verifies the archive, extracts it to a private temporary directory, and relocates five hard-coded application-path references in the temporary `CIPro.m`. The original release bytes and upstream algorithms are preserved. Each session checks the public definitions and dispatch registry after loading the package. See `CIProData/DataInfo.txt` within the release for the dataset source attributions.

For the upstream package, cite Lara B. Anderson, Andrei Constantin, James Gray, Yang-Hui He, Seung-Joo Lee, and Andre Lukas, *CIPro Package: Complete Intersections in Products of Projective Spaces and Line Bundles*, [arXiv:2606.27588](https://arxiv.org/abs/2606.27588).

For the Python software and its research outputs, use the versioned citation
metadata and identify the release used for the calculation.
[Citation metadata](CITATION.cff) · [Zenodo archive, version 0.9.3](https://doi.org/10.5281/zenodo.24352380) · [All Zenodo versions](https://doi.org/10.5281/zenodo.24352379) · [GitHub releases](https://github.com/docxology/py-CIPro/releases)

## Verification

```sh
python -m unittest discover -s tests -v
WOLFRAM_KERNEL='/path/to/WolframKernel' py-cipro-qualify > native-qualification.json
WOLFRAM_KERNEL='/path/to/WolframKernel' python -m unittest discover -s tests -p 'test_live.py' -v
```

The offline suite checks archive integrity and scientific fixtures, source-to-catalog coverage, the loopback API, and the Python-to-WXF boundary. The qualification command emits a JSON receipt with the release digest, kernel version, system ID, and results for the quintic, bicubic, tetraquadric, and native dataset count. The live suite runs when `WOLFRAM_KERNEL` is set and checks CIPro computations and dataset access in the activated kernel. Binary datasets use Wolfram `DumpSave` and require a compatible kernel/system.
