from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit11_numerical.py"
SPEC = importlib.util.spec_from_file_location("unit11_numerical", MODULE_PATH)
assert SPEC and SPEC.loader
unit11 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = unit11
SPEC.loader.exec_module(unit11)


class Unit11NumericalTests(unittest.TestCase):
    def test_bisection_contains_root_and_meets_width(self) -> None:
        result = unit11.bisection(lambda x: x * x - 2.0, 1.0, 2.0, width_tolerance=1e-10)
        self.assertLessEqual(result.width, 1e-10)
        self.assertLessEqual(result.left, math.sqrt(2.0))
        self.assertGreaterEqual(result.right, math.sqrt(2.0))

    def test_bisection_rejects_missing_sign_change(self) -> None:
        with self.assertRaises(ValueError):
            unit11.bisection(lambda x: x * x + 1.0, -1.0, 1.0, width_tolerance=1e-6)

    def test_bisection_rejects_nonfinite_points_and_function_values(self) -> None:
        for invalid_endpoint in (math.nan, math.inf, -math.inf):
            with self.subTest(endpoint=repr(invalid_endpoint)):
                with self.assertRaisesRegex(ValueError, "berhingga"):
                    unit11.bisection(
                        lambda x: x,
                        invalid_endpoint,
                        1.0,
                        width_tolerance=1e-6,
                    )

        for invalid_value in (math.nan, math.inf, -math.inf):
            with self.subTest(function_value=repr(invalid_value)):
                with self.assertRaisesRegex(ValueError, "berhingga"):
                    unit11.bisection(
                        lambda _x, value=invalid_value: value,
                        -1.0,
                        1.0,
                        width_tolerance=1e-6,
                    )

                def invalid_at_midpoint(x: float, value: float = invalid_value) -> float:
                    return value if x == 0.0 else x

                with self.assertRaisesRegex(ValueError, "titik tengah"):
                    unit11.bisection(
                        invalid_at_midpoint,
                        -1.0,
                        1.0,
                        width_tolerance=1e-6,
                    )

    def test_scipy_bisection_comparison_records_and_verifies_core_claims(self) -> None:
        comparison = unit11.compare_bisection_with_scipy(
            unit11.square_minus_two,
            1.0,
            2.0,
            original_width_tolerance=1e-12,
            scipy_xtol=5e-13,
        )
        self.assertEqual(comparison["method"], "bisect")
        self.assertEqual(comparison["scipy_version"], unit11.scipy.__version__)
        self.assertEqual(comparison["initial_bracket"], [1.0, 2.0])
        self.assertLess(comparison["endpoint_values"][0], 0)
        self.assertGreater(comparison["endpoint_values"][1], 0)
        self.assertEqual(
            comparison["tolerances"]["original_width_tolerance"], 1e-12
        )
        self.assertEqual(comparison["tolerances"]["scipy_xtol"], 5e-13)
        self.assertNotEqual(
            comparison["tolerances"]["semantics"]["original"],
            comparison["tolerances"]["semantics"]["scipy"],
        )

        scipy_result = comparison["scipy"]
        verification = comparison["verification"]
        self.assertTrue(scipy_result["converged"])
        self.assertEqual(scipy_result["flag"], "converged")
        self.assertTrue(verification["strict_sign_change"])
        self.assertTrue(verification["roots_inside_initial_bracket"])
        self.assertTrue(verification["roots_agree"])
        self.assertLessEqual(
            verification["absolute_root_difference"],
            verification["agreement_tolerance"],
        )
        self.assertIn("bukti kerja", comparison["proof_boundary"])

    def test_scipy_comparison_rejects_unbracketed_or_endpoint_root(self) -> None:
        with self.assertRaisesRegex(ValueError, "tanda berbeda"):
            unit11.compare_bisection_with_scipy(
                lambda x: x * x + 1.0,
                -1.0,
                1.0,
                original_width_tolerance=1e-8,
                scipy_xtol=1e-9,
            )
        with self.assertRaisesRegex(ValueError, "diapit secara ketat"):
            unit11.compare_bisection_with_scipy(
                lambda x: x,
                0.0,
                1.0,
                original_width_tolerance=1e-8,
                scipy_xtol=1e-9,
            )

    def test_trapezoid_is_exact_for_linear_function(self) -> None:
        self.assertEqual(unit11.trapezoid(lambda x: 3 * x + 2, 0.0, 4.0, 1), 32.0)

    def test_exact_linear_system_and_residual(self) -> None:
        solution = unit11.solve_2x2_exact(((2, 1), (1, -1)), (7, 1))
        self.assertEqual(solution, (Fraction(8, 3), Fraction(5, 3)))
        residual = unit11.residual(((2.0, 1.0), (1.0, -1.0)), (7.0, 1.0), tuple(map(float, solution)))
        self.assertTrue(all(abs(value) < 1e-12 for value in residual))

    def test_euler_refinement_reduces_example_error(self) -> None:
        errors = []
        for steps in (10, 20, 40):
            value = unit11.euler(lambda _t, y: y, 0.0, 1.0, 1 / steps, steps)
            errors.append(abs(value - math.e))
        self.assertGreater(errors[0], errors[1])
        self.assertGreater(errors[1], errors[2])

    def test_canonical_results(self) -> None:
        first = unit11.canonical_json_bytes(unit11.build_results())
        second = unit11.canonical_json_bytes(unit11.build_results())
        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertEqual(parsed["schema"], "o002.unit11-results.v1")

        bisection = parsed["bisection"]
        self.assertEqual(bisection["function"]["id"], "square_minus_two")
        self.assertEqual(bisection["initial_interval"], [1.0, 2.0])
        self.assertEqual(bisection["width_tolerance"], 1e-12)

        comparison = parsed["bisection_scipy_comparison"]
        self.assertEqual(comparison["scipy_version"], unit11.SCIPY_VERSION)
        self.assertEqual(
            comparison["tolerances"]["original_width_tolerance"], 1e-12
        )
        self.assertEqual(comparison["tolerances"]["scipy_xtol"], 1e-12)
        self.assertTrue(comparison["scipy"]["converged"])
        self.assertTrue(comparison["verification"]["roots_agree"])

        routes = parsed["curriculum_routes"]
        self.assertIn("bisection_scipy_comparison", routes["b80_a30_core"])
        self.assertEqual(
            set(routes["deferred_extensions_not_b80_core"]),
            {"B30", "B40", "B70"},
        )

        quadrature = parsed["quadrature_parameters"]
        self.assertEqual(quadrature["bounds"], [0.0, 1.0])
        self.assertEqual(quadrature["interval_grid"], [4, 8, 16, 32])
        self.assertEqual(quadrature["reference_integral"]["fraction"], "1/3")

        linear_system = parsed["linear_system"]
        self.assertEqual(linear_system["matrix"], [[2, 1], [1, -1]])
        self.assertEqual(linear_system["right_hand_side"], [7, 1])

        euler_parameters = parsed["euler_parameters"]
        self.assertEqual(euler_parameters["initial_time"], 0.0)
        self.assertEqual(euler_parameters["initial_value"], 1.0)
        self.assertEqual(euler_parameters["target_time"], 1.0)
        self.assertEqual(euler_parameters["steps_grid"], [10, 20, 40])
        self.assertEqual(
            float(euler_parameters["reference_solution"]["value_at_target"]),
            math.e,
        )

    def test_reader_gates_deferred_routes_and_adds_scipy_mastery(self) -> None:
        qmd = (ROOT / "source" / "units" / "11-eksperimen-numerik.qmd").read_text(
            encoding="utf-8"
        )
        for token in (
            "#gate-o002-u11-b30",
            "#gate-o002-u11-b40",
            "#gate-o002-u11-b70",
        ):
            self.assertEqual(qmd.count(token), 1)
        self.assertEqual(qmd.count("#ex-o002-u11-s01"), 1)
        mastery = qmd.split("#ex-o002-u11-s01", maxsplit=1)[1]
        self.assertIn('title="Petunjuk"', mastery)
        self.assertIn('title="Pemeriksaan mandiri"', mastery)
        self.assertIn('title="Jawaban dan solusi"', mastery)
        self.assertIn("compare_bisection_with_scipy", mastery)
        self.assertIn("SCIPY_VERSION", mastery)


if __name__ == "__main__":
    unittest.main()
