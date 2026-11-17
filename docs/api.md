# Python API for CIPro v1.0

py-CIPro loads the pinned Wolfram Language release and exposes its callable public symbols. The wrapper starts a persistent kernel, marshals expressions in Wolfram Expression Format (WXF), and captures the kernel's value and diagnostics. The released CIPro code implements the mathematics. See the [Wolfram backend guide](wolfram-api.md) for local, remote, and cloud evaluation paths.

## Session and evaluation

```python
from py_cipro import CIPro

with CIPro() as ci:
    print(ci.functions)
    print(ci.properties)
    print(ci.modifications)
```

| Python interface | Behavior |
| --- | --- |
| `CIPro(kernel=None, *, startup_timeout=180, evaluation_timeout=600)` | Use the specified executable path, `WOLFRAM_KERNEL`, or Wolfram Client automatic discovery, in that order. Timeouts are in seconds. An evaluation timeout of `None` removes the Python-side wait limit. |
| `start()`, `close()`, context manager | Start explicitly or on the first evaluation. A successful start loads CIPro from a fresh private temporary directory. Closing terminates the owned kernel and removes its temporary application and data files. |
| `call(name, *args, **options)`, `ci.Name(...)` | Invoke an exact, case-sensitive public Wolfram symbol in the `` CIPro` `` context. A name outside the callable catalog raises `ValueError` from `call`; absent attribute access raises `AttributeError`. |
| `property(geometry, keys, **options)` | Invoke `CIProp` with a string key or list of keys. |
| `modify(geometry, key, **options)` | Invoke `CIMod` with one operation key. |
| `evaluate(expression)` | Evaluate a trusted Wolfram expression in the same kernel. |
| `call_result(name, ...)`, `evaluate_result(expression)` | Return an `Evaluation` containing `value`, `success`, `messages`, `output`, raw result `wxf` bytes, and `failure`. Kernel-start and transport failures still raise. |
| `startup` | The most recent package-load `Evaluation`. The loader checks that all public function definitions and both dispatch registries are present. Inspect its output and messages for the load diagnostics. |

Calls on one client are serialized, and package options, loaded datasets, and other Wolfram definitions persist within that client. A timeout or kernel transport failure closes the owned kernel and its extracted data. A subsequent call starts a fresh session. `call` and `evaluate` raise `EvaluationError` when an evaluation is unsuccessful, including kernel statuses caused by messages and results such as `$Failed` or `$Aborted`. Inspect `exc.detail` to retain the outcome. Help and data notices can be emitted through Wolfram `Print` and appear in `output`.

### Values and options

Pass Python lists as Wolfram lists and dictionaries as Wolfram associations. Plain Python strings are literal Wolfram strings. Use `wl` for a symbol or expression and `wlexpr` to parse trusted Wolfram source text. For example, `wl.All` is the Wolfram symbol used to select every dataset row. `"All"` is a string. Pass package options as Python kwargs such as `Format="Medium"` or as explicit Wolfram rules such as `wl.Rule("Format", "Medium")`. The wrapper's keyword arguments use **string** keys. For Wolfram options that require symbol keys, build the corresponding rules explicitly.

WXF results can contain immutable mappings, tuples, exact numeric objects, arrays, or symbolic heads. Use the returned structure directly in later Wolfram calls. Export `Evaluation.wxf` when a record needs exact symbolic values and preserve associated diagnostics and provenance separately. JSON is appropriate for the dashboard's bounded numeric and Boolean schema. [Wolfram Client expression and serialization guide](https://reference.wolfram.com/language/WolframClientForPython/docpages/basic_usages.html)

```python
from pathlib import Path
from py_cipro import CIPro, wl

quintic = {"DimPs": [4], "Conf": [[5]]}

with CIPro() as ci:
    outcome = ci.call_result("CIProp", quintic, ["CIDim", "CY", "Euler"])
    if not outcome.success:
        raise RuntimeError(outcome.messages or outcome.failure or outcome.value)
    Path("quintic-result.wxf").write_bytes(outcome.wxf)
    print(outcome.value["CIDim"], outcome.value["CY"], outcome.value["Euler"])
    print(ci.evaluate(getattr(wl, "System`$Version")))
