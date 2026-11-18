# Python API for CIPro v1.0

Python callers can use the native implementations with SymPy and exact arithmetic, or call the released Wolfram Language package. The [method concordance](../concordance.md) covers all callable symbols and dispatch keys. The [Wolfram guide](../wolfram/api.md) describes the underlying package interfaces.

Launch `py-cipro-dashboard` to use the same Python methods interactively. The dashboard starts with Python selected, shows the backend used for each result, and accepts structured JSON arguments in its method lab. The library constructor `CIPro()` defaults to Wolfram as described below. [Dashboard and method lab](../dashboard.md)

## Choose a backend

```python
from py_cipro import CIPro

quintic = {"Conf": [[5]], "DimPs": [4]}
with CIPro(backend="python") as ci:
    result = ci.property(quintic, ["CIDim", "CY", "Euler"])
    assert (result["CIDim"], result["CY"], result["Euler"]) == (3, True, -200)
    assert ci.Data("Cicy3", 7890)["Euler"] == -200
```

| Backend | Behavior |
| --- | --- |
| `python` | Runs the supported native domain without starting Wolfram. Raises `NativeUnsupportedError` for an operation, signature, or domain that needs the Wolfram backend. |
| `wolfram` | Default. Calls the pinned CIPro source in an activated local kernel. Set `WOLFRAM_KERNEL` or pass `kernel=` to select an executable. |
| `auto` | Tries the entire call in Python first. A `NativeUnsupportedError` triggers a fresh Wolfram call with the original arguments. Input errors and other computation errors propagate directly. |

`call`, `call_result`, `property`, `modify`, and exact-name methods accept a per-call `backend=` keyword. A Wolfram client in a context manager starts its kernel on entry. `python` and `auto` clients enter lazily. `evaluate` and `evaluate_result` take Wolfram expressions and require `wolfram` or `auto`. Python `Evaluation` objects report `backend="python"` with `wxf=None`. Wolfram results retain WXF, printed output, and messages.

```python
with CIPro(backend="auto") as ci:
    evaluation = ci.call_result("CIProp", quintic, "Euler", Format="Short")
    assert evaluation.backend == "python"
    assert evaluation.value == -200
```

## Call conventions and options

