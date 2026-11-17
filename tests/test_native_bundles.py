"""Source and mathematical fixtures for native CIPro line-bundle operations."""

from fractions import Fraction
import unittest

import sympy as sp

from py_cipro import CIPro
from py_cipro._native_bundles import NATIVE_FUNCTIONS
from py_cipro._native_errors import NativeUnsupportedError


class NativeBundleTests(unittest.TestCase):
    def test_tensor_and_power_order_and_released_zero_conventions(self):
        base = ((1, 1, -5), (1, -1, 2))
        self.assertEqual(NATIVE_FUNCTIONS["LineWedge"](base, 2), ((2, -4, -4), (0, 3, 1)))
        self.assertEqual(NATIVE_FUNCTIONS["LineWedge"](base, 4), ((0,), (0,)))
        self.assertEqual(NATIVE_FUNCTIONS["LineSymm"](((1, 2), (3, 5)), 2), ((2, 3, 4), (6, 8, 10)))
        self.assertEqual(NATIVE_FUNCTIONS["LineTensor"](((1, 2), (3, 5)), ((0, 4), (0, 2))), ((1, 5, 2, 6), (3, 5, 5, 7)))
        geometry = {"Conf": [[3], [3]], "DimPs": [2, 2], "LBS": base}
        with CIPro(backend="python") as ci:
            self.assertEqual(ci.modify(geometry, "LBSWedge", TensorPower=Fraction(5, 2))["LBS"], ((2, -4, -4), (0, 3, 1)))
            self.assertEqual(ci.modify(geometry, "LBSWedge", TensorPower=0)["LBS"], ((), ()))
            self.assertEqual(ci.modify(geometry, "LBSSymm", TensorPower=0)["LBS"], ((), ()))

    def test_bundle_classes_and_index_on_quintic(self):
        j = sp.IndexedBase("J")[1]
        geometry = {"Conf": [[5]], "DimPs": [4], "LBS": [[1]]}
        with CIPro(backend="python") as ci:
            association = ci.property(geometry, ["ChLBSPoly", "CLBSPoly", "IndLBS", "LBSRank"])
        self.assertEqual(association["ChLBSPoly"], 1+j+j**2/2+j**3/6)
        self.assertEqual(association["CLBSPoly"], 1+j)
        self.assertEqual(association["IndLBS"], 5)
        self.assertEqual(association["LBSRank"], 1)

    def test_ambient_bott_basis_order_and_prime_coset_rank(self):
        a, b, c, d, e = sp.symbols("a b c d e")
        geometry = {"DimPs": [1, 2], "LBS": [[2, -3], [-3, 0]], "CohList": [2, 1],
                    "AmbCoords": [[a, b], [c, d, e]]}
        basis = NATIVE_FUNCTIONS["Basis"](geometry)
        self.assertEqual(basis, ((a**2/(c*d*e), a*b/(c*d*e), b**2/(c*d*e)),
                                 (1/(a*b**2), 1/(a**2*b))))
        self.assertEqual(NATIVE_FUNCTIONS["AmbCohDim"]({"Basis": basis}), 5)
        self.assertEqual(NATIVE_FUNCTIONS["LBSCohDim"]({"Coset": ([[2, 0], [0, 1]], [[0], [0]])}, Modulus=2), 1)

    def test_exact_cohomology_dimensions_and_explicit_limitation(self):
        with CIPro(backend="python") as ci:
            quintic = {"Conf": [[5]], "DimPs": [4], "LBS": [[-1, 0, 1]]}
            self.assertEqual(ci.modify(quintic, "CohLBS", CohSum=False), ((0, 1, 5), (0, 0, 0), (0, 0, 0), (5, 1, 0)))
            self.assertEqual(ci.modify(quintic, "CohLBS"), ((6,), (0,), (0,), (6,)))
            ambient = {"Conf": [[], []], "DimPs": [1, 2], "LBS": [[2], [-3]]}
            self.assertEqual(ci.modify(ambient, "CohLBS"), ((0,), (0,), (3,), (0,)))
            bicubic = {"Conf": [[3], [3]], "DimPs": [2, 2], "LBS": [[3], [3]]}
            self.assertEqual(ci.modify(bicubic, "CohLBS"), ((99,), (0,), (0,), (0,)))
            bicubic["LBS"] = [[0], [0]]
            with self.assertRaises(NativeUnsupportedError):
                ci.modify(bicubic, "CohLBS")

    def test_explicit_koszul_maps_and_set_coefficient_bundle_map(self):
        a, b = sp.symbols("a b")
        ambient = {"Conf": [[1, 1]], "DimPs": [1], "AmbCoords": [[a, b]], "LBS": [[1]], "DefEqs": [a, b]}
        ordinary = {**ambient, "LBS": [[4]]}
        self.assertEqual(NATIVE_FUNCTIONS["KoszulLBS"]([ordinary], Ekpq=(1, 2, 0)), ((b,), (-a,)))
        self.assertEqual(NATIVE_FUNCTIONS["KoszulLBS"]([ambient], Ekpq=(2, 2, 1)), ((a*b,),))
        source = {"AmbCoords": [[a, b]], "LBS": [[0, 2]]}
        self.assertEqual(NATIVE_FUNCTIONS["MapLBS"]([source, {"LBS": [[1]]}], CoeffRange=(2, 2)), ((2*a+2*b, 0),))

    def test_prepared_bbw_map_spaces_and_identity_quotient(self):
        a, b = sp.symbols("a b")
        ambient = {"Conf": [[]], "DimPs": [1], "AmbCoords": [[a, b]]}
        with CIPro(backend="python") as ci:
            source = ci.property({**ambient, "LBS": [[0]]}, "LBSCohDim")
            target = ci.property({**ambient, "LBS": [[1]]}, "LBSCohDim")
            kernel = ci.modify([source, target], "MapSpaceLBS", Map=[[a]], Space="Ker")
            image = ci.modify([source, target], "MapSpaceLBS", Map=[[a]], Space="Im")
            cokernel = ci.modify([source, target], "MapSpaceLBS", Map=[[a]], Space="Coker")
            quotient = ci.modify([target, image], "QuotientLBS")
            self.assertEqual([result["LBSCohDim"] for result in (kernel, image, cokernel, quotient)], [0, 1, 1, 1])
            self.assertEqual(quotient["AmbCohdim"], 2)

            negative = ci.property({**ambient, "LBS": [[-3]]}, "LBSCohDim", CohQ=1)
            less_negative = ci.property({**ambient, "LBS": [[-2]]}, "LBSCohDim", CohQ=1)
            laurent_kernel = ci.modify([negative, less_negative], "MapSpaceLBS", Map=[[a]], Space="Ker")
            self.assertEqual(laurent_kernel["LBSCohDim"], 1)
            self.assertEqual(laurent_kernel["Coset"][0][0][0], 1)
