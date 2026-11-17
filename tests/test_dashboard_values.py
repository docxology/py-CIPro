"""Test exact browser values and construction with each backend."""

import unittest

import sympy as sp
from wolframclient.language import wl

from py_cipro._dashboard_values import decode, encode


class DashboardValueTests(unittest.TestCase):
    def test_values_beyond_javascript_safe_range_are_exact(self):
        number = 9007199254740993
        tagged = {"$integer": str(number)}
        fraction = {"$rational": [tagged, 2]}
        self.assertEqual(encode(number), tagged)
        self.assertEqual(decode(tagged), number)
        self.assertEqual(decode(fraction), sp.Rational(number, 2))
        self.assertEqual(encode(decode(fraction)), fraction)
        self.assertEqual(decode(fraction, "wolfram"), wl.Rational(number, 2))

    def test_tags_are_structured_and_validate_their_content(self):
        for invalid in ({"$integer": "1e9"}, {"$rational": [1, 0]}, {"$symbol": "x+y"}, {"$pow": [2, 100]},
                        {"$indexed": ["X", "1"]}, {"$source": "x"}, {"$symbol": "x", "options": {}}):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                decode(invalid)
