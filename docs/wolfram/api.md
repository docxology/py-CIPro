# Wolfram Language API for CIPro v1.0

Install the release's `CIPro.m`, `CIProAux`, `CIProData`, and `CIProExamples` in the Wolfram user applications directory. Load the package from a Wolfram notebook or kernel. The Python wrapper locates the same pinned release automatically when using its Wolfram backend. [CIPro v1.0 release](https://github.com/JamesGray-Physics/CIPro/releases/tag/v1.0) · [Python API](../python/api.md) · [Method concordance](../concordance.md)

The dashboard offers **Wolfram** for eligible methods and starts a local kernel when a request needs it. Set `WOLFRAM_KERNEL` when automatic discovery fails. The dashboard accepts a restricted set of symbolic JSON tags. A Wolfram notebook or the Python library's Wolfram backend provides the broader native expression interface. [Dashboard and method lab](../dashboard.md)

```wolfram
Needs["CIPro`"];
quintic = <|"Conf" -> {{5}}, "DimPs" -> {4}|>;
result = CIProp[quintic, {"CIDim", "CY", "Euler"}];
Lookup[result, {"CIDim", "CY", "Euler"}]
(* {3, True, -200} *)
```

## Geometry and dispatch

`DimPs` gives the ambient projective dimensions in row order. Each column of `Conf` gives the multidegree of a defining equation. For example, the bicubic in the product of two projective planes is `<|"DimPs" -> {2, 2}, "Conf" -> {{3}, {3}}|>`. Supply `DimPs` explicitly for a non-Calabi–Yau configuration. CIPro's missing-dimension default is `Max[Total[row], 2] - 1` for each row. With explicit geometry, `CY` tests the configuration's zero first Chern class condition by comparing row totals minus one with `DimPs`. Smoothness is a separate geometric question. [CIPro paper, Section 2](https://arxiv.org/html/2606.27588v1#S2)

### `CIProp`

The dispatcher creates dependencies required for the requested keys. It preserves an existing key from the input association, so passing an archived `Euler` field back to `CIProp` with `"Euler"` would reuse that field. To recompute, pass a fresh association with only the required inputs. `"Format" -> "Full"` returns the input and computed keys. `"Format" -> "Medium"` returns the newly computed association, which can include dependencies. The short branch takes the last newly computed result. For one specific answer, use `"Format" -> "Full"` and select the named key.

| Category | Keys |
| --- | --- |
| Geometry | `Conf`, `DimPs`, `AmbCoords`, `AmbDim`, `CIDim`, `CY`, `Mu`, `ISecForm`, `ISec`, `CPoly`, `C`, `ChPoly`, `Ch`, `TdPoly`, `Td`, `Euler`, `K`, `MonList`, `DefEqs`, `Singular`, `SingularLocus`, `GVInv`, `HilbertSeries` |
| Group data | `Gen`, `GenOrder`, `Abelian`, `ProjAbelian`, `Group`, `Order`, `ProjTrivialGroup`, `ProjTrivialOrder`, `ProjGroup`, `ProjOrder`, `PermGroupGen` |
| Group actions on complete intersections | `ConfInvQ`, `InvQ`, `InvMon` |
| Line bundles | `LBS`, `LBSRank`, `ChLBSPoly`, `ChLBS`, `CLBSPoly`, `CLBS`, `IndLBS`, `CohList`, `Basis`, `AmbCohDim`, `Coset`, `CohInfo`, `LBSCohDim` |

Common options include `"CoeffRange" -> {1, 100}` and `"CoeffType" -> "Integer"` for generated coefficients, `"FieldChar" -> 101` for applicable finite-field checks, `"MaxDeg" -> 5` for invariant degree, `"CohQ" -> 0` for cohomological degree, and `Eqs` for supplied defining equations. `"HilbertFormat" -> {}` requests closed form, an integer requests a total-degree bound, and an integer vector sets a multidegree bound. Pass only options applicable to the selected calculation. The dispatch key and Wolfram head can differ, for example `Euler` calls `EulerCI`, `CY` calls `CYQ`, and `LBS` uses the private `DefLBS` definition. [CIPro paper, Appendix B](https://arxiv.org/html/2606.27588v1#A2)

### `CIMod`

`CIMod` accepts either an association or a list of associations and fills operation-specific dependencies. The result can be a modified association, a scalar comparison, a matrix, or another Wolfram expression. Options control particular operations and return shapes.

| Category | Keys |
| --- | --- |
| Configurations | `CINormal`, `CIEquiv` |
| Bundle algebra | `LBSSum`, `LBSTensor`, `LBSWedge`, `LBSSymm` |
| Maps and cohomology | `MapLBS`, `MapSpaceLBS`, `QuotientLBS`, `DirectSumLBS`, `KoszulLBS`, `CohLBS` |

`CINormal` returns the normal configuration, reordered ambient dimensions, and row and column permutation matrices. `CIEquiv` tests equality under row and column permutations. For symmetric and exterior bundle powers, set `TensorPower`. `MapSpaceLBS` supports `Map` and `Space` with `"Ker"`, `"Im"`, or `"Coker"`. `CohLBS` has `"CohFormat" -> "Dim"` for dimensions and `"CohSum" -> True` in the released option table. Pass `CohSum` explicitly when the per-summand shape matters. `Modulus`, `Ekpq`, and `CohProt` apply to the corresponding cohomology or Koszul operations. Some cohomology paths call legacy Wolfram `Combinatorica`; requesting a separate protocol window also requires a notebook front end. [CIPro paper, Sections 2 and 3](https://arxiv.org/html/2606.27588v1#S3) · [Wolfram Combinatorica reference](https://reference.wolfram.com/language/Combinatorica/ref/Compositions.html)

```wolfram
bundle = <|
    "DimPs" -> {2, 4},
    "Conf" -> {{1, 1, 1}, {2, 2, 1}},
    "LBS" -> {{1, 1, -5}, {1, -1, 2}}
