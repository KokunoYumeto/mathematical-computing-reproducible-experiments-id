from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit03_arrays.py"
SPEC = importlib.util.spec_from_file_location("unit03_arrays", MODULE_PATH)
assert SPEC and SPEC.loader
unit03 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit03)


class Unit03ArrayTests(unittest.TestCase):
    def test_make_vector_declares_shape_dtype_and_copy(self) -> None:
        source = np.array([1, 2, 3], dtype=np.int64)
        vector = unit03.make_vector(source, dtype="float64")
        self.assertEqual(vector.shape, (3,))
        self.assertEqual(vector.dtype, np.dtype("float64"))
        vector[0] = 99
        np.testing.assert_array_equal(source, np.array([1, 2, 3]))
        with self.assertRaisesRegex(ValueError, "satu dimensi"):
            unit03.make_vector([[1, 2], [3, 4]])

    def test_vectorization_matches_reference_and_preserves_invariants(self) -> None:
        values = np.array([1, 2, 3, 4], dtype=np.int64)
        before = values.copy()
        result = unit03.affine_transform(values, scale=3, shift=-2)
        np.testing.assert_array_equal(result, np.array([1, 4, 7, 10]))
        np.testing.assert_array_equal(values, before)
        self.assertEqual(result.shape, values.shape)
        self.assertEqual(
            int(np.sum(result)),
            3 * int(np.sum(values)) - 2 * values.size,
        )

    def test_broadcasting_has_an_explicit_shape_contract(self) -> None:
        table = np.array([[10, 20, 30], [40, 50, 60]])
        offsets = np.array([1, -2, 3])
        result = unit03.add_column_offsets(table, offsets)
        np.testing.assert_array_equal(
            result,
            np.array([[11, 18, 33], [41, 48, 63]]),
        )
        with self.assertRaisesRegex(ValueError, "jumlah offset"):
            unit03.add_column_offsets(table, np.array([1, 2]))

    def test_slice_view_and_explicit_copy_have_different_aliasing(self) -> None:
        trace = unit03.copy_view_trace()
        self.assertEqual(trace["base"], [0, -10, 2, 3, 4, 5])
        self.assertEqual(trace["view"], [-10, 2, 3])
        self.assertEqual(trace["copy"], [1, 99, 3])
        self.assertTrue(trace["view_shares_memory"])
        self.assertFalse(trace["copy_shares_memory"])

    def test_result_records_float_and_proof_boundaries(self) -> None:
        result = unit03.build_results()
        self.assertTrue(result["floating_point"]["close_to_0.6"])
        self.assertFalse(result["floating_point"]["is_exactly_0.6"])
        self.assertTrue(
            result["proof_boundary"]["vectorized_matches_scalar_reference"]
        )
        self.assertFalse(
            result["proof_boundary"]["proves_for_every_compatible_array"]
        )

    def test_canonical_output_is_byte_stable(self) -> None:
        result = unit03.build_results()
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a.json"
            second = Path(tmp) / "b.json"
            unit03.write_result(result, first)
            unit03.write_result(result, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
            self.assertEqual(parsed["schema"], "o002.unit03-results.v1")
            self.assertEqual(parsed["vectorization"]["result"], [1, 4, 7, 10])


if __name__ == "__main__":
    unittest.main()
