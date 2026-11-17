"""Verify that the Python catalog matches the bundled CIPro release."""

from pathlib import Path, PurePosixPath
import re
import unittest
from zipfile import ZipFile

from py_cipro._catalog import DATASETS, FUNCTIONS, MODIFICATIONS, PROPERTIES


ARCHIVE = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "py_cipro"
    / "vendor"
    / "CIProPackage.zip"
)


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(ARCHIVE) as archive:
            cls.source = archive.read("CIPro.m").decode("utf-8")
            cls.members = tuple(PurePosixPath(name) for name in archive.namelist())

    def test_public_functions(self):
        usage = set(
            re.findall(r"^CIPro`([A-Za-z]\w*)::usage\b", self.source, re.MULTILINE)
        )
        # CIPro::usage is declared in BeginPackage before the private context.
        usage.add("CIPro")
        definitions = set(
            re.findall(r"^([A-Za-z]\w*)\[[^\n]*\]\s*:=", self.source, re.MULTILINE)
        )
        self.assertEqual(FUNCTIONS, usage & definitions)

    def test_property_dispatch(self):
        registered = re.findall(
            r'^AssociateTo\[CIPro`Private`CIProMod,"([^"]+)"->',
            self.source,
            re.MULTILINE,
        )
        self.assertEqual(PROPERTIES, tuple(registered))
        # The "LBS" key calls the private DefLBS head, despite LBS::usage.
        self.assertIn("LBS", PROPERTIES)
        self.assertNotIn("LBS", FUNCTIONS)

    def test_modification_dispatch(self):
        registered = re.findall(
            r'^AssociateTo\[CIPro`Private`CIModMod,"([^"]+)"->',
            self.source,
            re.MULTILINE,
        )
        self.assertEqual(MODIFICATIONS, tuple(registered))

    def test_data_members(self):
        datasets = tuple(
            sorted(
                member.name
                for member in self.members
                if member.parent == PurePosixPath("CIProData") and "." not in member.name
            )
        )
        self.assertEqual(DATASETS, datasets)


if __name__ == "__main__":
    unittest.main()
