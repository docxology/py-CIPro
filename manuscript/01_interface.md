# Software and research questions {#sec:interface}

Complete intersections in products of projective spaces encode equations, divisor classes, and many geometric invariants in arrays of small integers. The classical CICY threefold catalog established this representation at scale, and later work determined Hodge numbers, analyzed fibrations, and identified free quotients [@candelas-cicy; @green-hubsch; @green-hodge; @anderson-fibrations; @braun-quotients]. CIPro consolidates these constructions, data, and symbolic algorithms in a Wolfram Language package [@anderson-cipro; @cipro-release]. py-CIPro supplies an interface to that release, an independently implemented Python backend for documented domains, and interactive analysis of the bundled threefold archive.

Existing software addresses related domains. Larfors and Schneider used Python to study line-bundle cohomology on CICY threefolds of Picard number two, while CYTools specializes in Calabi–Yau hypersurfaces in toric varieties [@larfors-schneider-cohomology; @cytools]. py-CIPro centers the interface and artifacts of the released CIPro package so that computations, source records, and backend availability can be inspected together.

The studies examine four choices that affect the interpretation of a result. [@sec:chern_audit] fixes a polarization and computes its degree and second Chern pairing directly from each configuration. [@sec:catalog] compares two ways of weighting the same archive. [@sec:integral_invariants] derives invariants that survive a change of divisor generators and tests which Hodge groups they distinguish. [@sec:bundles] fixes a smooth bicubic equation and computes dimensions from its exact multiplication maps. Together the studies specify which data to preserve when comparing presentations, integral lattices, archive summaries, or members of a family.

