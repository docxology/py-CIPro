"""Regenerate the method concordance from the installed CIPro registries."""

import argparse
from pathlib import Path

from py_cipro import FUNCTIONS, MODIFICATIONS, PROPERTIES
from py_cipro._catalog import PROPERTY_SYMBOLS
from py_cipro._native import NATIVE_FUNCTIONS, NATIVE_MODIFICATIONS, NATIVE_PROPERTIES


NOTES = {
    "CICheck": "Association checks with Python warnings.",
    "CIProp": "Native keys in the table below. Wolfram handles interactive help.",
    "CIMod": "Native keys below. Python accepts the default Full format.",
    "Data": "Released textual Cicy3 only. Exact records, indexing, ranges and field projections.",
    "DefConf": "Integer configuration matrices, including explicit `Conf`.",
    "CIDim": "Integer configurations. Retains the release's handling of negative columns.",
    "Class2Class": "Default symbolic basis. Direction and dimension bounds in the Python guide.",
    "ClassConvert": "Exact coefficients and intersection tensors in positive dimension.",
    "HilbertSeries": "Closed rational form and supported coefficient expansions.",
    "HilbertExpand": "Finite exact series expansion through supported scalar or multidegree requests.",
    "CIEquiv2": "Bounded integer evaluation with unique row and column signatures.",
    "SymmMatNormal": "Integer input with bounded equal-tally blocks and candidate orders.",
    "SymmMatNormal0": "Integer input with bounded equal-tally blocks and candidate orders.",
    "MatNormal": "Integer input with bounded equal-tally blocks and candidate orders.",
    "CINormal": "Integer configurations with bounded canonicalization.",
    "CIEquiv": "Integer configurations with bounded canonicalization.",
    "GenGroup": "Exact finite matrix groups within the native closure limit.",
    "GenOrder": "Finite numeric matrices up to the supported generator order limit.",
    "ProjGenGroup": "Exact numeric projective groups within the native limits.",
    "ProjAbelian": "Preserves the released self-comparison. See the Python guide.",
    "MList": "Bounded deterministic exact monomials.",
    "MMList": "Bounded multigraded monomial enumeration.",
    "MMonList": "Bounded indexed-coordinate monomials for integer degrees.",
    "InvMon": "Exact finite group actions with bounded candidate enumeration.",
    "RandomPoly": "Native random coefficient generation with Python's RNG.",
    "GenericDefEqs": "Integer multidegrees with native generated or symbolic coefficients.",
    "InvDefEqs": "Equations from invariant monomials with native coefficients.",
    "DefEqs": "Explicit SymPy equations or Python-generated coefficients.",
    "SingularityCheck": "Bounded affine Jacobian checks over characteristic zero or a prime field.",
    "SingularityLocus": "Bounded exact affine-patch generators and substitutions.",
    "ChLBPoly": "Exact native line-bundle Chern character.",
    "CohLBS": "Certified dimension-only cases in characteristic zero.",
    "KoszulLBS": "Explicit SymPy defining equations and bounded supported differentials.",
    "DirectSumLBS": "Prepared exact Bott–Borel–Weil associations.",
    "MapLBS": "Integer charge matrices and Python-generated map coefficients.",
    "GVInvariants": "Upstream Klemm instanton code.",
    "ConfInvQ": "The released configuration check contains an uninitialized loop.",
    "MapSpaceLBS": "Prepared exact characteristic-zero map kernel, image and cokernel.",
    "QuotientLBS": "Prepared exact characteristic-zero Bott–Borel–Weil quotient.",
    "SaveData": "Wolfram DumpSave persistence.",
    "DeleteData": "Interactive Wolfram confirmation and deletion.",
    "CIExample": "Wolfram notebook help and examples.",
    "CIPro": "Wolfram help and option display.",
    "MM": "Wolfram MatrixForm display.",
    "HelpPrint": "Wolfram notebook help.",
    "InfoPrint": "Formatted Wolfram output.",
    "WarningPrint": "Formatted Wolfram output.",
    "ErrorPrint": "Formatted Wolfram output.",
    "StPrint": "Formatted Wolfram output.",
}


def _table(entries, registry, python_call, wolfram_call, lookup):
    rows = [
        "| Method | Python call | Wolfram call | Native availability |",
        "| --- | --- | --- | --- |",
    ]
    for key in entries:
        note = NOTES.get(key, NOTES.get(lookup(key), ""))
        availability = "Python and Wolfram" if key in registry else "Wolfram"
        if note:
            availability += f". {note}"
        rows.append(f"| `{key}` | `{python_call(key)}` | `{wolfram_call(key)}` | {availability} |")
    return "\n".join(rows)


def render():
    sections = [
        "# Method concordance for CIPro v1.0",
        f"Native Python covers **{len(NATIVE_FUNCTIONS)} of {len(FUNCTIONS)} public functions**, "
        f"**{len(NATIVE_PROPERTIES)} of {len(PROPERTIES)} property keys**, and "
        f"**{len(NATIVE_MODIFICATIONS)} of {len(MODIFICATIONS)} modification keys**. "
        "Coverage describes registered implementations within their supported argument domains. "
        "Live Wolfram parity has not been established. See the [Python guide](python/api.md) and "
        "[Wolfram Language guide](wolfram/api.md) for options and result representations.",
        "For the Python calls below, construct `CIPro(backend=\"python\")` to run locally. "
        "Every released function and key can also be invoked through Python with `backend=\"wolfram\"`. "
        "Wolfram calls assume `Needs[\"CIPro`\"]` or an equivalent package load. Ellipses denote positional arguments or options.",
        "## Public functions",
        _table(sorted(FUNCTIONS), NATIVE_FUNCTIONS, lambda name: f"ci.{name}(…)", lambda name: f"{name}[…]", lambda name: name),
        "## CIProp keys",
        _table(PROPERTIES, NATIVE_PROPERTIES, lambda key: f'ci.property(g, "{key}")',
               lambda key: f'CIProp[g, "{key}"]', PROPERTY_SYMBOLS.get),
        "## CIMod keys",
        _table(MODIFICATIONS, NATIVE_MODIFICATIONS, lambda key: f'ci.modify(g, "{key}")',
               lambda key: f'CIMod[g, "{key}"]', lambda key: key),
    ]
    return "\n\n".join(sections) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=Path("docs/concordance.md"), type=Path)
    args = parser.parse_args()
    args.output.write_text(render(), encoding="utf-8")


if __name__ == "__main__":
    main()