|>;
exterior = CIMod[bundle, "LBSWedge", "TensorPower" -> 2];
exterior["LBS"]
(* {{2, -4, -4}, {0, 3, 1}} *)
```

Each column of `LBS` is a charge vector. The expected columns in this example are the pairwise sums of the three distinct input summands.

### All callable public Wolfram heads

Names below are grouped by usage. The [source-derived catalog](../../src/py_cipro/_catalog.py) defines the Python dispatch set. The release's `CIPro.m` gives the function patterns and checks. The notebooks, manual, and paper demonstrate higher-level usage.

| Area | Names |
| --- | --- |
| Dispatch, data, help, display | `CIPro`, `CIProp`, `CIMod`, `CICheck`, `CIExample`, `Data`, `SaveData`, `DeleteData`, `HelpPrint`, `InfoPrint`, `StPrint`, `WarningPrint`, `ErrorPrint`, `MM`, `MMList`, `MD` |
| Configurations and characteristic classes | `AmbCoords`, `AmbDim`, `DefConf`, `DimPs`, `CIDim`, `CYQ`, `CINormal`, `CIEquiv`, `CIEquiv2`, `CCI`, `CCIPoly`, `ChCI`, `ChCIPoly`, `TdCI`, `TdCIPoly`, `Class2Class`, `ClassConvert`, `Intersec`, `IntersecForm`, `EulerCI`, `KCI`, `Mu`, `GVInvariants`, `HilbertSeries`, `HilbertExpand` |
| Defining equations and algebra | `DefEqs`, `GenericDefEqs`, `InvDefEqs`, `MList`, `MMonList`, `RandomPoly`, `SingularityCheck`, `SingularityLocus`, `TransformPoly`, `ReynoldsPoly` |
| Matrices, groups and actions | `BlockMatrix`, `BlockMatrix2`, `MatNormal`, `MatProjEquiv`, `MatProjTrivial`, `SymmMatNormal`, `SymmMatNormal0`, `PermMatrix`, `PermGroupGen`, `ArrangeGen`, `Gen`, `GenGroup`, `GenOrder`, `GOrder`, `Abelian`, `ProjAbelian`, `ProjGenGroup`, `ProjOrder`, `ProjTrivialGroup`, `ProjTrivialOrder`, `ConfInvQ`, `InvQ`, `InvMon` |
| Bundles and cohomology | `CLBS`, `CLBSPoly`, `ChLBPoly`, `ChLBS`, `ChLBSPoly`, `LBSRank`, `IndLBS`, `LineSymm`, `LineTensor`, `LineWedge`, `LBSSum`, `LBSTensor`, `LBSSymm`, `LBSWedge`, `DirectSumLBS`, `QuotientLBS`, `MapLBS`, `MapSpaceLBS`, `KoszulLBS`, `CohLBS`, `CohInfo`, `CohList`, `LBSCohDim`, `AmbCohDim`, `Basis`, `Coset` |

Direct calls use the Wolfram function's native arguments and can require preparatory keys that the dispatchers supply automatically. Ask the kernel for a help string or the upstream options as follows.

```wolfram
CIProp["Keys"]
CIProp::usage
Options[CIProp]
CIProp["Euler"]
```

## Inputs for the ambient divisibility analyses

Use `CIProp[g, {"ISec", "C"}]` with a fresh geometry association containing
`DimPs` and `Conf` to obtain the intersection tensor and Chern data.
The cubic signature applies integer gcds to tensor evaluations and
the ordered second Chern pairings. Use `IndLBS` with ambient charges
in `LBS` to check individual values of the line-bundle index.
The manuscript gives the finite generators for the gcd of the whole
index polynomial. [Research guide](../research.md#recompute-the-ambient-divisibility-studies)

## Dataset calls

| Call | Interpretation |
| --- | --- |
| `Data[]` | Print the dataset list and general help. |
| `Data["Cicy3"]` | Print the named dataset description. The optional second argument `"String"` prints the description in plain form. |
| `Data["Cicy3", "Length"]` | Dataset length. |
| `Data["Cicy3", 1]` | The first association. Indexing is one-based. |
| `Data["Cicy3", {1, 3}, {"Num", "H11", "H21"}]` | Inclusive range, returning a row of values in the requested key order for each record. A single projected key yields one list of values. |
| `Data["Cicy3", All]` | Entire dataset. Use a range and a key projection for large collections. |
| `Data["Cicy3", #["Euler"] == -200 &, "Num"]` | Evaluate a trusted selection predicate and return matching numbers. |

The eight datasets are `Cicy3`, `Cicy3Favour`, `Cicy3FavourSym`, `Cicy3Sym`, `Cicy4`, `LBSStandardModels`, `LBSStandardModels202`, and `delPezzo2`. Their attribution and fields are described in the release's `CIProData/DataInfo.txt` and in the paper. `Cicy3` is Wolfram Language text. The other seven are Wolfram binary dumps, whose compatibility depends on the target kernel platform. [CIPro paper, Appendix C](https://arxiv.org/html/2606.27588v1#A3) · [Wolfram DumpSave reference](https://reference.wolfram.com/language/ref/DumpSave.html)

`SaveData` writes a list of associations into the configured data directory and updates its metadata. In a standalone Wolfram session the destination is the configured `DataPath`. The Python wrapper gives each owned Wolfram session a temporary data directory. `DeleteData` prompts for confirmation using Wolfram `Input`. `CIExample[]` lists examples, while opening a named example uses notebook functions. Prefer the short help forms in headless workflows and open the bundled notebooks in Mathematica for interactive examples.