```

The expected invariants for a smooth quintic are `3`, `True`, and `-200`. Use `getattr(wl, name)` when a Wolfram symbol contains characters that are unavailable in Python attribute syntax.

## Geometry and dispatch

`DimPs` gives the ambient projective dimensions in row order. Each column of `Conf` gives the multidegree of a defining equation. For example, the bicubic in the product of two projective planes is `{"DimPs": [2, 2], "Conf": [[3], [3]]}`. Supply `DimPs` explicitly for a non-Calabi–Yau configuration. CIPro's missing-dimension default is `Max[Total[row], 2] - 1` for each row. With explicit geometry, `CY` tests the configuration's zero first Chern class condition by comparing row totals minus one with `DimPs`. Smoothness is a separate geometric question. [CIPro paper, Section 2](https://arxiv.org/html/2606.27588v1#S2)

### `CIProp`

The dispatcher creates dependencies required for the requested keys. It preserves an existing key from the input association, so passing an archived `Euler` field back to `CIProp` with `"Euler"` would reuse that field. To recompute, pass a fresh association with only the required inputs. `Format="Full"` returns the input and computed keys. `Format="Medium"` returns the newly computed association, which can include dependencies. The short branch takes the last newly computed result. For one specific answer, use `Format="Full"` and select the named key.

| Category | Keys |
| --- | --- |
| Geometry | `Conf`, `DimPs`, `AmbCoords`, `AmbDim`, `CIDim`, `CY`, `Mu`, `ISecForm`, `ISec`, `CPoly`, `C`, `ChPoly`, `Ch`, `TdPoly`, `Td`, `Euler`, `K`, `MonList`, `DefEqs`, `Singular`, `SingularLocus`, `GVInv`, `HilbertSeries` |
| Group data | `Gen`, `GenOrder`, `Abelian`, `ProjAbelian`, `Group`, `Order`, `ProjTrivialGroup`, `ProjTrivialOrder`, `ProjGroup`, `ProjOrder`, `PermGroupGen` |
| Group actions on complete intersections | `ConfInvQ`, `InvQ`, `InvMon` |
| Line bundles | `LBS`, `LBSRank`, `ChLBSPoly`, `ChLBS`, `CLBSPoly`, `CLBS`, `IndLBS`, `CohList`, `Basis`, `AmbCohDim`, `Coset`, `CohInfo`, `LBSCohDim` |

Common options include `CoeffRange=[1, 100]` and `CoeffType="Integer"` for generated coefficients, `FieldChar=101` for applicable finite-field checks, `MaxDeg=5` for invariant degree, `CohQ=0` for cohomological degree, and `Eqs` for supplied defining equations. `HilbertFormat=[]` requests closed form, an integer requests a total-degree bound, and an integer vector sets a multidegree bound. Pass only options applicable to the selected calculation. The dispatch key and Wolfram head can differ, for example `Euler` calls `EulerCI`, `CY` calls `CYQ`, and `LBS` uses the private `DefLBS` definition. [CIPro paper, Appendix B](https://arxiv.org/html/2606.27588v1#A2)

### `CIMod`

`CIMod` accepts either an association or a list of associations and fills operation-specific dependencies. The result can be a modified association, a scalar comparison, a matrix, or another Wolfram expression. Options control particular operations and return shapes.

| Category | Keys |
| --- | --- |
| Configurations | `CINormal`, `CIEquiv` |
| Bundle algebra | `LBSSum`, `LBSTensor`, `LBSWedge`, `LBSSymm` |
| Maps and cohomology | `MapLBS`, `MapSpaceLBS`, `QuotientLBS`, `DirectSumLBS`, `KoszulLBS`, `CohLBS` |

`CINormal` returns the normal configuration, reordered ambient dimensions, and row and column permutation matrices. `CIEquiv` tests equality under row and column permutations. For symmetric and exterior bundle powers, set `TensorPower`. `MapSpaceLBS` supports `Map` and `Space` with `"Ker"`, `"Im"`, or `"Coker"`. `CohLBS` has `CohFormat="Dim"` for dimensions and `CohSum=True` in the released option table. Pass `CohSum` explicitly when the per-summand shape matters. `Modulus`, `Ekpq`, and `CohProt` apply to the corresponding cohomology or Koszul operations. Some cohomology paths call legacy Wolfram `Combinatorica`; requesting a separate protocol window also requires a notebook front end. [CIPro paper, Sections 2 and 3](https://arxiv.org/html/2606.27588v1#S3) · [Wolfram Combinatorica reference](https://reference.wolfram.com/language/Combinatorica/ref/Compositions.html)

```python
from py_cipro import CIPro

bundle = {
    "DimPs": [2, 4],
    "Conf": [[1, 1, 1], [2, 2, 1]],
    "LBS": [[1, 1, -5], [1, -1, 2]],
}

with CIPro() as ci:
    exterior = ci.modify(bundle, "LBSWedge", TensorPower=2)
    assert tuple(map(tuple, exterior["LBS"])) == ((2, -4, -4), (0, 3, 1))
