"""Independent configuration and exact polynomial checks for the native geometry port."""

from fractions import Fraction
import unittest

import sympy as sp

from py_cipro._native_errors import NativeUnsupportedError
from py_cipro._native_geometry import (
    amb_coords,
    canonical_bundle,
    chern,
    chern_character,
    chern_poly,
    ci_dim,
    class_convert,
    class_to_class,
    cy_q,
    def_conf,
    dim_ps,
    euler,
    hilbert_series,
    intersec,
    intersec_form,
    kahler_basis,
    mu,
    todd,
)
from py_cipro.catalog import get_catalog


QUINTIC = {"DimPs": (4,), "Conf": ((5,),)}
BICUBIC = {"DimPs": (2, 2), "Conf": ((3,), (3,))}


class NativeGeometryTests(unittest.TestCase):
    def test_configuration_and_coordinate_contract(self):
        self.assertEqual(def_conf({"DimPs": [1, 3]}), ((), ()))
        self.assertIsNone(def_conf({}))
        self.assertEqual(dim_ps({"Conf": [[0], [1], [3]]}), (1, 1, 2))
        self.assertEqual(canonical_bundle({"DimPs": [3], "Conf": [[2]]}), ((-2,),))
        self.assertFalse(cy_q({"DimPs": [3], "Conf": [[2]]}))
        a, b = sp.IndexedBase("a"), sp.IndexedBase("b")
        self.assertEqual(amb_coords({"DimPs": [1, 2]}, CoordName=(a, b)), ((a[0], a[1]), (b[0], b[1], b[2])))
        with self.assertWarnsRegex(UserWarning, "zero degree"):
            self.assertEqual(ci_dim({"DimPs": [1, 2], "Conf": [[0], [0]]}), -1)
        with self.assertWarnsRegex(UserWarning, "negative degrees"):
            self.assertEqual(ci_dim({"DimPs": [3, 2], "Conf": [[-1, 0], [3, 1]]}), 4)

    def test_integrated_forms_and_characteristic_classes(self):
        j1, j2 = kahler_basis(2)
        t1, t2 = kahler_basis(2, "t")
        self.assertEqual(mu(BICUBIC), 3*j1 + 3*j2)
        self.assertEqual(intersec_form(BICUBIC), 9*t1**2*t2 + 9*t1*t2**2)
        self.assertEqual(intersec(BICUBIC), (((0, 3), (3, 3)), ((3, 3), (3, 0))))
        self.assertEqual(chern_poly(QUINTIC), 1 + 10*j1**2 - 40*j1**3)
        self.assertEqual(chern(QUINTIC), ((0,), (50,), -200))
        self.assertEqual(chern(BICUBIC), ((0, 0), (36, 36), -162))
        self.assertEqual(chern_character(QUINTIC), ((0,), (-50,), -100))
        self.assertEqual(todd(QUINTIC), ((0,), (Fraction(25, 6),), 0))
        self.assertEqual(euler({"DimPs": [1], "Conf": [[2]]}), 2)
        self.assertEqual(euler({**QUINTIC, "C": ((0,), (50,), -211)}), -211)
        self.assertEqual(class_convert(j1*j2, ((((0, 0), (0, 0)), ((0, 0), (0, 0))),)*2, 4, 2)[1], ((0, 1), (0, 0)))
        with self.assertRaises(NativeUnsupportedError):
            class_to_class(1, 4, 1, 4)

    def test_hilbert_closed_form_and_exact_box_coefficients(self):
        t1, t2 = kahler_basis(2, "t")
        self.assertEqual(hilbert_series(QUINTIC), (1-t1**5)/(1-t1)**5)
        self.assertEqual(hilbert_series(QUINTIC, HilbertFormat=5).coeff(t1, 5), 125)
        self.assertEqual(hilbert_series(BICUBIC, HilbertFormat=((1, 0), (2, 2))), 1+3*t1+36*t1**2*t2**2)

    def test_native_euler_against_released_threefolds(self):
        archive = get_catalog()
        for record in (archive.record(record_id) for record_id in (1, 794, 2537, 5187, 7542, 7862, 7884, 7890)):
            with self.subTest(record=record.id):
                geometry = {"DimPs": record.ambient_dimensions, "Conf": record.configuration}
                self.assertEqual(euler(geometry), record.euler)
