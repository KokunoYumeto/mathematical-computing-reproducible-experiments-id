from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit08_validation.py"
SPEC = importlib.util.spec_from_file_location("unit08_validation", MODULE_PATH)
assert SPEC and SPEC.loader
unit08 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit08)


class Unit08UnitTests(unittest.TestCase):
    def test_exact_reference_examples(self) -> None:
        for n, expected in unit08.REFERENCE_VALUES:
            with self.subTest(n=n):
                self.assertEqual(unit08.triangular_iterative(n), expected)

    def test_edge_and_domain_contract(self) -> None:
        self.assertEqual(unit08.triangular_iterative(0), 0)
        with self.assertRaises(ValueError):
            unit08.triangular_iterative(-1)
        with self.assertRaises(TypeError):
            unit08.triangular_iterative(2.5)
        with self.assertRaises(TypeError):
            unit08.triangular_iterative(True)

    def test_exact_assertion_and_tolerant_assertion_are_distinct(self) -> None:
        self.assertEqual(unit08.triangular_iterative(10), 55)
        early = unit08.sqrt2_residual_check(iterations=2)
        converged = unit08.sqrt2_residual_check(iterations=5)
        self.assertFalse(early["passed"])
        self.assertTrue(converged["passed"])


class Unit08PropertyTests(unittest.TestCase):
    def test_independent_pairing_oracle(self) -> None:
        for n in range(201):
            with self.subTest(n=n):
                self.assertEqual(
                    unit08.triangular_iterative(n),
                    unit08.triangular_pairing_formula(n),
                )

    def test_metamorphic_relations(self) -> None:
        violations = unit08.property_violations(200)
        self.assertEqual(
            violations,
            {
                "pairing_formula": [],
                "increment_relation": [],
                "doubling_relation": [],
            },
        )


class Unit08IntegrationAndRegressionTests(unittest.TestCase):
    def test_regression_zero_boundary(self) -> None:
        self.assertEqual(unit08.triangular_iterative(0), 0)
        self.assertEqual(unit08.triangular_pairing_formula(0), 0)

    def test_report_is_integrated_honest_and_byte_stable(self) -> None:
        report = unit08.build_validation_report(limit=200)
        self.assertTrue(report["all_required_checks_passed"])
        self.assertEqual(report["independent_oracle"]["mismatches"], [])
        self.assertIn("bukan bukti", report["coverage_limit"])

        core = {key: value for key, value in report.items() if key != "core_sha256"}
        expected_digest = hashlib.sha256(
            unit08.canonical_json_bytes(core)
        ).hexdigest()
        self.assertEqual(report["core_sha256"], expected_digest)

        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            unit08.write_report(report, first)
            unit08.write_report(report, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(parsed["schema"], "o002.unit08.validation.v1")

    def test_concise_cli_uses_documented_default_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH)],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = Path(directory) / "output" / "unit08-results.json"
            self.assertTrue(result.is_file())


if __name__ == "__main__":
    unittest.main()
