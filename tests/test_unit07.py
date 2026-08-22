from __future__ import annotations

from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit07_experiment_design.py"
SPEC = importlib.util.spec_from_file_location("unit07_experiment_design", MODULE_PATH)
assert SPEC and SPEC.loader
unit07 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit07)


class Unit07ExperimentDesignTests(unittest.TestCase):
    def test_plan_freezes_grid_stopping_rule_and_separate_seeds(self) -> None:
        plan = unit07.DEFAULT_PLAN
        unit07.validate_plan(plan)
        self.assertEqual(plan.parameter_grid, (3, 4, 5, 6, 7))
        self.assertNotEqual(plan.development_seed, plan.holdout_seed)
        self.assertEqual(plan.minimum_meaningful_effect, Fraction(1, 10))
        invalid = plan._replace(holdout_seed=plan.development_seed)
        with self.assertRaisesRegex(ValueError, "berbeda"):
            unit07.validate_plan(invalid)

    def test_seeded_cases_are_repeatable_but_seed_sensitive(self) -> None:
        first = unit07.generate_cases(101, 50)
        second = unit07.generate_cases(101, 50)
        different = unit07.generate_cases(102, 50)
        self.assertEqual(first, second)
        self.assertNotEqual(first, different)
        self.assertTrue(all(0 <= case.score <= 9 for case in first))

    def test_grid_uses_paired_cases_and_selects_declared_winner(self) -> None:
        result = unit07.build_results()
        development = result["development"]
        self.assertTrue(development["paired_cases_across_thresholds"])
        self.assertEqual(result["selected_threshold"], 5)
        correct = {
            int(threshold): record["correct"]
            for threshold, record in development["by_threshold"].items()
        }
        self.assertEqual(correct, {3: 2730, 4: 2938, 5: 3189, 6: 2986, 7: 2725})

    def test_fixed_replication_counts_are_completed_without_early_stopping(self) -> None:
        result = unit07.build_results()
        development = result["development"]
        holdout = result["holdout"]
        self.assertEqual(development["repetitions_completed"], 20)
        self.assertEqual(development["total_cases"], 4000)
        self.assertEqual(len(development["replications"]), 20)
        self.assertEqual(holdout["repetitions_completed"], 12)
        self.assertEqual(holdout["total_cases"], 3000)
        self.assertEqual(len(holdout["replications"]), 12)
        self.assertFalse(result["plan"]["stopping_rule"]["early_stopping_allowed"])

    def test_holdout_reports_effect_size_and_honest_negative_result(self) -> None:
        result = unit07.build_results()
        conclusion = result["conclusion"]
        self.assertEqual(conclusion["effect_size"]["fraction"], "151/3000")
        self.assertEqual(conclusion["effect_size"]["decimal"], "0.0503")
        self.assertFalse(conclusion["hypothesis_supported"])
        self.assertIn("hasil negatif", conclusion["result_label"])
        self.assertTrue(conclusion["minimum_effect_was_not_changed_after_run"])
        self.assertFalse(
            result["proof_boundary"]["proves_selected_threshold_is_universally_best"]
        )

    def test_custom_plan_controls_question_and_all_plan_metadata(self) -> None:
        custom = unit07.ExperimentPlan(
            parameter_grid=(1, 4, 8),
            reference_threshold=8,
            minimum_meaningful_effect=Fraction(1, 7),
            development_seed=41,
            development_repetitions=3,
            development_cases_per_repetition=17,
            holdout_seed=97,
            holdout_repetitions=2,
            holdout_cases_per_repetition=19,
        )
        result = unit07.build_results(custom)
        self.assertIn("1/7", result["question"])
        self.assertIn("0,1429", result["question"])
        self.assertIn("ambang referensi 8", result["question"])
        self.assertNotIn("ambang referensi 6", result["question"])
        self.assertEqual(
            result["hypothesis"]["minimum_meaningful_effect"]["fraction"],
            "1/7",
        )
        self.assertEqual(
            result["plan"],
            {
                "parameter_grid": [1, 4, 8],
                "reference_threshold": 8,
                "minimum_meaningful_effect": result["hypothesis"][
                    "minimum_meaningful_effect"
                ],
                "development_seed": 41,
                "development_repetitions": 3,
                "development_cases_per_repetition": 17,
                "holdout_seed": 97,
                "holdout_repetitions": 2,
                "holdout_cases_per_repetition": 19,
                "selection_rule": (
                    "akurasi pengembangan tertinggi; jika seri pilih ambang terkecil"
                ),
                "stopping_rule": {
                    "development": "tepat 3 replikasi x 17 kasus",
                    "holdout": "tepat 2 replikasi x 19 kasus",
                    "early_stopping_allowed": False,
                },
                "holdout_policy": (
                    "holdout tidak dipakai untuk memilih ambang dan dinilai sekali "
                    "setelah pilihan dibekukan"
                ),
            },
        )
        self.assertEqual(result["development"]["base_seed"], 41)
        self.assertEqual(result["holdout"]["base_seed"], 97)

    def test_canonical_output_and_core_hash_are_stable(self) -> None:
        result = unit07.build_results()
        core = dict(result)
        recorded_hash = core.pop("core_sha256")
        self.assertEqual(
            recorded_hash,
            hashlib.sha256(unit07.canonical_json_bytes(core)).hexdigest(),
        )
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            unit07.write_result(result, first)
            unit07.write_result(result, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(parsed["schema"], unit07.SCHEMA)
        self.assertTrue(parsed["randomness"]["replayable"])


if __name__ == "__main__":
    unittest.main()
