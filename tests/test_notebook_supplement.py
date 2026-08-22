from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError
from jupyter_client.kernelspec import KernelSpecManager


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "make_notebook_supplement.py"
NOTEBOOK_PATH = ROOT / "source" / "notebooks" / "o002-p01-clean-kernel.ipynb"
SPEC = importlib.util.spec_from_file_location("make_notebook_supplement", SCRIPT_PATH)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class NotebookSupplementTests(unittest.TestCase):
    def test_generator_is_byte_deterministic_and_matches_registered_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.ipynb"
            second = Path(directory) / "second.ipynb"
            generator.write_notebook(first)
            generator.write_notebook(second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first.read_bytes(), NOTEBOOK_PATH.read_bytes())

    def test_nbformat_kernel_and_portability_metadata(self) -> None:
        raw = NOTEBOOK_PATH.read_bytes()
        notebook = nbformat.reads(raw.decode("utf-8"), as_version=4)
        nbformat.validate(notebook)

        self.assertEqual(notebook.metadata.kernelspec.name, "o002-frozen")
        self.assertEqual(notebook.metadata.kernelspec.display_name, "o002-frozen")
        self.assertEqual(notebook.metadata.kernelspec.language, "python")
        self.assertEqual(notebook.metadata.o002.identifier, "o002.p01.notebook.clean-kernel")
        self.assertEqual(notebook.metadata.o002.language, "id-ID")
        self.assertFalse(notebook.metadata.o002.network_required)

        decoded = raw.decode("utf-8")
        payload = json.loads(decoded)
        portable_text = "\n".join(
            [cell.source for cell in notebook.cells]
            + [json.dumps(payload["metadata"], ensure_ascii=False)]
        )
        self.assertIsNone(re.search(r"(?<![A-Za-z])[A-Za-z]:[\\/]", portable_text))
        self.assertNotIn("/Users/", portable_text)
        self.assertNotIn("/home/", portable_text)
        self.assertNotIn("timestamp", json.dumps(payload["metadata"]).lower())

    def test_actual_source_cells_and_interactive_protocol_are_explicit(self) -> None:
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        by_id = {cell.id: cell for cell in notebook.cells}
        required = {
            "o002-p01-nb-protocol",
            "o002-p01-nb-source-a",
            "o002-p01-nb-source-b",
            "o002-p01-nb-final-check",
        }
        self.assertTrue(required.issubset(by_id))
        self.assertIn("Restart Kernel", by_id["o002-p01-nb-protocol"].source)
        self.assertIn("data = 7", by_id["o002-p01-nb-source-a"].source)
        self.assertIn("hasil = data * 2", by_id["o002-p01-nb-source-b"].source)
        combined = "\n".join(cell.source for cell in notebook.cells)
        self.assertNotIn("exec(", combined)
        self.assertNotIn("ruang_nama", combined)

    def test_source_b_fails_in_a_fresh_actual_kernel(self) -> None:
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        by_id = {cell.id: cell for cell in notebook.cells}
        b_only = nbformat.v4.new_notebook(
            metadata=copy.deepcopy(notebook.metadata),
            cells=[copy.deepcopy(by_id["o002-p01-nb-source-b"])],
        )
        client = NotebookClient(
            b_only,
            timeout=60,
            kernel_name="o002-frozen",
            resources={"metadata": {"path": str(ROOT)}},
        )
        with self.assertRaises(CellExecutionError) as caught:
            client.execute()
        self.assertIn("NameError", str(caught.exception))
        self.assertIn("data", str(caught.exception))

    def test_notebook_executes_from_clean_kernel_at_project_root(self) -> None:
        notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
        available = KernelSpecManager().find_kernel_specs()
        self.assertIn(
            "o002-frozen",
            available,
            "JUPYTER_PATH harus memuat kernelspec beku proyek sebelum tes dijalankan",
        )
        client = NotebookClient(
            notebook,
            timeout=60,
            kernel_name="o002-frozen",
            resources={"metadata": {"path": str(ROOT)}},
        )
        executed = client.execute()

        code_cells = [cell for cell in executed.cells if cell.cell_type == "code"]
        self.assertTrue(code_cells)
        self.assertTrue(all(cell.execution_count is not None for cell in code_cells))
        errors = [
            output
            for cell in code_cells
            for output in cell.outputs
            if output.output_type == "error"
        ]
        self.assertEqual(errors, [])

        final = next(cell for cell in executed.cells if cell.id == "o002-p01-nb-final-check")
        final_text = json.dumps(final.outputs, ensure_ascii=False)
        self.assertIn("Restart dan Run All berhasil", final_text)


if __name__ == "__main__":
    unittest.main()
