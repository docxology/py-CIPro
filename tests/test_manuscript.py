"""Check that the scholarly outputs remain bound to executable source."""

import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(sys.version_info >= (3, 14), "manuscript renderer requires Python 3.14")
class ManuscriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
            import check_intersections
            import atlas_comparison
            import bicubic_exact
            import chern_audit
            import integral_invariants
            import manuscript_analysis
            import manuscript_variables

        cls.intersections = check_intersections
        cls.atlas = atlas_comparison
        cls.bicubic = bicubic_exact
        cls.chern = chern_audit
        cls.integral = integral_invariants
        cls.analysis = manuscript_analysis
        cls.variables = manuscript_variables

    def test_analysis_receipts_match_recomputation(self):
        catalog = self.intersections.get_catalog()
        expected = json.loads((ROOT / "data" / "analytic-checks.json").read_text())
        self.assertEqual(self.intersections.check_catalog_euler(catalog), expected["configuration_euler"])
        for fixture in expected["fixtures"].values():
            computed = self.intersections.analytic_fixture(catalog.record(fixture["record"]))
            self.assertEqual(json.loads(json.dumps(computed)), fixture)
        expected = json.loads((ROOT / "data" / "manuscript-analysis.json").read_text())
        self.assertEqual(json.loads(json.dumps(self.analysis.manuscript_analysis())), expected)

    def test_revision_analyses_match_recomputation(self):
        catalog = self.intersections.get_catalog()
        data = ROOT / "data"
        for path, result in (
            ("chern-audit.json", self.chern.compute_chern_audit()),
            ("atlas-comparison.json", self.atlas.atlas_comparison(catalog)),
            ("bicubic-exact.json", self.bicubic.analysis(data / "manuscript-analysis.json")),
            ("integral-invariants.json", self.integral.compute_integral_invariants()),
        ):
            with self.subTest(path=path):
                expected = json.loads((data / path).read_text(encoding="utf-8"))
                self.assertEqual(json.loads(json.dumps(result)), expected)

    def test_all_authored_tokens_have_generated_values(self):
        with patch.object(self.variables, "version", return_value="test-renderer"):
            with patch.object(self.variables.subprocess, "check_output", return_value="0" * 40):
                values, evidence = self.variables.build_variables(ROOT)
        self.variables.validate_tokens(ROOT, values)
        surfaces = evidence["software"]["method_surfaces"]
        self.assertEqual(evidence["software"]["version"], values["PACKAGE_VERSION"])
        self.assertEqual(
            f"{sum(surface['dashboard_examples'] for surface in surfaces):,}",
            values["NATIVE_TOTAL"],
        )


if __name__ == "__main__":
    unittest.main()
