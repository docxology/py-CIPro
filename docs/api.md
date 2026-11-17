# CIPro v1.0 API

`call(name, *args, **options)` invokes the corresponding public Wolfram Language symbol in the `` CIPro` `` context. The [Python catalog](../src/py_cipro/_catalog.py) contains all 100 function names found in the bundled `CIPro.m`. Direct functions accept their Wolfram argument forms. Where the package computes prerequisites, use `property` or `modify` to ask CIPro to resolve them.

`property(geometry, key, **options)` calls `CIProp`. Pass an association as a Python dictionary and a key or list of keys. The upstream default `"Format" -> "Full"` returns the input association extended with requested properties and their dependencies. Already populated keys are reused by CIPro.

| CIProp category | Keys |
| --- | --- |
| Complete intersections | `Conf`, `DimPs`, `AmbCoords`, `AmbDim`, `CIDim`, `CY`, `Mu`, `ISecForm`, `ISec`, `CPoly`, `C`, `ChPoly`, `Ch`, `TdPoly`, `Td`, `Euler`, `K`, `MonList`, `DefEqs`, `Singular`, `SingularLocus`, `GVInv`, `HilbertSeries` |
| Symmetries | `Gen`, `GenOrder`, `Abelian`, `ProjAbelian`, `Group`, `Order`, `ProjTrivialGroup`, `ProjTrivialOrder`, `ProjGroup`, `ProjOrder`, `PermGroupGen` |
| Complete intersections with symmetries | `ConfInvQ`, `InvQ`, `InvMon` |
| Line-bundle sums and cohomology | `LBS`, `LBSRank`, `ChLBSPoly`, `ChLBS`, `CLBSPoly`, `CLBS`, `IndLBS`, `CohList`, `Basis`, `AmbCohDim`, `Coset`, `CohInfo`, `LBSCohDim` |

`modify(geometry, key, **options)` calls `CIMod`. Depending on the operation, the first argument is an association or a sequence of associations. The result can be a new association, matrix, scalar, or another Wolfram expression.

| CIMod category | Keys |
| --- | --- |
| Complete intersections | `CINormal`, `CIEquiv` |
| Line-bundle sums and cohomology | `LBSSum`, `LBSTensor`, `LBSWedge`, `LBSSymm`, `MapLBS`, `MapSpaceLBS`, `QuotientLBS`, `DirectSumLBS`, `KoszulLBS`, `CohLBS` |

The `LBS` property uses an internal `DefLBS` definition. Request it through `property(geometry, "LBS")`. The property and operation tables follow the registries in the [v1.0 release](https://github.com/JamesGray-Physics/CIPro/releases/tag/v1.0). See Appendix B for documented options and Sections 2–4 for worked Wolfram Language examples. [CIPro paper](https://arxiv.org/html/2606.27588v1#A2)

## Datasets and interactive functions

`Data` accepts an exact dataset name, optionally followed by a one-based index, inclusive two-index range, `"Length"`, Wolfram `All`, or a Wolfram selector function. An optional third argument chooses keys from the selected records. The bundled catalogs are `Cicy3`, `Cicy3Favour`, `Cicy3FavourSym`, `Cicy3Sym`, `Cicy4`, `LBSStandardModels`, `LBSStandardModels202`, and `delPezzo2`. `Cicy3` is Wolfram Language source. The other seven are Wolfram binary dumps and require a compatible kernel. [CIPro dataset reference](https://arxiv.org/html/2606.27588v1#A3), [Wolfram DumpSave documentation](https://reference.wolfram.com/language/ref/DumpSave.html)

`SaveData` writes a dataset and its metadata to CIPro's configured data directory. `DeleteData` uses Wolfram `Input` to ask for confirmation. `CIExample[]` lists examples, and opening an example by name uses Mathematica notebook front-end functions. CIPro also uses `Print` for banners, help, and dataset information, so those calls can return Wolfram `Null` while producing output. [CIPro release and examples](https://github.com/JamesGray-Physics/CIPro/releases/tag/v1.0)
