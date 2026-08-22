from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit04_visualization.py"
SPEC = importlib.util.spec_from_file_location("unit04_visualization", MODULE_PATH)
assert SPEC and SPEC.loader
unit04 = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = unit04
SPEC.loader.exec_module(unit04)


class Unit04VisualizationTests(unittest.TestCase):
    def test_dataset_is_ordered_and_model_fits_stated_intervals(self) -> None:
        unit04.validate_observations(unit04.OBSERVATIONS)
        self.assertEqual(
            [observation.time_s for observation in unit04.OBSERVATIONS],
            list(range(7)),
        )
        self.assertTrue(
            all(
                unit04.model_is_within_uncertainty(observation)
                for observation in unit04.OBSERVATIONS
            )
        )

    def test_invalid_uncertainty_and_time_order_are_rejected(self) -> None:
        invalid_uncertainty = (
            unit04.Observation(0, 1.0, 0.0, 1.0),
        )
        with self.assertRaisesRegex(ValueError, "positif"):
            unit04.validate_observations(invalid_uncertainty)

        invalid_order = (
            unit04.Observation(1, 3.0, 0.4, 3.0),
            unit04.Observation(0, 1.0, 0.4, 1.0),
        )
        with self.assertRaisesRegex(ValueError, "terurut"):
            unit04.validate_observations(invalid_order)

    def test_truncated_baseline_amplifies_visible_ratio(self) -> None:
        full_scale = unit04.visible_height_ratio(98, 100, 0)
        truncated = unit04.visible_height_ratio(98, 100, 97)
        self.assertAlmostEqual(full_scale, 100 / 98)
        self.assertEqual(truncated, 3)
        self.assertGreater(truncated, full_scale)
        with self.assertRaises(ValueError):
            unit04.visible_height_ratio(98, 100, 98)

    def test_csv_is_canonical_and_carries_units_in_headers(self) -> None:
        payload = unit04.canonical_csv_bytes()
        self.assertTrue(payload.endswith(b"\n"))
        self.assertNotIn(b"\r\n", payload)
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
        self.assertEqual(len(rows), 7)
        self.assertEqual(
            list(rows[0]),
            [
                "time_s",
                "measured_distance_m",
                "uncertainty_m",
                "model_distance_m",
            ],
        )
        self.assertEqual(rows[-1]["measured_distance_m"], "13.1")

    def test_figure_declares_scales_units_and_redundant_encodings(self) -> None:
        figure, axes = unit04.create_figure()
        try:
            self.assertEqual(axes.get_xlabel(), "Waktu, t (s)")
            self.assertEqual(axes.get_ylabel(), "Jarak, d (m)")
            self.assertEqual(axes.get_xlim()[0], 0)
            self.assertEqual(axes.get_ylim()[0], 0)
            model_line = next(
                line for line in axes.lines if line.get_label() == "Model d = 2t + 1"
            )
            self.assertEqual(model_line.get_linestyle(), "--")
            legend_text = [text.get_text() for text in axes.get_legend().get_texts()]
            self.assertIn("Pengukuran (±0,4 m)", legend_text)
        finally:
            unit04.plt.close(figure)

    def test_artifacts_are_byte_stable_and_manifest_hashes_are_correct(self) -> None:
        with tempfile.TemporaryDirectory() as first_tmp, tempfile.TemporaryDirectory() as second_tmp:
            first = unit04.write_artifacts(Path(first_tmp))
            second = unit04.write_artifacts(Path(second_tmp))

            for key in ("data", "figure", "alt_text", "manifest"):
                self.assertEqual(first[key].read_bytes(), second[key].read_bytes())

            manifest = json.loads(first["manifest"].read_text(encoding="utf-8"))
            self.assertEqual(manifest["schema"], unit04.SCHEMA)
            self.assertIn(
                "membuktikan model untuk semua waktu", manifest["claim_limit"]
            )
            for key in ("data", "figure", "alt_text"):
                digest = hashlib.sha256(first[key].read_bytes()).hexdigest()
                self.assertEqual(manifest["artifacts"][first[key].name], digest)

            svg = first["figure"].read_text(encoding="utf-8")
            self.assertIn("dc:description", svg)
            self.assertIn("tujuh pengamatan", svg)


if __name__ == "__main__":
    unittest.main()
