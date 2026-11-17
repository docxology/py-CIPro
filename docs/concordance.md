# Method concordance for CIPro v1.0

Native Python covers **88 of 100 public functions**, **48 of 50 property keys**, and **12 of 12 modification keys**. Coverage describes registered implementations within their supported argument domains. Live Wolfram parity has not been established. See the [Python guide](python/api.md) and [Wolfram Language guide](wolfram/api.md) for options and result representations.

For the Python calls below, construct `CIPro(backend="python")` to run locally. Every released function and key can also be invoked through Python with `backend="wolfram"`. Wolfram calls assume `Needs["CIPro`"]` or an equivalent package load. Ellipses denote positional arguments or options.

## Public functions

| Method | Python call | Wolfram call | Native availability |
| --- | --- | --- | --- |
| `Abelian` | `ci.Abelian(…)` | `Abelian[…]` | Python and Wolfram |
| `AmbCohDim` | `ci.AmbCohDim(…)` | `AmbCohDim[…]` | Python and Wolfram |
| `AmbCoords` | `ci.AmbCoords(…)` | `AmbCoords[…]` | Python and Wolfram |
| `AmbDim` | `ci.AmbDim(…)` | `AmbDim[…]` | Python and Wolfram |
| `ArrangeGen` | `ci.ArrangeGen(…)` | `ArrangeGen[…]` | Python and Wolfram |
| `Basis` | `ci.Basis(…)` | `Basis[…]` | Python and Wolfram |
| `BlockMatrix` | `ci.BlockMatrix(…)` | `BlockMatrix[…]` | Python and Wolfram |
| `BlockMatrix2` | `ci.BlockMatrix2(…)` | `BlockMatrix2[…]` | Python and Wolfram |
| `CCI` | `ci.CCI(…)` | `CCI[…]` | Python and Wolfram |
| `CCIPoly` | `ci.CCIPoly(…)` | `CCIPoly[…]` | Python and Wolfram |
| `CICheck` | `ci.CICheck(…)` | `CICheck[…]` | Python and Wolfram. Association checks with Python warnings. |
| `CIDim` | `ci.CIDim(…)` | `CIDim[…]` | Python and Wolfram. Integer configurations. Retains the release's handling of negative columns. |
| `CIEquiv` | `ci.CIEquiv(…)` | `CIEquiv[…]` | Python and Wolfram. Integer configurations with bounded canonicalization. |
| `CIEquiv2` | `ci.CIEquiv2(…)` | `CIEquiv2[…]` | Python and Wolfram. Bounded integer evaluation with unique row and column signatures. |
| `CIExample` | `ci.CIExample(…)` | `CIExample[…]` | Wolfram. Wolfram notebook help and examples. |
| `CIMod` | `ci.CIMod(…)` | `CIMod[…]` | Python and Wolfram. Native keys below. Python accepts the default Full format. |
| `CINormal` | `ci.CINormal(…)` | `CINormal[…]` | Python and Wolfram. Integer configurations with bounded canonicalization. |
| `CIPro` | `ci.CIPro(…)` | `CIPro[…]` | Wolfram. Wolfram help and option display. |
| `CIProp` | `ci.CIProp(…)` | `CIProp[…]` | Python and Wolfram. Native keys in the table below. Wolfram handles interactive help. |
| `CLBS` | `ci.CLBS(…)` | `CLBS[…]` | Python and Wolfram |
| `CLBSPoly` | `ci.CLBSPoly(…)` | `CLBSPoly[…]` | Python and Wolfram |
| `CYQ` | `ci.CYQ(…)` | `CYQ[…]` | Python and Wolfram |
| `ChCI` | `ci.ChCI(…)` | `ChCI[…]` | Python and Wolfram |
| `ChCIPoly` | `ci.ChCIPoly(…)` | `ChCIPoly[…]` | Python and Wolfram |
| `ChLBPoly` | `ci.ChLBPoly(…)` | `ChLBPoly[…]` | Python and Wolfram. Exact native line-bundle Chern character. |
| `ChLBS` | `ci.ChLBS(…)` | `ChLBS[…]` | Python and Wolfram |
| `ChLBSPoly` | `ci.ChLBSPoly(…)` | `ChLBSPoly[…]` | Python and Wolfram |
| `Class2Class` | `ci.Class2Class(…)` | `Class2Class[…]` | Python and Wolfram. Default symbolic basis. Direction and dimension bounds in the Python guide. |
| `ClassConvert` | `ci.ClassConvert(…)` | `ClassConvert[…]` | Python and Wolfram. Exact coefficients and intersection tensors in positive dimension. |
| `CohInfo` | `ci.CohInfo(…)` | `CohInfo[…]` | Python and Wolfram |
| `CohLBS` | `ci.CohLBS(…)` | `CohLBS[…]` | Python and Wolfram. Certified dimension-only cases in characteristic zero. |
| `CohList` | `ci.CohList(…)` | `CohList[…]` | Python and Wolfram |
| `ConfInvQ` | `ci.ConfInvQ(…)` | `ConfInvQ[…]` | Wolfram. The released configuration check contains an uninitialized loop. |
| `Coset` | `ci.Coset(…)` | `Coset[…]` | Python and Wolfram |
| `Data` | `ci.Data(…)` | `Data[…]` | Python and Wolfram. Released textual Cicy3 only. Exact records, indexing, ranges and field projections. |
| `DefConf` | `ci.DefConf(…)` | `DefConf[…]` | Python and Wolfram. Integer configuration matrices, including explicit `Conf`. |
| `DefEqs` | `ci.DefEqs(…)` | `DefEqs[…]` | Python and Wolfram. Explicit SymPy equations or Python-generated coefficients. |
| `DeleteData` | `ci.DeleteData(…)` | `DeleteData[…]` | Wolfram. Interactive Wolfram confirmation and deletion. |
| `DimPs` | `ci.DimPs(…)` | `DimPs[…]` | Python and Wolfram |
| `DirectSumLBS` | `ci.DirectSumLBS(…)` | `DirectSumLBS[…]` | Python and Wolfram. Prepared exact Bott–Borel–Weil associations. |
| `ErrorPrint` | `ci.ErrorPrint(…)` | `ErrorPrint[…]` | Wolfram. Formatted Wolfram output. |
| `EulerCI` | `ci.EulerCI(…)` | `EulerCI[…]` | Python and Wolfram |
| `GOrder` | `ci.GOrder(…)` | `GOrder[…]` | Python and Wolfram |
| `GVInvariants` | `ci.GVInvariants(…)` | `GVInvariants[…]` | Wolfram. Upstream Klemm instanton code. |
| `Gen` | `ci.Gen(…)` | `Gen[…]` | Python and Wolfram |
| `GenGroup` | `ci.GenGroup(…)` | `GenGroup[…]` | Python and Wolfram. Exact finite matrix groups within the native closure limit. |
| `GenOrder` | `ci.GenOrder(…)` | `GenOrder[…]` | Python and Wolfram. Finite numeric matrices up to the supported generator order limit. |
| `GenericDefEqs` | `ci.GenericDefEqs(…)` | `GenericDefEqs[…]` | Python and Wolfram. Integer multidegrees with native generated or symbolic coefficients. |
| `HelpPrint` | `ci.HelpPrint(…)` | `HelpPrint[…]` | Wolfram. Wolfram notebook help. |
| `HilbertExpand` | `ci.HilbertExpand(…)` | `HilbertExpand[…]` | Python and Wolfram. Finite exact series expansion through supported scalar or multidegree requests. |
| `HilbertSeries` | `ci.HilbertSeries(…)` | `HilbertSeries[…]` | Python and Wolfram. Closed rational form and supported coefficient expansions. |
| `IndLBS` | `ci.IndLBS(…)` | `IndLBS[…]` | Python and Wolfram |
| `InfoPrint` | `ci.InfoPrint(…)` | `InfoPrint[…]` | Wolfram. Formatted Wolfram output. |
| `Intersec` | `ci.Intersec(…)` | `Intersec[…]` | Python and Wolfram |
| `IntersecForm` | `ci.IntersecForm(…)` | `IntersecForm[…]` | Python and Wolfram |
| `InvDefEqs` | `ci.InvDefEqs(…)` | `InvDefEqs[…]` | Python and Wolfram. Equations from invariant monomials with native coefficients. |
| `InvMon` | `ci.InvMon(…)` | `InvMon[…]` | Python and Wolfram. Exact finite group actions with bounded candidate enumeration. |
| `InvQ` | `ci.InvQ(…)` | `InvQ[…]` | Python and Wolfram |
| `KCI` | `ci.KCI(…)` | `KCI[…]` | Python and Wolfram |
| `KoszulLBS` | `ci.KoszulLBS(…)` | `KoszulLBS[…]` | Python and Wolfram. Explicit SymPy defining equations and bounded supported differentials. |
| `LBSCohDim` | `ci.LBSCohDim(…)` | `LBSCohDim[…]` | Python and Wolfram |
| `LBSRank` | `ci.LBSRank(…)` | `LBSRank[…]` | Python and Wolfram |
| `LBSSum` | `ci.LBSSum(…)` | `LBSSum[…]` | Python and Wolfram |
| `LBSSymm` | `ci.LBSSymm(…)` | `LBSSymm[…]` | Python and Wolfram |
| `LBSTensor` | `ci.LBSTensor(…)` | `LBSTensor[…]` | Python and Wolfram |
| `LBSWedge` | `ci.LBSWedge(…)` | `LBSWedge[…]` | Python and Wolfram |
| `LineSymm` | `ci.LineSymm(…)` | `LineSymm[…]` | Python and Wolfram |
| `LineTensor` | `ci.LineTensor(…)` | `LineTensor[…]` | Python and Wolfram |
| `LineWedge` | `ci.LineWedge(…)` | `LineWedge[…]` | Python and Wolfram |
| `MD` | `ci.MD(…)` | `MD[…]` | Python and Wolfram |
| `MList` | `ci.MList(…)` | `MList[…]` | Python and Wolfram. Bounded deterministic exact monomials. |
| `MM` | `ci.MM(…)` | `MM[…]` | Wolfram. Wolfram MatrixForm display. |
| `MMList` | `ci.MMList(…)` | `MMList[…]` | Python and Wolfram. Bounded multigraded monomial enumeration. |
| `MMonList` | `ci.MMonList(…)` | `MMonList[…]` | Python and Wolfram. Bounded indexed-coordinate monomials for integer degrees. |
| `MapLBS` | `ci.MapLBS(…)` | `MapLBS[…]` | Python and Wolfram. Integer charge matrices and Python-generated map coefficients. |
| `MapSpaceLBS` | `ci.MapSpaceLBS(…)` | `MapSpaceLBS[…]` | Python and Wolfram. Prepared exact characteristic-zero map kernel, image and cokernel. |
| `MatNormal` | `ci.MatNormal(…)` | `MatNormal[…]` | Python and Wolfram. Integer input with bounded equal-tally blocks and candidate orders. |
| `MatProjEquiv` | `ci.MatProjEquiv(…)` | `MatProjEquiv[…]` | Python and Wolfram |
| `MatProjTrivial` | `ci.MatProjTrivial(…)` | `MatProjTrivial[…]` | Python and Wolfram |
| `Mu` | `ci.Mu(…)` | `Mu[…]` | Python and Wolfram |
| `PermGroupGen` | `ci.PermGroupGen(…)` | `PermGroupGen[…]` | Python and Wolfram |
| `PermMatrix` | `ci.PermMatrix(…)` | `PermMatrix[…]` | Python and Wolfram |
| `ProjAbelian` | `ci.ProjAbelian(…)` | `ProjAbelian[…]` | Python and Wolfram. Preserves the released self-comparison. See the Python guide. |
| `ProjGenGroup` | `ci.ProjGenGroup(…)` | `ProjGenGroup[…]` | Python and Wolfram. Exact numeric projective groups within the native limits. |
| `ProjOrder` | `ci.ProjOrder(…)` | `ProjOrder[…]` | Python and Wolfram |
| `ProjTrivialGroup` | `ci.ProjTrivialGroup(…)` | `ProjTrivialGroup[…]` | Python and Wolfram |
| `ProjTrivialOrder` | `ci.ProjTrivialOrder(…)` | `ProjTrivialOrder[…]` | Python and Wolfram |
| `QuotientLBS` | `ci.QuotientLBS(…)` | `QuotientLBS[…]` | Python and Wolfram. Prepared exact characteristic-zero Bott–Borel–Weil quotient. |
| `RandomPoly` | `ci.RandomPoly(…)` | `RandomPoly[…]` | Python and Wolfram. Native random coefficient generation with Python's RNG. |
| `ReynoldsPoly` | `ci.ReynoldsPoly(…)` | `ReynoldsPoly[…]` | Python and Wolfram |
| `SaveData` | `ci.SaveData(…)` | `SaveData[…]` | Wolfram. Wolfram DumpSave persistence. |
| `SingularityCheck` | `ci.SingularityCheck(…)` | `SingularityCheck[…]` | Python and Wolfram. Bounded affine Jacobian checks over characteristic zero or a prime field. |
| `SingularityLocus` | `ci.SingularityLocus(…)` | `SingularityLocus[…]` | Python and Wolfram. Bounded exact affine-patch generators and substitutions. |
| `StPrint` | `ci.StPrint(…)` | `StPrint[…]` | Wolfram. Formatted Wolfram output. |
| `SymmMatNormal` | `ci.SymmMatNormal(…)` | `SymmMatNormal[…]` | Python and Wolfram. Integer input with bounded equal-tally blocks and candidate orders. |
| `SymmMatNormal0` | `ci.SymmMatNormal0(…)` | `SymmMatNormal0[…]` | Python and Wolfram. Integer input with bounded equal-tally blocks and candidate orders. |
| `TdCI` | `ci.TdCI(…)` | `TdCI[…]` | Python and Wolfram |
| `TdCIPoly` | `ci.TdCIPoly(…)` | `TdCIPoly[…]` | Python and Wolfram |
| `TransformPoly` | `ci.TransformPoly(…)` | `TransformPoly[…]` | Python and Wolfram |
| `WarningPrint` | `ci.WarningPrint(…)` | `WarningPrint[…]` | Wolfram. Formatted Wolfram output. |

