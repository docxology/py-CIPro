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
