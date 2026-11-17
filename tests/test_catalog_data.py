"""Check the full Cicy3 archive projection and representative fixtures."""

from collections import Counter
import unittest

from py_cipro.catalog import get_catalog


class CatalogDataTests(unittest.TestCase):
    def test_released_population_and_consistency(self):
        records = get_catalog().records
        self.assertEqual(len(records), 7890)
        self.assertEqual(tuple(record.id for record in records), tuple(range(1, 7891)))
        self.assertEqual(len({(record.h11, record.h21) for record in records}), 266)
        self.assertEqual(sum(record.favourable for record in records), 4874)
        self.assertEqual(sum(record.product for record in records), 22)
        self.assertTrue(all(record.product == ((record.h11, record.h21) == (0, 0)) for record in records))
        self.assertEqual(Counter(record.euler for record in records).most_common(1), [(-32, 613)])
        self.assertTrue(all(record.euler == 2 * (record.h11 - record.h21) for record in records))

    def test_quintic_bicubic_and_tetraquadric(self):
        catalog = get_catalog()
        cases = (
            (7890, ((5,),), (4,), (1, 101, -200)),
            (7884, ((3,), (3,)), (2, 2), (2, 83, -162)),
            (7862, ((2,), (2,), (2,), (2,)), (1, 1, 1, 1), (4, 68, -128)),
        )
        for number, matrix, ambient, invariants in cases:
            with self.subTest(number=number):
                record = catalog.record(number)
                self.assertEqual(record.configuration, matrix)
                self.assertEqual(record.ambient_dimensions, ambient)
                self.assertEqual((record.h11, record.h21, record.euler), invariants)

        for number in (0, -1, 7891, True, "1"):
            with self.subTest(number=number), self.assertRaises(KeyError):
                catalog.record(number)
