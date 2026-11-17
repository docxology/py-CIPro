"""Every native dashboard example executes from its public JSON payload."""

import json
import unittest
from unittest.mock import patch

from py_cipro import CIPro
from py_cipro._dashboard_examples import EXAMPLES
from py_cipro._dashboard_values import decode, encode
from py_cipro._native import NATIVE_FUNCTIONS, NATIVE_MODIFICATIONS, NATIVE_PROPERTIES


class DashboardExampleTests(unittest.TestCase):
    def test_native_examples_cover_the_method_registries(self):
        expected = {
            (kind, name)
            for kind, registry in (
                ("function", NATIVE_FUNCTIONS),
                ("property", NATIVE_PROPERTIES),
                ("modification", NATIVE_MODIFICATIONS),
            )
            for name in registry
        }
        self.assertEqual(EXAMPLES.keys(), expected)

    def test_native_examples_execute_without_wolfram(self):
        with patch("py_cipro._client.WolframLanguageSession") as session, CIPro(backend="python") as ci:
            for (kind, name), example in EXAMPLES.items():
                with self.subTest(kind=kind, name=name):
                    payload = json.loads(json.dumps(example, allow_nan=False))
                    args = decode(payload["args"], backend="python")
                    options = decode(payload["options"], backend="python")
                    if kind == "function":
                        result = ci.call(name, *args, **options)
                    elif kind == "property":
                        result = ci.property(args[0], name, **options)
                    else:
                        result = ci.modify(args[0], name, **options)
                    json.dumps(encode(result), allow_nan=False)
            session.assert_not_called()