## CIProp keys

| Method | Python call | Wolfram call | Native availability |
| --- | --- | --- | --- |
| `Conf` | `ci.property(g, "Conf")` | `CIProp[g, "Conf"]` | Python and Wolfram. Integer configuration matrices, including explicit `Conf`. |
| `DimPs` | `ci.property(g, "DimPs")` | `CIProp[g, "DimPs"]` | Python and Wolfram |
| `AmbCoords` | `ci.property(g, "AmbCoords")` | `CIProp[g, "AmbCoords"]` | Python and Wolfram |
| `AmbDim` | `ci.property(g, "AmbDim")` | `CIProp[g, "AmbDim"]` | Python and Wolfram |
| `CIDim` | `ci.property(g, "CIDim")` | `CIProp[g, "CIDim"]` | Python and Wolfram. Integer configurations. Retains the release's handling of negative columns. |
| `CY` | `ci.property(g, "CY")` | `CIProp[g, "CY"]` | Python and Wolfram |
| `Mu` | `ci.property(g, "Mu")` | `CIProp[g, "Mu"]` | Python and Wolfram |
| `ISecForm` | `ci.property(g, "ISecForm")` | `CIProp[g, "ISecForm"]` | Python and Wolfram |
| `ISec` | `ci.property(g, "ISec")` | `CIProp[g, "ISec"]` | Python and Wolfram |
| `CPoly` | `ci.property(g, "CPoly")` | `CIProp[g, "CPoly"]` | Python and Wolfram |
| `C` | `ci.property(g, "C")` | `CIProp[g, "C"]` | Python and Wolfram |
| `ChPoly` | `ci.property(g, "ChPoly")` | `CIProp[g, "ChPoly"]` | Python and Wolfram |
| `Ch` | `ci.property(g, "Ch")` | `CIProp[g, "Ch"]` | Python and Wolfram |
| `TdPoly` | `ci.property(g, "TdPoly")` | `CIProp[g, "TdPoly"]` | Python and Wolfram |
| `Td` | `ci.property(g, "Td")` | `CIProp[g, "Td"]` | Python and Wolfram |
| `Euler` | `ci.property(g, "Euler")` | `CIProp[g, "Euler"]` | Python and Wolfram |
| `K` | `ci.property(g, "K")` | `CIProp[g, "K"]` | Python and Wolfram |
| `MonList` | `ci.property(g, "MonList")` | `CIProp[g, "MonList"]` | Python and Wolfram. Bounded indexed-coordinate monomials for integer degrees. |
| `DefEqs` | `ci.property(g, "DefEqs")` | `CIProp[g, "DefEqs"]` | Python and Wolfram. Explicit SymPy equations or Python-generated coefficients. |
| `Singular` | `ci.property(g, "Singular")` | `CIProp[g, "Singular"]` | Python and Wolfram. Bounded affine Jacobian checks over characteristic zero or a prime field. |
| `SingularLocus` | `ci.property(g, "SingularLocus")` | `CIProp[g, "SingularLocus"]` | Python and Wolfram. Bounded exact affine-patch generators and substitutions. |
| `GVInv` | `ci.property(g, "GVInv")` | `CIProp[g, "GVInv"]` | Wolfram. Upstream Klemm instanton code. |
| `HilbertSeries` | `ci.property(g, "HilbertSeries")` | `CIProp[g, "HilbertSeries"]` | Python and Wolfram. Closed rational form and supported coefficient expansions. |
| `Gen` | `ci.property(g, "Gen")` | `CIProp[g, "Gen"]` | Python and Wolfram |
| `GenOrder` | `ci.property(g, "GenOrder")` | `CIProp[g, "GenOrder"]` | Python and Wolfram. Finite numeric matrices up to the supported generator order limit. |
| `Abelian` | `ci.property(g, "Abelian")` | `CIProp[g, "Abelian"]` | Python and Wolfram |
| `ProjAbelian` | `ci.property(g, "ProjAbelian")` | `CIProp[g, "ProjAbelian"]` | Python and Wolfram. Preserves the released self-comparison. See the Python guide. |
| `Group` | `ci.property(g, "Group")` | `CIProp[g, "Group"]` | Python and Wolfram. Exact finite matrix groups within the native closure limit. |
| `Order` | `ci.property(g, "Order")` | `CIProp[g, "Order"]` | Python and Wolfram |
| `ProjTrivialGroup` | `ci.property(g, "ProjTrivialGroup")` | `CIProp[g, "ProjTrivialGroup"]` | Python and Wolfram |
| `ProjTrivialOrder` | `ci.property(g, "ProjTrivialOrder")` | `CIProp[g, "ProjTrivialOrder"]` | Python and Wolfram |
| `ProjGroup` | `ci.property(g, "ProjGroup")` | `CIProp[g, "ProjGroup"]` | Python and Wolfram. Exact numeric projective groups within the native limits. |
| `ProjOrder` | `ci.property(g, "ProjOrder")` | `CIProp[g, "ProjOrder"]` | Python and Wolfram |
| `PermGroupGen` | `ci.property(g, "PermGroupGen")` | `CIProp[g, "PermGroupGen"]` | Python and Wolfram |
| `ConfInvQ` | `ci.property(g, "ConfInvQ")` | `CIProp[g, "ConfInvQ"]` | Wolfram. The released configuration check contains an uninitialized loop. |
| `InvQ` | `ci.property(g, "InvQ")` | `CIProp[g, "InvQ"]` | Python and Wolfram |
| `InvMon` | `ci.property(g, "InvMon")` | `CIProp[g, "InvMon"]` | Python and Wolfram. Exact finite group actions with bounded candidate enumeration. |
| `LBS` | `ci.property(g, "LBS")` | `CIProp[g, "LBS"]` | Python and Wolfram |
| `LBSRank` | `ci.property(g, "LBSRank")` | `CIProp[g, "LBSRank"]` | Python and Wolfram |
| `ChLBSPoly` | `ci.property(g, "ChLBSPoly")` | `CIProp[g, "ChLBSPoly"]` | Python and Wolfram |
| `ChLBS` | `ci.property(g, "ChLBS")` | `CIProp[g, "ChLBS"]` | Python and Wolfram |
| `CLBSPoly` | `ci.property(g, "CLBSPoly")` | `CIProp[g, "CLBSPoly"]` | Python and Wolfram |
| `CLBS` | `ci.property(g, "CLBS")` | `CIProp[g, "CLBS"]` | Python and Wolfram |
| `IndLBS` | `ci.property(g, "IndLBS")` | `CIProp[g, "IndLBS"]` | Python and Wolfram |
| `CohList` | `ci.property(g, "CohList")` | `CIProp[g, "CohList"]` | Python and Wolfram |
| `Basis` | `ci.property(g, "Basis")` | `CIProp[g, "Basis"]` | Python and Wolfram |
| `AmbCohDim` | `ci.property(g, "AmbCohDim")` | `CIProp[g, "AmbCohDim"]` | Python and Wolfram |
| `Coset` | `ci.property(g, "Coset")` | `CIProp[g, "Coset"]` | Python and Wolfram |
| `CohInfo` | `ci.property(g, "CohInfo")` | `CIProp[g, "CohInfo"]` | Python and Wolfram |
| `LBSCohDim` | `ci.property(g, "LBSCohDim")` | `CIProp[g, "LBSCohDim"]` | Python and Wolfram |