| Selection | Execution and prerequisites |
| --------- | ------------------------------------------------------------- |
| Python | Runs the documented native domain, including the text archive. Reports a typed unsupported-domain error when applicable. |
| Wolfram | Loads the pinned release in an activated local Wolfram kernel. The Python API preserves kernel output, messages, and WXF. |
| Auto | Tries the native implementation and retries the original request through Wolfram on a native unsupported-domain outcome. Argument and computation errors propagate directly. |
: Execution paths in py-CIPro. The browser starts in Python mode. Direct construction of `CIPro()` defaults to Wolfram. Set the library backend explicitly to reproduce a native run. {#tbl:backends}

## From configuration data to a backend result

A geometry is a mapping containing ambient dimensions and configuration degrees. Defining equations, line-bundle sums, and symmetry generators can be added as needed. In the original API, `CIProp` requests properties and their prerequisites, while `CIMod` constructs modified objects or operation-specific results. In Python these correspond to `property` and `modify`. The `call` and `call_result` methods address public functions by name. Full property results can include both the input and additional fields [@anderson-cipro; @cipro-release]. To recompute an invariant independently of the archive, construct a fresh association from `DimPs` and `Conf`. A populated association can reuse its precomputed keys.

The Python path uses native integers and SymPy for exact algebra [@sympy]. Keyword options retain the spelling of the exported interface. For the Wolfram path, mappings become associations, lists become lists, and keyword names become string-keyed options. Wolfram Expression Format (WXF) preserves symbolic heads and exact rationals across transport. The diagnostic result includes messages and printed output, which can be material when reproducing a failed or partially evaluated symbolic computation [@wolfram-client].

The released catalog contains {{RELEASED_TOTAL}} entries across public functions, keys for properties, and keys for modifications. Python registers {{NATIVE_TOTAL}} of these in supported domains. Several keys call shared operations. [@tbl:method_inventory] counts the registered entries, and the language guides define their mathematical domains.

| Interface | CIPro {{UPSTREAM_TAG}} | Native Python | Wolfram-only |
| --- | ---: | ---: | ---: | ---: |
{{METHOD_TABLE_ROWS}}
: Method concordance measured from the pinned release and the native dispatch registries. One released name or dispatch key contributes one entry. The {{WOLFRAM_ONLY_TOTAL}} remaining entries use the Wolfram library. {#tbl:method_inventory}

## Notation and method concordance

The notation in [@tbl:geometry_notation] follows the mathematical inputs. [@tbl:formula_routes] identifies the corresponding release calls and Python replay paths. In the table, `g` is an association that contains the required inputs, and `ci` is a `CIPro(backend="python")` client. Use fresh associations when checking a calculation against a stored field.

| Notation | Mathematical meaning and input |
| --- | --- |
| $A$, $X$, $(n_i)$, $Q=(q_{ia})$ | Ambient product, complete intersection, factor dimensions, and configuration matrix. Rows index factors and columns index equations. See [@prop:adjunction]. |
| $H_i$, $D_a$, $F$ | Restricted hyperplane class, ambient degree class of equation $a$, and a specified defining polynomial when there is one equation. |
| $\mu$, $d_{ijk}$, $\lambda$, $T_i$ | Trilinear cup product, its evaluations on the $H_i$, second Chern functional, and its evaluations on the $H_i$. See [@def:integral_content]. |
| $\rho_X$, $L_X$ | First Pontryagin evaluation on the full integral second cohomology. For $c_1(TX)=0$, $\rho_X=-2\lambda$ on the ambient lattice. See [@prop:integral_topological_comparison]. |
| $L$, $S$, $(g_3,g_2)$ | Integral image of ambient classes, its saturation in the free second cohomology, and the cubic and second Chern content. See [@prop:integral_content_saturation]. |
| $\mathcal L$, $\ell$, $V$, $T$ | All-ones line bundle, its first Chern class, its cubic degree, and its second Chern pairing. See [@eq:polarized_pairings]. |
| $L_{\mathbf{k}}$, $h^q$, $\chi(X,L_{\mathbf{k}})$ | Ambient line bundle restricted to $X$, its degree-$q$ cohomology dimension, and its index. In the API one charge vector is one column of `LBS`. See [@eq:line_index]. |
| $M_{(a,b)}(F)$, $r_2$, $\delta(a,b)$ | Middle Koszul multiplication map at the bicubic charge, its rank, and the paired dimension excess over the generic member. See [@prop:bicubic_koszul_ranks] and [@eq:bicubic_paired_excess]. |
: Geometric notation used in the computations. The CIPro key `Mu` gives the integrating polynomial $\prod_a D_a$. The trilinear $\mu$ in this manuscript evaluates three divisor classes. {#tbl:geometry_notation}

| Quantity or formula | Released CIPro call | Python route and evidence |
| --- | --- | --- |
| Configuration and Hodge pair | `Data["Cicy3", id]` | `ci.Data("Cicy3", id)` reads the released fields. The atlas uses the original row IDs and filters in [@sec:catalog]. |
| Dimension and canonical class, [@prop:adjunction] | `CIProp[g, {"CIDim", "CY", "K"}]` | `ci.property` with the same keys. Use `DimPs` and `Conf` as defining inputs. |
| Chern classes and Euler, [@eq:archive_euler] and [@eq:quadratic_chern] | `CIProp[g, {"CPoly", "C", "Euler"}]` | `ci.property` with the same keys. The independent ring audit compares the stored Euler scalar and ordered second Chern pairings. |
| Intersection tensor and content, [@eq:integral_content_gcd] | `CIProp[g, "ISec"]` supplies the tensor | `ci.property(g, "ISec")` gives the tensor. The content audit pairs it with the Chern evaluations via a separate integer calculation. |
| Multigraded quotient series, [@eq:hilbert] | `HilbertSeries[g]` | `ci.HilbertSeries(g)` evaluates the rational expression and supports documented coefficient requests. |
| Line-bundle index, [@eq:line_index] | `CIProp[g, "IndLBS"]` | `ci.property(g, "IndLBS")` computes the index in the supported domain. The cohomology sweeps compare it with the index formula. |
| Individual dimensions, [@eq:bicubic_dimension_from_rank] | `CIMod[g, "CohLBS"]` | `ci.modify(g, "CohLBS")` covers documented native cases. The specified bicubic study independently computes rational map ranks. |
| Archive weights and content cells, [@eq:atlas_measures] and [@fig:integral_invariants] | `Data` supplies records | The dashboard research replays derive exact rational weights or integer divisibilities from those records. |
: Concordance for the calculations in this manuscript. Each displayed call uses the spelling in the pinned CIPro release. Python research calculations derive additional quantities from the inputs alongside the native method dispatch. [@anderson-cipro; @cipro-release] {#tbl:formula_routes}

## Replaying an archive record and a method preset

Start `py-cipro-dashboard` and open the loopback address printed by the launcher. Select archive record {{QUINTIC_RECORD_ID}} and compute `CIDim`, `CY`, and `Euler` from the configuration association. For this quintic the results are $3$, true, and ${{QUINTIC_EULER}}$. The record inspector identifies which values were computed and which were read from the archive. In the method lab, load and edit a preset, run the method, and inspect scalar, numeric matrix, or symbolic results. Symbolic arguments use a constrained JSON representation for symbols, indices, rationals, and arithmetic. The result identifies the actual backend, including when Auto resolves in Python. Procedural details and individual supported domains are in the repository's dashboard guide and Python/Wolfram concordance.

The computation below also records the backend without a browser. The association contains only the defining data.

~~~python
from py_cipro import CIPro

quintic = {"DimPs": [4], "Conf": [[5]]}
with CIPro(backend="python") as ci:
    result = ci.call_result(
        "CIProp", quintic, ["CIDim", "CY", "Euler"]
    )
    assert result.backend == "python"
    assert (result.value["CIDim"], result.value["CY"],
            result.value["Euler"]) == (3, True, -200)
~~~
