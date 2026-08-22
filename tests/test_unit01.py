from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_ROOT = PROJECT_ROOT / "source" / "code"
sys.path.insert(0, str(CODE_ROOT))

import unit01_experiment as experiment  # noqa: E402


class Unit01ExperimentTests(unittest.TestCase):
    def test_exact_arithmetic(self) -> None:
        self.assertEqual(experiment.exact_sum(), Fraction(3, 10))

    def test_float_is_approximate_but_close(self) -> None:
        value = experiment.floating_sum()
        self.assertNotEqual(value, 0.3)
        self.assertTrue(experiment.close_to_three_tenths(value))

    def test_finite_parity_check(self) -> None:
        self.assertTrue(all(experiment.even_expression_holds(n) for n in range(10_000)))

    def test_counterexample(self) -> None:
        result = experiment.first_euler_counterexample()
        self.assertEqual(result, {"n": 40, "value": 1681, "factor": 41})
        self.assertEqual(result["value"], result["factor"] ** 2)

    def test_positive_limit_is_required(self) -> None:
        with self.assertRaisesRegex(ValueError, "positif"):
            experiment.run_experiment(0)

    def test_json_is_stable_for_same_environment(self) -> None:
        result = experiment.run_experiment(1000)
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            experiment.write_result(result, first)
            experiment.write_result(result, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(parsed["schema"], "o002.unit01.experiment.v1")
            self.assertFalse(parsed["finite_check"]["proves_universal_claim"])

    def test_concise_cli_uses_documented_default_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, str(CODE_ROOT / "unit01_experiment.py")],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = Path(directory) / "output" / "unit01-results.json"
            self.assertTrue(result.is_file())


if __name__ == "__main__":
    unittest.main()