## CIMod keys

| Method | Python call | Wolfram call | Native availability |
| --- | --- | --- | --- |
| `CINormal` | `ci.modify(g, "CINormal")` | `CIMod[g, "CINormal"]` | Python and Wolfram. Integer configurations with bounded canonicalization. |
| `CIEquiv` | `ci.modify(g, "CIEquiv")` | `CIMod[g, "CIEquiv"]` | Python and Wolfram. Integer configurations with bounded canonicalization. |
| `LBSSum` | `ci.modify(g, "LBSSum")` | `CIMod[g, "LBSSum"]` | Python and Wolfram |
| `LBSTensor` | `ci.modify(g, "LBSTensor")` | `CIMod[g, "LBSTensor"]` | Python and Wolfram |
| `LBSWedge` | `ci.modify(g, "LBSWedge")` | `CIMod[g, "LBSWedge"]` | Python and Wolfram |
| `LBSSymm` | `ci.modify(g, "LBSSymm")` | `CIMod[g, "LBSSymm"]` | Python and Wolfram |
| `MapLBS` | `ci.modify(g, "MapLBS")` | `CIMod[g, "MapLBS"]` | Python and Wolfram. Integer charge matrices and Python-generated map coefficients. |
| `MapSpaceLBS` | `ci.modify(g, "MapSpaceLBS")` | `CIMod[g, "MapSpaceLBS"]` | Python and Wolfram. Prepared exact characteristic-zero map kernel, image and cokernel. |
| `QuotientLBS` | `ci.modify(g, "QuotientLBS")` | `CIMod[g, "QuotientLBS"]` | Python and Wolfram. Prepared exact characteristic-zero Bott–Borel–Weil quotient. |
| `DirectSumLBS` | `ci.modify(g, "DirectSumLBS")` | `CIMod[g, "DirectSumLBS"]` | Python and Wolfram. Prepared exact Bott–Borel–Weil associations. |
| `KoszulLBS` | `ci.modify(g, "KoszulLBS")` | `CIMod[g, "KoszulLBS"]` | Python and Wolfram. Explicit SymPy defining equations and bounded supported differentials. |
| `CohLBS` | `ci.modify(g, "CohLBS")` | `CIMod[g, "CohLBS"]` | Python and Wolfram. Certified dimension-only cases in characteristic zero. |
