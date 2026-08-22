from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import sympy as sp


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit05_symbolic.py"
SPEC = importlib.util.spec_from_file_location("unit05_symbolic", MODULE_PATH)
assert SPEC and SPEC.loader
unit05 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit05)


class Unit05SymbolicTests(unittest.TestCase):
    def test_standard_library_fraction_stays_exact(self) -> None:
        self.assertEqual(unit05.exact_fraction_sum(), Fraction(3, 10))

    def test_expression_is_not_its_evaluated_value(self) -> None:
        x, expression, value = unit05.expression_and_value(Fraction(1, 2))
        self.assertIn(x, expression.free_symbols)
        self.assertEqual(value, sp.Rational(-3, 4))
        self.assertNotEqual(expression, value)

    def test_structural_difference_can_be_a_polynomial_identity(self) -> None:
        _, left, right = unit05.equivalence_example()
        self.assertNotEqual(left, right)
        self.assertTrue(unit05.polynomial_identity_holds(left, right))

    def test_cancellation_preserves_the_original_domain_exclusion(self) -> None:
        x, original, simplified, excluded = unit05.domain_sensitive_cancellation()
        self.assertEqual(simplified, x + 1)
        self.assertEqual(excluded, (sp.Integer(1),))
        self.assertTrue(sp.simplify(original - simplified) == 0)
        self.assertTrue(original.subs(x, 1).has(sp.nan, sp.zoo))
        self.assertEqual(simplified.subs(x, 1), 2)

    def test_assumptions_change_a_valid_simplification(self) -> None:
        real_result, positive_result = unit05.square_root_under_assumptions()
        self.assertEqual(sp.sstr(real_result), "Abs(x)")
        self.assertEqual(sp.sstr(positive_result), "x")

    def test_factorization_and_solutions_are_exact_and_checkable(self) -> None:
        _, polynomial, factored = unit05.exact_factorization()
        self.assertEqual(sp.expand(factored), polynomial)
        self.assertEqual(
            tuple(sp.sstr(item) for item in unit05.exact_real_solutions()),
            ("-sqrt(2)", "sqrt(2)"),
        )
        self.assertTrue(
            all(sp.simplify(item**2 - 2) == 0 for item in unit05.exact_real_solutions())
        )

    def test_canonical_output_is_repeatable_and_sage_lab_is_required(self) -> None:
        payload = unit05.build_results()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            unit05.write_results(payload, first)
            unit05.write_results(payload, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(parsed["schema"], "o002.unit05.symbolic.v1")
        self.assertEqual(parsed["exact_fraction"]["result"], "3/10")
        self.assertTrue(parsed["sage_bridge"]["required_for_baseline"])
        self.assertIn("from sage.all import", parsed["sage_bridge"]["source"])
        self.assertEqual(
            parsed["sage_bridge"]["executable_lab"],
            "source/code/unit05_sage_lab.py",
        )
        self.assertEqual(parsed["sage_bridge"]["required_runtime"], "SageMath 9.5")
        self.assertFalse(
            parsed["sage_bridge"]["remote_service_satisfies_requirement"]
        )
        self.assertEqual(len(parsed["core_sha256"]), 64)

    def test_reader_declares_required_sage_lab_and_two_mastery_exercises(self) -> None:
        qmd = (ROOT / "source" / "units" / "05-eksak-simbolik-sage.qmd").read_text(
            encoding="utf-8"
        )
        for exercise_id in ("#ex-o002-u05-sage-01", "#ex-o002-u05-sage-02"):
            self.assertEqual(qmd.count(exercise_id), 1)
            exercise = qmd.split(exercise_id, maxsplit=1)[1]
            self.assertIn('title="Petunjuk"', exercise)
            self.assertIn('title="Pemeriksaan mandiri"', exercise)
            self.assertIn('title="Jawaban dan solusi"', exercise)
        self.assertIn("SageMath 9.5", qmd)
        self.assertIn("/usr/bin/sage -python", qmd)
        self.assertNotIn("Jembatan SageMath yang opsional", qmd)


if __name__ == "__main__":
    unittest.main()
