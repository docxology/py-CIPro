"""Exact source fixtures for the native group and polynomial subsets."""

import unittest
from unittest.mock import patch

from sympy import Integer, Symbol, expand

from py_cipro._native_errors import NativeUnsupportedError
from py_cipro._native_symmetry import NATIVE_FUNCTIONS as native


class NativeSymmetryTests(unittest.TestCase):
    def test_block_shape_and_projective_equivalence(self):
        self.assertEqual(native["BlockMatrix"]([[[1, 2]], [[3], [4]]]), ((1, 2, 0), (0, 0, 3), (0, 0, 4)))
        self.assertEqual(native["PermMatrix"]([[0., 1.], [1., 0.]], [1, 1]), ((0, 1), (1, 0)))
        self.assertEqual(native["PermMatrix"]([[1]], [2]), {"Gen": ()})
        self.assertIs(native["MatProjEquiv"]([[4, 0], [0, -3]], [[1, 0], [0, 1]], [1, 1]), True)
        self.assertIs(native["MatProjEquiv"]([[4, 0], [0, -3]], [[1, 0], [0, 1]], [2]), False)
        self.assertTrue(native["MatProjTrivial"]([[2., 0.], [0., 2.]], [2]))
        self.assertFalse(native["MatProjEquiv"]([[0, 0], [0, 0]], [[1, 0], [0, 1]], [2]))

    def test_group_closure_and_projective_kernel(self):
        negative = ((-1, 0), (0, -1))
        swap = ((0, 1), (1, 0))
        geometry = {"DimPs": [1], "Gen": (negative, swap)}
        self.assertEqual(native["ArrangeGen"](geometry), ((negative,), (swap,)))
        self.assertEqual(native["GenOrder"](geometry), (2, 2))
        self.assertEqual(native["GenOrder"](geometry, MaxGenOrder=1), (None, None))
        self.assertTrue(native["Abelian"](geometry))
        geometry["Group"] = native["GenGroup"](geometry)
        self.assertEqual(native["GOrder"](geometry), 4)
        geometry["ProjTrivialGroup"] = native["ProjTrivialGroup"](geometry)
        self.assertEqual(native["ProjTrivialOrder"](geometry), 2)
        self.assertEqual(native["ProjOrder"](geometry), 2)
        classes = native["ProjGenGroup"](geometry)
        self.assertEqual(len(classes), 2)
        self.assertEqual({g for group in classes for g in group}, set(geometry["Group"]))
        with patch("py_cipro._native_symmetry._MAX_GROUP_SIZE", 5):
            with self.assertRaises(NativeUnsupportedError):
                native["GenGroup"]({"Gen": [[[2]]]})

    def test_release_projective_abelian_quirk(self):
        generators = (((0, 1), (1, 0)), ((1, 1), (0, 1)))
        geometry = {"Gen": generators, "DimPs": [1]}
        self.assertFalse(native["Abelian"](geometry))
        self.assertTrue(native["ProjAbelian"](geometry))  # CIPro v1.0 compares the same product twice.

    def test_default_generator_has_exact_fifth_order(self):
        association = {"Gen": native["Gen"]({})}
        self.assertEqual(native["GenOrder"](association), (5,))
        self.assertEqual(len(native["GenGroup"](association)), 5)

    def test_normal_form_witness_matrices(self):
        conf = ((3, 0), (1, 2))
        rearranged = ((2, 1), (0, 3))
        one = {"Conf": conf, "DimPs": [4, 2]}
        two = {"Conf": rearranged, "DimPs": [2, 4]}
        out = native["CINormal"](one)
        transposed_column_perm = tuple(zip(*out["ColPerm"]))
        self.assertEqual(native["MD"]([[out["RowPerm"]], [conf], [transposed_column_perm]]), (out["Conf"],))
        self.assertTrue(native["CIEquiv"]([one, two]))
        self.assertEqual(native["SymmMatNormal0"]([[1, 0], [0, 1]])[1], (((1, 0), (0, 1)), ((0, 1), (1, 0))))
        swap = ((0, 1), (1, 0))
        self.assertEqual(native["CIEquiv2"]({"Conf": [[1, 2], [3, 4]]}, {"Conf": [[4, 3], [2, 1]]}, 2), (True, swap, swap))
        self.assertEqual(native["CIEquiv2"]({"Conf": [[1]]}, {"Conf": [[2]]}, 1), (False, ()))
        with self.assertRaises(NativeUnsupportedError):
            native["CIEquiv2"]({"Conf": [[1, 0], [0, 1]]}, {"Conf": [[0, 1], [1, 0]]}, 2)

    def test_monomials_transform_and_average(self):
        x, y, z = map(Symbol, ("x", "y", "z"))
        self.assertEqual(native["MList"](2, (x, y)), (x**2, y**2, x*y))
        self.assertEqual(native["MList"](-1, (x, y)), (0,))
        self.assertEqual(native["MMList"]((1, 2), ((x, y), (z,))), (x*z**2, y*z**2))
        self.assertEqual(native["MMonList"]({"AmbCoords": ((x, y), (z,)), "Conf": [[1], [2]]}), ((x*z**2, y*z**2),))
        self.assertEqual(native["TransformPoly"](x**2 + y, (x, y), [[0, 1], [1, 0]]), y**2 + x)
        identity = ((1, 0), (0, 1))
        generator = ((-1, 0), (0, 1))
        group = ((identity,), (generator,))
        self.assertEqual(native["ReynoldsPoly"]((x + y,), (x, y), group), (y,))
        geometry = {"AmbCoords": ((x, y),), "Group": group, "Gen": (generator,), "DefEqs": (x**2+y,), "MonList": ((x**2, y**2, x*y),)}
        self.assertTrue(native["InvQ"](geometry))
        self.assertEqual(native["InvMon"](geometry), ((x**2,), (y**2,)))

    def test_equations_and_random_polynomial_options(self):
        x, y = map(Symbol, ("x", "y"))
        geometry = {"MonList": ((x, y),), "InvMon": ((x,),)}
        self.assertEqual(native["DefEqs"](geometry, Eqs=(y,)), (y,))
        self.assertEqual(native["DefEqs"](geometry, CoeffRange=(2, 2)), (2*x,))
        self.assertEqual(native["GenericDefEqs"](geometry, CoeffRange=(2, 2)), (2*x+2*y,))
        self.assertEqual(expand(native["RandomPoly"]((2,), ((x, y),), CoeffRange=(2, 2))), 2*x**2+2*x*y+2*y**2)
        self.assertEqual(native["MList"](0, (x, y)), (Integer(1),))