- Use dictionaries for Wolfram associations and lists or tuples for finite sequences. Native results typically use dictionaries, tuples, exact integers and fractions, and SymPy expressions. Mathematica expressions and SymPy expressions have different types. Pass original integer geometry when switching backends, or construct symbols explicitly in the receiving backend.
- `ci.call("Name", *args, **options)` and `ci.Name(*args, **options)` use the same dispatch. `property` and `modify` use exact released keys. The native property dispatcher computes source-declared prerequisites, reuses fields already present, and keeps the original input mapping intact. `Format="Full"` extends the input, `Format="Medium"` gives newly added fields, and `Format="Short"` returns the last new value. Use `Full` or `Medium` when every field is already present.
- `modify` accepts an association or a sequence of associations. Python supports the default `Format="Full"`. `CohLBS` uses a narrower prerequisite set for its certified dimension-only cases.
- Scalar CI geometry uses a row per projective factor and a column per defining equation. A bundle charge matrix uses a row per factor and a column per line-bundle summand. The Python coordinate convention is `IndexedBase("x")[i, j]`, with a one-based factor index and a zero-based homogeneous coordinate index. The default Kähler forms and moduli use `IndexedBase("J")[i]` and `IndexedBase("t")[i]`, both one-based. Exact polynomials can be combined with SymPy operations. [SymPy polynomial domains](https://docs.sympy.org/latest/modules/polys/domainsref.html)

## Geometry, characteristic classes, and Hilbert series

The native geometry routines cover integer configuration matrices, ambient and CI dimensions, the Calabi–Yau row-sum criterion, intersection forms and tensors, canonical bundles, Chern and Todd classes, Euler characteristics, and multigraded Hilbert series. The row-sum criterion is an adjunction check. Smoothness of particular equations is a separate calculation.

Characteristic-class contractions use positive dimension. `Class2Class` supports Chern class to Chern character through dimension three, and Chern character to Chern class or Chern class to Todd class through dimension four, with the default `J` basis. `KFormsName`, `KModuliName`, and `CoordName` affect the functions that explicitly consume them. Keep the default basis when combining outputs with `ClassConvert` or `Class2Class`. `HilbertFormat` supports the empty closed-form choice, a degree bound, an inclusive multidegree range, or an explicit degree matrix.

```python
bicubic = {"Conf": [[3], [3]], "DimPs": [2, 2]}
with CIPro(backend="python") as ci:
    invariants = ci.property(bicubic, ["C", "Euler"])
    assert invariants["C"] == ((0, 0), (36, 36), -162)
    assert invariants["Euler"] == -162
```

`SingularityLocus` constructs the patchwise equation and maximal Jacobian minor generators. `SingularityCheck` checks the corresponding Gröbner ideals in characteristic zero or a prime `FieldChar` (default `101`). The supported domain has exact rational polynomials of total degree at most 12, at most eight affine variables, and at most 64 patches and 64 maximal minors per patch. The release returns the string `"True"` on a detected singularity and Boolean `False` when every ideal is the unit ideal. The released cached `SingularLocus` path uses an uninitialized value and stays with Wolfram.

```python
conic = {"Conf": [[2]], "DimPs": [2]}
with CIPro(backend="python") as ci:
    x, y, z = ci.AmbCoords(conic)[0]
    assert ci.property(conic, "Singular", Eqs=[x**2], FieldChar=0, Format="Short") == "True"
    assert ci.property(conic, "Singular", Eqs=[x**2 + y**2 + z**2], FieldChar=0, Format="Short") is False
```

## Matrix groups and symbolic polynomials

The native symmetry routines cover block matrices, generator actions, finite group closure, projective equivalence, and deterministic integer normalization. Exact finite closures are bounded to 1,024 elements. Projective predicates also accept supported finite numeric matrices. Normalization bounds each equal-tally block to eight rows and all candidate orders to `8!`. `CIEquiv2` requires distinct row and column power signatures over its supported range of one through eight powers.

`MList`, `MMList`, `MMonList`, polynomial transformation, Reynolds averaging, and the invariant monomial routines use SymPy expressions. Monomial enumeration is bounded to 50,000 results and 100 variables per degree block. `InvMon` bounds trial tuples and group applications. `RandomPoly`, generated equations and bundle maps support the released coefficient choices in their documented domains. They draw from Python's random generator, so cross-runtime seeds can produce different samples. A plain string in a symbolic variable slot names a symbol. Construct expressions with SymPy before calling a polynomial method.

CIPro v1.0's `ProjAbelian` performs a self-comparison of each generator product. The Python implementation preserves this released behavior. `ConfInvQ` remains routed to Wolfram because its configuration loop starts from uninitialized variables.

## Line bundles and cohomology

Native line-bundle methods cover direct sums, tensor products, exterior and symmetric powers, characteristic classes, index, ambient Bott–Borel–Weil dimensions, and supported basis and cohomology constructions. Tensor, exterior and symmetric power options retain the upstream column convention. The direct `LineWedge` helper returns the released zero-charge column for its degenerate cases, while the `LBSWedge` modification uses a zero-column result where applicable.

`CohLBS` implements dimension-only characteristic-zero calculations without a printed protocol. The supported cases are ambient products, regular complete intersections in a single projective space, and multiprojective examples whose relevant Koszul twists or Serre-dual twists are acyclic above degree zero. `CohSum=True` gives one total column for each cohomological degree. `CohSum=False` gives one column per line-bundle summand. Exact ambient bases and cosets support the native `DirectSumLBS`. `KoszulLBS` requires explicit SymPy defining equations and an applicable integer `Ekpq`. `MapLBS` returns a polynomial matrix for integer charges. `MapSpaceLBS` and `QuotientLBS` support prepared exact characteristic-zero Bott–Borel–Weil bases and coset relations. Supply a multihomogeneous SymPy polynomial map for kernel, image or cokernel. The native basis generators may differ while spanning the same subspace.

```python
with CIPro(backend="python") as ci:
    bundle = {**quintic, "LBS": [[1]]}
    assert ci.modify(bundle, "CohLBS") == ((5,), (0,), (0,), (0,))
```

## Read the original CICY3 records

The native `Data` path reads the digest-checked text member of the release. It returns original archive fields, including `C` and `GVBasic`, rather than the dashboard projection. `Data("Cicy3", "Length")`, `Data("Cicy3", "All")`, one-based integer indices, inclusive `[start, end]` ranges, and Python predicates are supported. An optional field name or list projects values in selection order. Binary datasets, help and persistence calls use Wolfram. Product rows retain the source Hodge placeholders. [Dataset provenance](../research.md)

```python
with CIPro(backend="python") as ci:
    assert ci.Data("Cicy3", "Length") == 7890
    assert ci.Data("Cicy3", (7889, 7890), ("Num", "Euler")) == ((7889, -176), (7890, -200))
```

## Recompute cubic and index divisibility

`cubic_signature(record_id)` and `ambient_index_divisor(record_id)` are
native research functions for the non-product records in the pinned CIPro
v1.0 textual archive. Each call constructs the ambient intersection data
from the archived degree matrix. The IDs are one-based. Invalid IDs and
product records raise `ValueError`.

```python
from py_cipro import ambient_index_divisor, cubic_signature

assert cubic_signature(7741) == {"id": 7741, "d1": 1, "d2": 2, "d3": 2, "dp": 4}
assert ambient_index_divisor(7626) == 2
assert ambient_index_divisor(7635) == 1
```

The signature gives the gcds of all cubic evaluations, repeated cubic
evaluations, diagonal cubic evaluations, and second Chern evaluations.
The fixed divisor is the gcd of all line-bundle indices on the same
lattice. For example, every ambient line-bundle index on record 7626 is
even. [Mathematical definitions and archive comparison](../research.md#recompute-the-ambient-divisibility-studies)

## Using the original Wolfram kernel from Python

```python
from py_cipro import CIPro

with CIPro() as ci:
    print(ci.functions)
    print(ci.properties)
    print(ci.modifications)
```

| Python interface | Behavior |
| --- | --- |
| `CIPro(kernel=None, *, backend="wolfram", startup_timeout=180, evaluation_timeout=600)` | Use the specified executable path, `WOLFRAM_KERNEL`, or Wolfram Client automatic discovery, in that order. Timeouts are in seconds. An evaluation timeout of `None` removes the Python-side wait limit. |
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

## Verification and maintenance

The offline tests bind the registries to the original source and check the implemented mathematical domains against known archive and analytic fixtures. Live comparison uses an activated Wolfram kernel with `WOLFRAM_KERNEL` set. Regenerate this repository's [concordance](../concordance.md) with `python scripts/build_concordance.py` after changing the native registry.
