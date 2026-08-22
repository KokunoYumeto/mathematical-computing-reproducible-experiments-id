from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "primer01_execution.py"
QMD_PATH = ROOT / "source" / "units" / "p01-menjalankan-eksperimen-python.qmd"
NOTEBOOK_PATH = ROOT / "source" / "notebooks" / "o002-p01-clean-kernel.ipynb"
SPEC = importlib.util.spec_from_file_location("primer01_execution", MODULE_PATH)
assert SPEC and SPEC.loader
p01 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p01)


class Primer01ExecutionTests(unittest.TestCase):
    def test_scalar_snapshot_names_types_and_values(self) -> None:
        records = p01.scalar_snapshot()
        self.assertEqual(
            [record["name"] for record in records],
            ["jumlah", "toleransi", "label", "lulus", "catatan"],
        )
        self.assertEqual(
            [record["type"] for record in records],
            ["int", "float", "str", "bool", "NoneType"],
        )
        self.assertEqual(records[-1]["value"], None)

    def test_circle_area_and_invalid_radius(self) -> None:
        self.assertAlmostEqual(p01.circle_area(3), 28.274333882308138)
        self.assertEqual(p01.circle_area(0), 0.0)
        with self.assertRaisesRegex(ValueError, "tidak boleh negatif"):
            p01.circle_area(-1)

    def test_computation_is_distinct_from_display_text(self) -> None:
        record = p01.computation_and_display(2, 3)
        self.assertEqual(record["computed_value"], 5)
        self.assertEqual(record["display_text"], "2 + 3 = 5")
        self.assertIsInstance(record["computed_value"], int)
        self.assertIsInstance(record["display_text"], str)

    def test_clean_namespace_rejects_hidden_state(self) -> None:
        with self.assertRaises(NameError):
            p01.run_cells(("hasil = data * 2",))

    def test_old_namespace_can_hide_an_order_error(self) -> None:
        dirty = p01.run_cells(("data = 7",))
        result = p01.run_cells(("hasil = data * 2",), dirty)
        self.assertEqual(result["hasil"], 14)

    def test_restart_and_run_all_succeeds_in_source_order(self) -> None:
        result = p01.run_cells(("data = 7", "hasil = data * 2"))
        self.assertEqual(result, {"data": 7, "hasil": 14})

    def test_traceback_uses_stable_cell_name(self) -> None:
        try:
            p01.run_cells(("nilai = 1 / 0",))
        except ZeroDivisionError as error:
            frames = []
            traceback = error.__traceback__
            while traceback is not None:
                frames.append(traceback.tb_frame.f_code.co_filename)
                traceback = traceback.tb_next
            self.assertIn("<o002.p01.cell.1>", frames)
        else:
            self.fail("ZeroDivisionError tidak muncul")

    def test_receipt_is_complete_and_canonical(self) -> None:
        receipt = p01.build_receipt()
        self.assertEqual(receipt["schema"], "o002.p01.execution.v1")
        self.assertEqual(receipt["clean_run"], {"data": 7, "hasil": 14})
        first = p01.canonical_json_bytes(receipt)
        second = p01.canonical_json_bytes(p01.build_receipt())
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first)["computation_and_display"]["computed_value"], 5)

    def test_cli_writes_the_documented_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "p01.json"
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--output", str(output)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue(output.is_file())
            self.assertIn(str(output), completed.stdout)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["schema"], p01.SCHEMA)


class Primer01ReaderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = QMD_PATH.read_text(encoding="utf-8")

    def test_stable_unit_and_exercise_ids(self) -> None:
        self.assertIn("identifier: o002.p01", self.text)
        found = set(re.findall(r"#ex-o002-p01-\d{2}", self.text))
        expected = {f"#ex-o002-p01-{number:02d}" for number in range(1, 6)}
        self.assertEqual(found, expected)

    def test_every_exercise_has_hint_check_and_full_solution(self) -> None:
        self.assertEqual(self.text.count('title="Petunjuk"'), 5)
        self.assertEqual(self.text.count('title="Pemeriksaan mandiri"'), 5)
        self.assertEqual(self.text.count('title="Jawaban dan solusi"'), 5)

    def test_clean_kernel_mastery_is_explicit(self) -> None:
        for phrase in (
            "keadaan tersembunyi",
            "Restart Kernel and Run All Cells",
            "NameError",
            "kernel Jupyter sungguhan",
            "o002-p01-clean-kernel.ipynb",
        ):
            self.assertIn(phrase, self.text)

    def test_every_executable_python_block_has_a_stable_label(self) -> None:
        self.assertEqual(self.text.count("```{python}"), 17)
        self.assertEqual(self.text.count("#| label:"), 17)


class Primer01NotebookKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        cls.cells_by_id = {cell["id"]: cell for cell in cls.notebook.cells}

    def test_notebook_uses_separate_actual_source_cells(self) -> None:
        source_a = self.cells_by_id["o002-p01-nb-source-a"]
        source_b = self.cells_by_id["o002-p01-nb-source-b"]
        self.assertEqual(source_a.cell_type, "code")
        self.assertEqual(source_b.cell_type, "code")
        self.assertIn("data = 7", source_a.source)
        self.assertIn("hasil = data * 2", source_b.source)
        combined = "\n".join(cell.source for cell in self.notebook.cells)
        self.assertNotIn("exec(", combined)
        self.assertNotIn("ruang_nama", combined)

    def test_source_b_fails_in_a_fresh_actual_kernel(self) -> None:
        notebook = nbformat.v4.new_notebook(
            metadata=copy.deepcopy(self.notebook.metadata),
            cells=[copy.deepcopy(self.cells_by_id["o002-p01-nb-source-b"])],
        )
        client = NotebookClient(
            notebook,
            timeout=120,
            kernel_name="o002-frozen",
            resources={"metadata": {"path": str(ROOT)}},
        )
        with self.assertRaises(CellExecutionError) as caught:
            client.execute()
        self.assertIn("NameError", str(caught.exception))
        self.assertIn("data", str(caught.exception))

    def test_restart_and_run_all_succeeds_in_a_fresh_actual_kernel(self) -> None:
        notebook = copy.deepcopy(self.notebook)
        executed = NotebookClient(
            notebook,
            timeout=120,
            kernel_name="o002-frozen",
            resources={"metadata": {"path": str(ROOT)}},
        ).execute()
        source_b = next(
            cell for cell in executed.cells if cell["id"] == "o002-p01-nb-source-b"
        )
        output_text = "".join(
            output.get("text", "")
            for output in source_b.get("outputs", [])
            if output.get("output_type") == "stream"
        )
        self.assertIn("14", output_text)


if __name__ == "__main__":
    unittest.main()
