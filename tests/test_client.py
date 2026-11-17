"""Test release preparation and actual WXF encodings without an installed kernel."""

from concurrent.futures import Future
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from wolframclient.deserializers import binary_deserialize
from wolframclient.serializers import export

from py_cipro import CIPro, EvaluationError, KernelUnavailable, wl
from py_cipro._release import APPLICATION_ROOT_SYMBOL, prepare_application


QUINTIC = {"DimPs": [4], "Conf": [[5]]}


def response(value, *, success=True, messages=(), output=()):
    return SimpleNamespace(
        result=value,
        success=success,
        messages=messages,
        output=output,
        wxf=export(value, target_format="wxf"),
        failure=None if success else "MessageFailure",
    )


class RecordingKernel:
    """Record the serialized expressions and return scripted kernel responses."""

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.expressions = []
        self.terminated = False

    def start(self, *, timeout):
        pass

    def evaluate_wrap_future(self, expr):
        self.expressions.append(binary_deserialize(export(expr, target_format="wxf")))
        future = Future()
        future.set_result(next(self.responses))
        return future

    def terminate(self):
        self.terminated = True


class ClientTests(unittest.TestCase):
    def test_dispatch_serializes_rules_and_associations_without_source_interpolation(self):
        kernel = RecordingKernel(response(True), response({"Euler": -200}), response(7890))
        with patch("py_cipro._client.WolframLanguageSession", return_value=kernel):
            with CIPro() as ci:
                self.assertEqual(ci.property(QUINTIC, "Euler", Format="Medium")["Euler"], -200)
                self.assertEqual(ci.Data("Cicy3", "Length"), 7890)
                root = Path(kernel.expressions[0].args[0].args[1])
                self.assertTrue((root / "CIProData" / "Cicy4").is_file())
            self.assertFalse(root.exists())

        self.assertTrue(kernel.terminated)
        startup = kernel.expressions[0]
        self.assertEqual(startup.head, wl.CompoundExpression)
        self.assertEqual(startup.args[0].args[0].name, APPLICATION_ROOT_SYMBOL)
        call = kernel.expressions[1]
        self.assertEqual(call.head.name, "CIPro`CIProp")
        self.assertEqual(call.args[0]["Conf"], ((5,),))
        self.assertEqual(call.args[1:], ("Euler", wl.Rule("Format", "Medium")))
        self.assertEqual(kernel.expressions[2].head.name, "CIPro`Data")
        self.assertEqual(kernel.expressions[2].args, ("Cicy3", "Length"))

    def test_diagnostics_and_failure_symbols_are_preserved(self):
        failed = response(getattr(wl, "$Failed"), messages=("upstream message",))
        kernel = RecordingKernel(response(True), response(None, output=("keys",)), failed)
        with patch("py_cipro._client.WolframLanguageSession", return_value=kernel):
            with CIPro() as ci:
                help_result = ci.call_result("CIProp", "Keys")
                self.assertIsNone(help_result.value)
                self.assertEqual(help_result.output, ("keys",))
                with self.assertRaises(EvaluationError) as exc:
                    ci.call("Data", "Cicy3", 0)
                self.assertEqual(exc.exception.detail.messages, ("upstream message",))
                self.assertEqual(binary_deserialize(exc.exception.detail.wxf).name, "$Failed")

    def test_unknown_heads_and_missing_kernel_fail_clearly(self):
        ci = CIPro(kernel="/nonexistent/py-cipro/WolframKernel")
        with self.assertRaises(ValueError):
            ci.call("System`Get", "input.m")
        with self.assertRaises(KernelUnavailable):
            ci.start()

    def test_load_relocates_only_five_paths_and_keeps_release_members(self):
        archive = Path(__file__).resolve().parents[1] / "src/py_cipro/vendor/CIProPackage.zip"
        with TemporaryDirectory() as directory, ZipFile(archive) as original:
            root = Path(directory)
            source = prepare_application(root)
            before, after = original.read("CIPro.m"), source.read_bytes()
            self.assertEqual(after.count(APPLICATION_ROOT_SYMBOL.encode()), 5)
            self.assertEqual(
                after.replace(APPLICATION_ROOT_SYMBOL.encode() + b'<>"/', b'$UserBaseDirectory<>"/Applications/'),
                before,
            )
            self.assertEqual(
                sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()),
                sorted(entry.filename for entry in original.infolist() if not entry.is_dir()),
            )
