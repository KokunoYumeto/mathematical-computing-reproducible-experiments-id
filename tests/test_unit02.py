from __future__ import annotations

from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit02_objects.py"
SPEC = importlib.util.spec_from_file_location("unit02_objects", MODULE_PATH)
assert SPEC and SPEC.loader
unit02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit02)


class Unit02ObjectTests(unittest.TestCase):
    def test_scale_vector_is_pure_for_tuple_input(self) -> None:
        vector = (2, -1, 4)
        self.assertEqual(unit02.scale_vector(3, vector), (6, -3, 12))
        self.assertEqual(vector, (2, -1, 4))

    def test_scale_composition_invariant(self) -> None:
        vector = (Fraction(1, 3), Fraction(2, 5))
        self.assertEqual(
            unit02.scale_vector(6, vector),
            unit02.scale_vector(2, unit02.scale_vector(3, vector)),
        )

    def test_exact_mean(self) -> None:
        self.assertEqual(
            unit02.mean_fraction([Fraction(1, 3), Fraction(1, 2)]),
            Fraction(5, 12),
        )

    def test_empty_mean_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            unit02.mean_fraction([])

    def test_residue_contract(self) -> None:
        self.assertEqual(unit02.least_nonnegative_residue(-17, 5), 3)
        with self.assertRaises(ValueError):
            unit02.least_nonnegative_residue(3, 0)

    def test_canonical_output_is_stable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a.json"
            second = Path(tmp) / "b.json"
            for path in (first, second):
                path.write_bytes(unit02.canonical_json_bytes(unit02.build_results()))
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(json.loads(first.read_text(encoding="utf-8"))["mean"], "5/12")


if __name__ == "__main__":
    unittest.main()
