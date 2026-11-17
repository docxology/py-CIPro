"""Bind native routing and documentation to the exact released API."""

from pathlib import Path
import re
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from py_cipro import CIPro, Evaluation, FUNCTIONS, MODIFICATIONS, NativeUnsupportedError, PROPERTIES, wl, wlexpr
from py_cipro._catalog import MODIFICATION_DEPENDENCIES, PROPERTY_DEPENDENCIES, PROPERTY_SYMBOLS
from py_cipro._native import NATIVE_FUNCTIONS, NATIVE_MODIFICATIONS, NATIVE_PROPERTIES
from scripts.build_concordance import render

PROJECT = Path(__file__).resolve().parents[1]
QUINTIC = {"Conf": [[5]], "DimPs": [4]}


class NativeDispatchTests(unittest.TestCase):
    def test_source_mappings_and_concordance_are_complete(self):
        asset = PROJECT / "src/py_cipro/vendor/CIProPackage.zip"
        with ZipFile(asset) as upstream:
            source = upstream.read("CIPro.m").decode()
        for kind, registry in (("CIPro", PROPERTY_DEPENDENCIES), ("CIMod", MODIFICATION_DEPENDENCIES)):
            matches = re.findall(rf'{kind}Dep,"(\w+)"->\{{([^}}]*)\}}', source)
            expected = {key: tuple(dict.fromkeys(re.findall(r'"(\w+)"', body))) for key, body in matches}
            self.assertEqual(registry, expected)
        self.assertEqual(PROPERTY_SYMBOLS, dict(re.findall(r'CIProMod,"(\w+)"->(\w+)', source)))
        self.assertLessEqual(NATIVE_FUNCTIONS.keys(), FUNCTIONS)
        self.assertLessEqual(NATIVE_PROPERTIES.keys(), set(PROPERTIES))
        self.assertLessEqual(NATIVE_MODIFICATIONS.keys(), set(MODIFICATIONS))
        self.assertEqual((PROJECT / "docs/concordance.md").read_text(), render())
        for name in ("python", "wolfram"):
            self.assertEqual(list((PROJECT / "docs" / name).iterdir()), [PROJECT / "docs" / name / "api.md"])

    def test_native_methods_work_without_allocating_a_kernel(self):
        with patch("py_cipro._client.WolframLanguageSession") as kernel:
            with CIPro(backend="python") as ci:
                detail = ci.call_result("CIProp", QUINTIC, "Euler", Format="Short")
                self.assertEqual((detail.backend, detail.value, detail.wxf), ("python", -200, None))
                self.assertEqual(ci.CIDim(QUINTIC), 3)
                self.assertEqual(ci.property({**QUINTIC, "Euler": 123}, "Euler", Format="Medium"), {})
                self.assertEqual(ci.property({**QUINTIC, "Euler": 123}, "Euler")["Euler"], 123)
                with self.assertRaises(NativeUnsupportedError):
                    ci.property(QUINTIC, "GVInv")
                with self.assertRaises(NativeUnsupportedError):
                    ci.evaluate(wl.Plus(1, 2))
            kernel.assert_not_called()

    def test_auto_falls_back_with_original_arguments_only_for_unsupported_domains(self):
        kernel_result = Evaluation("remote", True, (), (), b"wxf", None)
        with CIPro(backend="auto") as ci, patch.object(ci, "_evaluate_wolfram", return_value=kernel_result) as wolfram:
            self.assertEqual(ci.property(QUINTIC, "Euler", Format="Short"), -200)
            wolfram.assert_not_called()
            self.assertEqual(ci.property(QUINTIC, ["CIDim", "GVInv"]), "remote")
            self.assertEqual(wolfram.call_args.args[0].args, (QUINTIC, ["CIDim", "GVInv"]))
            wolfram.reset_mock()
            with self.assertRaises(ValueError):
                ci.property(QUINTIC, "NoSuchKey")
            wolfram.assert_not_called()
            self.assertEqual(ci.property(QUINTIC, "CIDim", backend="wolfram"), "remote")

    def test_catalog_preserves_exact_archived_fields_and_selection_shape(self):
        ci = CIPro(backend="python")
        self.assertEqual(ci.Data("Cicy3", "Length"), 7890)
        row = ci.Data("Cicy3", 7890)
        self.assertEqual(row["C"], ((0,), (50,), -200))
        self.assertEqual(row["GVBasic"], (2875,))
        row["Euler"] = 1
        self.assertEqual(ci.Data("Cicy3", 7890, "Euler"), (-200,))
        self.assertEqual(ci.Data("Cicy3", (7890, 7889), ("Num", "Euler")), ((7889, -176), (7890, -200)))
        self.assertEqual(ci.Data("Cicy3", lambda record: record["Euler"] == -200, "Num"), (7890,))
        self.assertEqual(len(ci.Data("Cicy3", wl.All)), 7890)
        with self.assertRaises(NativeUnsupportedError):
            ci.Data("Cicy3", wlexpr('#["Euler"] == -200 &'))
        with self.assertRaises(NativeUnsupportedError):
            ci.Data("Cicy4", "Length")

    def test_exact_affine_jacobian_checks_and_released_types(self):
        ci = CIPro(backend="python")
        conic = {"Conf": [[2]], "DimPs": [2]}
        x, y, z = ci.AmbCoords(conic)[0]
        self.assertIs(ci.property(conic, "Singular", Eqs=[x*x + y*y + z*z], FieldChar=0, Format="Short"), False)
        self.assertEqual(ci.property(conic, "Singular", Eqs=[x*x], FieldChar=0, Format="Short"), "True")
        self.assertEqual(ci.property(conic, "Singular", Eqs=[x*x + y*y + z*z], FieldChar=2, Format="Short"), "True")
        generators, patches = ci.property(conic, "SingularLocus", Eqs=[x*y], Format="Short")
        self.assertEqual(patches[-1], ((z, 1),))
        self.assertEqual(generators[-1], (x*y, y, x))
