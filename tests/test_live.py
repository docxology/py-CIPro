"""Reproduce small analytical CIPro examples using an activated Wolfram kernel."""

import os
import unittest

from py_cipro import CIPro


@unittest.skipUnless(os.environ.get("WOLFRAM_KERNEL"), "set WOLFRAM_KERNEL for live CIPro tests")
class LiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ci = CIPro().start()
        cls.addClassCleanup(cls.ci.close)

    def test_quintic(self):
        geometry = {"DimPs": [4], "Conf": [[5]]}
        result = self.ci.property(geometry, ["CIDim", "CY", "Euler"])
        self.assertEqual(result["CIDim"], 3)
        self.assertIs(result["CY"], True)
        self.assertEqual(result["Euler"], -200)

    def test_wedge_example_from_paper(self):
        geometry = {"DimPs": [2, 4], "Conf": [[1, 1, 1], [2, 2, 1]], "LBS": [[1, 1, -5], [1, -1, 2]]}
        result = self.ci.modify(geometry, "LBSWedge", TensorPower=2)
        self.assertEqual(tuple(map(tuple, result["LBS"])), ((2, -4, -4), (0, 3, 1)))

    def test_cicy3(self):
        self.assertEqual(self.ci.Data("Cicy3", "Length"), 7890)