```

Each column of `LBS` is a charge vector. The expected columns in this example are the pairwise sums of the three distinct input summands.

### All callable public Wolfram heads

Names below are grouped by usage. The [source-derived catalog](../src/py_cipro/_catalog.py) defines the Python dispatch set. The release's `CIPro.m` gives the function patterns and checks. The notebooks, manual, and paper demonstrate higher-level usage.

| Area | Names |
| --- | --- |
| Dispatch, data, help, display | `CIPro`, `CIProp`, `CIMod`, `CICheck`, `CIExample`, `Data`, `SaveData`, `DeleteData`, `HelpPrint`, `InfoPrint`, `StPrint`, `WarningPrint`, `ErrorPrint`, `MM`, `MMList`, `MD` |
| Configurations and characteristic classes | `AmbCoords`, `AmbDim`, `DefConf`, `DimPs`, `CIDim`, `CYQ`, `CINormal`, `CIEquiv`, `CIEquiv2`, `CCI`, `CCIPoly`, `ChCI`, `ChCIPoly`, `TdCI`, `TdCIPoly`, `Class2Class`, `ClassConvert`, `Intersec`, `IntersecForm`, `EulerCI`, `KCI`, `Mu`, `GVInvariants`, `HilbertSeries`, `HilbertExpand` |
| Defining equations and algebra | `DefEqs`, `GenericDefEqs`, `InvDefEqs`, `MList`, `MMonList`, `RandomPoly`, `SingularityCheck`, `SingularityLocus`, `TransformPoly`, `ReynoldsPoly` |
| Matrices, groups and actions | `BlockMatrix`, `BlockMatrix2`, `MatNormal`, `MatProjEquiv`, `MatProjTrivial`, `SymmMatNormal`, `SymmMatNormal0`, `PermMatrix`, `PermGroupGen`, `ArrangeGen`, `Gen`, `GenGroup`, `GenOrder`, `GOrder`, `Abelian`, `ProjAbelian`, `ProjGenGroup`, `ProjOrder`, `ProjTrivialGroup`, `ProjTrivialOrder`, `ConfInvQ`, `InvQ`, `InvMon` |
| Bundles and cohomology | `CLBS`, `CLBSPoly`, `ChLBPoly`, `ChLBS`, `ChLBSPoly`, `LBSRank`, `IndLBS`, `LineSymm`, `LineTensor`, `LineWedge`, `LBSSum`, `LBSTensor`, `LBSSymm`, `LBSWedge`, `DirectSumLBS`, `QuotientLBS`, `MapLBS`, `MapSpaceLBS`, `KoszulLBS`, `CohLBS`, `CohInfo`, `CohList`, `LBSCohDim`, `AmbCohDim`, `Basis`, `Coset` |

Direct calls use the Wolfram function's native arguments and can require preparatory keys that the dispatchers supply automatically. Ask the kernel for a help string or the upstream options as follows.

```python
from py_cipro import CIPro, wl

with CIPro() as ci:
    cipro_prop = getattr(wl, "CIPro`CIProp")
    usage = ci.evaluate(wl.MessageName(cipro_prop, "usage"))
    options = ci.evaluate(wl.Options(cipro_prop))
    help_output = ci.call_result("CIProp", "Euler").output
```

## Dataset calls

| Call | Interpretation |
| --- | --- |
| `ci.call_result("Data")` | Package dataset list and general help in `output`. |
| `ci.call_result("Data", "Cicy3")` | Named dataset description in `output`. The optional second argument `"String"` prints the description in plain form. |
| `ci.Data("Cicy3", "Length")` | Dataset length. |
| `ci.Data("Cicy3", 1)` | The first association. Indexing is one-based. |
| `ci.Data("Cicy3", [1, 3], ["Num", "H11", "H21"])` | Inclusive range, returning a row of values in the requested key order for each record. A single projected key yields one list of values. |
| `ci.Data("Cicy3", wl.All)` | Entire dataset. Use a range and a key projection for large collections. |
| `ci.Data("Cicy3", wlexpr('#["Euler"] == -200 &'), "Num")` | Evaluate a trusted selection predicate and return matching numbers. |

The eight datasets are `Cicy3`, `Cicy3Favour`, `Cicy3FavourSym`, `Cicy3Sym`, `Cicy4`, `LBSStandardModels`, `LBSStandardModels202`, and `delPezzo2`. Their attribution and fields are described in the release's `CIProData/DataInfo.txt` and in the paper. `Cicy3` is Wolfram Language text. The other seven are Wolfram binary dumps, whose compatibility depends on the target kernel platform. [CIPro paper, Appendix C](https://arxiv.org/html/2606.27588v1#A3) · [Wolfram DumpSave reference](https://reference.wolfram.com/language/ref/DumpSave.html)

`SaveData` writes a list of associations into the configured data directory and updates its metadata. With default settings these writes are session-local. Keep durable results by saving their WXF or exporting to an explicit path before closing the client. `DeleteData` prompts for confirmation using Wolfram `Input`. `CIExample[]` lists examples, while opening a named example uses notebook functions. Prefer the short help forms in headless workflows and open the bundled notebooks in Mathematica for interactive examples.
