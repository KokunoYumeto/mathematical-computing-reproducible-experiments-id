from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit05_sage_lab.py"
SAGE_AVAILABLE = importlib.util.find_spec("sage") is not None


def windows_path_to_wsl(path: Path) -> str:
    """Ubah jalur Windows absolut menjadi jalur /mnt untuk proses WSL."""

    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    if not drive:
        raise ValueError(f"jalur Windows tanpa drive: {resolved}")
    relative = resolved.as_posix().split(":/", maxsplit=1)[1]
    return f"/mnt/{drive}/{relative}"


if SAGE_AVAILABLE:
    SPEC = importlib.util.spec_from_file_location("unit05_sage_lab", MODULE_PATH)
    assert SPEC and SPEC.loader
    sage_lab = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(sage_lab)


    class Unit05SageRuntimeTests(unittest.TestCase):
        def test_exact_frozen_sage_runtime(self) -> None:
            self.assertEqual(sage_lab.SAGE_VERSION, "9.5")
            self.assertEqual(sage_lab.EXPECTED_SAGE_VERSION, "9.5")
            sage_lab.require_frozen_runtime()

        def test_ZZ_QQ_RR_SR_parents_and_coercion(self) -> None:
            record = sage_lab.parent_and_coercion_record()
            objects = record["objects"]
            self.assertEqual(objects["integer"]["parent"], "Integer Ring")
            self.assertEqual(objects["rational"]["parent"], "Rational Field")
            self.assertEqual(objects["real"]["precision_bits"], 53)
            self.assertEqual(objects["symbolic"]["parent"], "Symbolic Ring")
            self.assertTrue(all(record["coercion_maps"].values()))
            self.assertEqual(record["mixed_ZZ_plus_QQ"]["parent"], "Rational Field")

        def test_polynomial_ring_factorization_is_exact(self) -> None:
            record = sage_lab.polynomial_record()
            self.assertEqual(record["base_ring"], "Rational Field")
            self.assertEqual(record["polynomial"], "x^4 - 1")
            self.assertTrue(record["expands_back"])
            self.assertEqual(
                {item["factor"] for item in record["factors"]},
                {"x - 1", "x + 1", "x^2 + 1"},
            )

        def test_symbolic_solutions_have_exact_zero_residuals(self) -> None:
            record = sage_lab.solve_record()
            self.assertEqual(set(record["solutions"]), {"-sqrt(2)", "sqrt(2)"})
            self.assertEqual(record["zero_residuals"], [True, True])
            self.assertEqual(record["parent"], "Symbolic Ring")

        def test_approximate_conversion_is_explicit(self) -> None:
            record = sage_lab.approximation_record()
            self.assertEqual(record["exact"]["value"], "1/3")
            self.assertEqual(record["exact"]["parent"], "Rational Field")
            self.assertEqual(record["conversion"], "RR(QQ(1)/3)")
            self.assertEqual(record["approximate"]["precision_bits"], 53)
            self.assertTrue(record["conversion_is_explicit"])

        def test_receipt_is_canonical_and_complete(self) -> None:
            first = sage_lab.canonical_json_bytes(sage_lab.build_results())
            second = sage_lab.canonical_json_bytes(sage_lab.build_results())
            self.assertEqual(first, second)
            parsed = json.loads(first)
            self.assertEqual(parsed["schema"], "o002.unit05.sage-lab.v1")
            self.assertEqual(parsed["runtime"]["sage"], "9.5")
            self.assertTrue(parsed["runtime"]["local_execution_required"])
            self.assertFalse(parsed["runtime"]["remote_service_satisfies_requirement"])
            self.assertEqual(len(parsed["core_sha256"]), 64)

        def test_cli_relative_and_absolute_outputs_are_identical(self) -> None:
            with tempfile.TemporaryDirectory() as directory:
                temporary = Path(directory)
                relative_command = [
                    "/usr/bin/sage",
                    "-python",
                    str(MODULE_PATH),
                    "--output",
                    "relative.json",
                ]
                absolute_output = temporary / "absolute.json"
                absolute_command = [
                    "/usr/bin/sage",
                    "-python",
                    str(MODULE_PATH),
                    "--output",
                    str(absolute_output),
                ]
                relative = subprocess.run(
                    relative_command,
                    cwd=temporary,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                absolute = subprocess.run(
                    absolute_command,
                    cwd=temporary,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(relative.returncode, 0, relative.stderr)
                self.assertEqual(absolute.returncode, 0, absolute.stderr)
                self.assertEqual(
                    (temporary / "relative.json").read_bytes(),
                    absolute_output.read_bytes(),
                )


else:

    class Unit05SageWslBridgeTests(unittest.TestCase):
        def test_complete_suite_runs_under_wsl_sage_9_5(self) -> None:
            test_path = windows_path_to_wsl(Path(__file__))
            completed = subprocess.run(
                [
                    "wsl.exe",
                    "-d",
                    "Ubuntu-22.04",
                    "--",
                    "/usr/bin/sage",
                    "-python",
                    test_path,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                timeout=180,
            )
            diagnostic = completed.stdout + completed.stderr
            self.assertEqual(completed.returncode, 0, diagnostic)
            self.assertIn("Ran 7 tests", diagnostic)
            self.assertIn("OK", diagnostic)


if __name__ == "__main__":
    unittest.main()
