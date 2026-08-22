from __future__ import annotations

from decimal import Decimal
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit06_floating.py"
SPEC = importlib.util.spec_from_file_location("unit06_floating", MODULE_PATH)
assert SPEC and SPEC.loader
unit06 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit06)


class Unit06FloatingTests(unittest.TestCase):
    def test_binary64_spacing_and_range_boundaries(self) -> None:
        profile = unit06.binary64_profile()
        self.assertEqual(float(profile["epsilon"]), math.ulp(1.0))
        self.assertEqual(float(profile["ulp_at_two_to_53"]), 2.0)
        self.assertTrue(profile["two_to_53_plus_one_is_unchanged"])
        self.assertEqual(profile["overflow_result"], "inf")
        self.assertTrue(profile["half_smallest_subnormal_is_zero"])

    def test_rationalized_difference_avoids_catastrophic_cancellation(self) -> None:
        report = unit06.cancellation_report()
        self.assertTrue(report["x_plus_one_rounds_to_x"])
        self.assertEqual(float(report["direct"]), 0.0)
        self.assertGreater(float(report["rationalized"]), 0.0)
        direct_error = Decimal(report["direct_relative_forward_error"])
        stable_error = Decimal(report["rationalized_relative_forward_error"])
        self.assertEqual(direct_error, Decimal(1))
        self.assertLess(stable_error, Decimal("1e-15"))
        self.assertTrue(report["rationalized_is_more_accurate"])

    def test_scipy_special_exprel_is_stable_near_zero(self) -> None:
        report = unit06.scipy_exprel_report(1e-8)
        self.assertEqual(report["scipy"]["function"], "scipy.special.exprel")
        self.assertEqual(report["mathematical_domain"], "semua x real")
        self.assertEqual(
            report["laboratory_domain"],
            "0 < |x| <= 1e-4 untuk masukan binary64",
        )
        self.assertEqual(report["decimal_oracle"]["precision_digits"], 80)
        self.assertEqual(
            report["decimal_oracle"]["method"],
            "deret pangkat bebas pembatalan untuk E dan E'",
        )

        forward = report["forward_error"]
        naive_forward = Decimal(forward["naive_relative"])
        stable_forward = Decimal(forward["scipy_relative"])
        self.assertGreater(naive_forward, Decimal("1e-9"))
        self.assertLess(stable_forward, Decimal("1e-15"))
        self.assertTrue(forward["scipy_is_more_accurate"])

        condition = Decimal(report["conditioning"]["relative_condition_number"])
        self.assertLess(condition, Decimal("1e-7"))
        backward = report["backward_error"]
        self.assertGreater(Decimal(backward["naive_relative_estimate"]), Decimal(1))
        self.assertLess(
            Decimal(backward["scipy_relative_estimate"]), Decimal("1e-6")
        )
        self.assertFalse(backward["is_exact_inverse_solution"])

        extreme = report["extreme_cancellation"]
        self.assertEqual(float(extreme["naive"]), 0.0)
        self.assertEqual(float(extreme["scipy_special_exprel"]), 1.0)
        self.assertTrue(extreme["math_exp_x_equals_one"])
        self.assertFalse(
            report["evidence_boundary"]["proves_stability_for_all_real_inputs"]
        )

    def test_scipy_exprel_lab_domain_is_explicitly_enforced(self) -> None:
        for boundary in (
            unit06.SCIPY_EXPREL_LAB_MIN_ABS,
            -unit06.SCIPY_EXPREL_LAB_MIN_ABS,
            unit06.SCIPY_EXPREL_LAB_MAX_ABS,
            -unit06.SCIPY_EXPREL_LAB_MAX_ABS,
        ):
            with self.subTest(boundary=boundary):
                report = unit06.scipy_exprel_report(boundary)
                self.assertEqual(report["tested_x"], repr(boundary))

        for invalid in (
            0.0,
            unit06.SCIPY_EXPREL_LAB_MAX_ABS * 10,
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, r"0 < \|x\|"):
                    unit06.scipy_exprel_report(invalid)

        for nonfinite in (math.inf, math.nan):
            with self.subTest(nonfinite=nonfinite):
                with self.assertRaisesRegex(ValueError, "berhingga"):
                    unit06.scipy_exprel_report(nonfinite)

    def test_decimal_oracle_resolves_smallest_subnormal_correction(self) -> None:
        smallest_subnormal = math.ulp(0.0)
        for x in (smallest_subnormal, -smallest_subnormal):
            with self.subTest(x=x):
                report = unit06.scipy_exprel_report(x)
                oracle = report["decimal_oracle"]
                self.assertGreaterEqual(oracle["precision_digits"], 370)

                stable_error = Decimal(report["forward_error"]["scipy_absolute"])
                expected_first_term = Decimal.from_float(abs(x)) / 2
                self.assertGreater(stable_error, 0)
                self.assertLess(
                    abs(stable_error - expected_first_term) / expected_first_term,
                    Decimal("1e-19"),
                )
                self.assertTrue(report["forward_error"]["scipy_is_more_accurate"])

                condition = Decimal(
                    report["conditioning"]["relative_condition_number"]
                )
                self.assertGreater(condition, 0)
                self.assertLess(
                    abs(condition - expected_first_term) / expected_first_term,
                    Decimal("1e-19"),
                )

    def test_forward_and_backward_error_are_small_and_distinct(self) -> None:
        report = unit06.sqrt_forward_backward_report(2)
        forward = Decimal(report["relative_forward_error"])
        backward = Decimal(report["relative_backward_error"])
        self.assertGreater(forward, 0)
        self.assertGreater(backward, 0)
        self.assertLess(forward, Decimal("1e-15"))
        self.assertLess(backward, Decimal("1e-15"))
        self.assertNotEqual(forward, backward)

    def test_conditioning_amplifies_a_small_input_change(self) -> None:
        report = unit06.conditioning_report()
        amplification = float(report["observed_amplification"])
        estimate = float(report["local_condition_estimate"])
        self.assertGreater(amplification, 1e7)
        self.assertLess(abs(amplification - estimate) / estimate, 2e-4)
        with self.assertRaisesRegex(ValueError, "tidak boleh sama"):
            unit06.reciprocal_gap(1.0)

    def test_summation_and_error_budget(self) -> None:
        summation = unit06.summation_report()
        self.assertEqual(float(summation["naive_left_to_right"]), 0.0)
        self.assertEqual(float(summation["reordered_naive_sum"]), 1.0)
        self.assertEqual(float(summation["math_fsum"]), 1.0)
        self.assertTrue(summation["naive_is_order_sensitive"])
        self.assertTrue(unit06.error_budget_report()["passes"])
        with self.assertRaisesRegex(ValueError, "negatif"):
            unit06.within_error_budget(
                1.0,
                1.0,
                absolute_budget=-1.0,
                relative_budget=0.0,
            )

    def test_canonical_output_is_byte_stable_and_limits_its_claim(self) -> None:
        payload = unit06.build_results()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            unit06.write_results(payload, first)
            unit06.write_results(payload, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(parsed["schema"], unit06.SCHEMA)
        self.assertFalse(
            parsed["proof_boundary"]["proves_every_binary64_operation_correct"]
        )
        self.assertEqual(len(parsed["core_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
