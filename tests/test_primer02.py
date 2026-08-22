# SPDX-License-Identifier: MIT
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "primer02_control_files.py"
QMD_PATH = ROOT / "source" / "units" / "p02-kontrol-koleksi-fungsi-modul-berkas.qmd"
SPEC = importlib.util.spec_from_file_location("primer02_control_files", MODULE_PATH)
assert SPEC and SPEC.loader
primer02 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(primer02)


def load_learner_module(path: Path):
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"modul peserta tidak ditemukan: {resolved}")
    spec = importlib.util.spec_from_file_location("o002_p02_learner", resolved)
    if spec is None or spec.loader is None:
        raise ImportError(f"modul peserta tidak dapat dimuat: {resolved}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Primer02ExerciseChecks(unittest.TestCase):
    def test_exercise_01_collections(self) -> None:
        report = primer02.collection_report([4, 1, 4, 2])
        self.assertEqual(report["first"], 4)
        self.assertEqual(report["last"], 2)
        self.assertEqual(report["middle"], [1, 4])
        self.assertEqual(report["first_pair"], (4, 1))
        self.assertEqual(report["unique_sorted"], [1, 2, 4])
        self.assertEqual(report["positions"], {"0": 4, "1": 1, "2": 4, "3": 2})

    def test_exercise_02_control_flow(self) -> None:
        values = [5, 2, -4, 3, 0]
        self.assertEqual(primer02.even_squares_explicit(values), [4, 16, 0])
        self.assertEqual(
            primer02.even_squares_explicit(values),
            primer02.even_squares_comprehension(values),
        )
        self.assertEqual(primer02.countdown(3), [3, 2, 1, 0])

    def test_exercise_03_functions_scope_and_errors(self) -> None:
        self.assertEqual(primer02.safe_mean([2, 4, 9]), 5.0)
        with self.assertRaisesRegex(ValueError, "tidak boleh kosong"):
            primer02.safe_mean([])
        with self.assertRaisesRegex(TypeError, r"values\[1\]"):
            primer02.safe_mean([2, "empat"])

    def test_exercise_04_learner_module(self) -> None:
        self.assertEqual(primer02.positive_total([3, -8, 2, 0]), 5)
        self.assertEqual(primer02.positive_total([-3, 0]), 0)
        with self.assertRaises(TypeError):
            primer02.positive_total([1, True])

    def test_exercise_05_files_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "bundle"
            manifest = primer02.write_demo_bundle(output_dir)
            self.assertEqual(manifest["schema"], "o002.p02.bundle-manifest.v1")
            self.assertEqual(len(manifest["artifacts"]), 3)
            self.assertEqual(
                sorted(path.name for path in output_dir.iterdir()),
                ["manifest.json", "measurements.csv", "summary.json", "values.txt"],
            )


class Primer02LearnerCheck(unittest.TestCase):
    """Cek yang hanya dimuat lewat CLI terhadap modul milik peserta."""

    learner = None
    learner_module_path: Path | None = None
    learner_test_path: Path | None = None

    def require_function(self, name: str):
        function = getattr(self.learner, name, None)
        self.assertTrue(callable(function), f"modul peserta harus mendefinisikan {name}")
        return function

    def check_exercise_01(self) -> None:
        collection_report = self.require_function("collection_report")
        report = collection_report([4, 1, 4, 2])
        self.assertEqual(
            report,
            {
                "first": 4,
                "last": 2,
                "middle": [1, 4],
                "first_pair": (4, 1),
                "unique_sorted": [1, 2, 4],
                "positions": {"0": 4, "1": 1, "2": 4, "3": 2},
            },
        )
        with self.assertRaises(ValueError):
            collection_report([])

    def check_exercise_02(self) -> None:
        explicit = self.require_function("even_squares_explicit")
        compact = self.require_function("even_squares_comprehension")
        countdown = self.require_function("countdown")
        values = [5, 2, -4, 3, 0]
        self.assertEqual(explicit(values), [4, 16, 0])
        self.assertEqual(compact(values), explicit(values))
        self.assertEqual(explicit([8, 7, -2]), [64, 4])
        self.assertEqual(compact([8, 7, -2]), [64, 4])
        self.assertEqual(countdown(3), [3, 2, 1, 0])
        self.assertEqual(countdown(0), [0])
        with self.assertRaises(ValueError):
            countdown(-1)

    def check_exercise_03(self) -> None:
        safe_mean = self.require_function("safe_mean")
        self.assertEqual(safe_mean([2, 4, 9]), 5.0)
        self.assertEqual(safe_mean(value for value in (1, 2, 6)), 3.0)
        with self.assertRaises(ValueError):
            safe_mean([])
        with self.assertRaises(TypeError):
            safe_mean([2, "empat"])
        with self.assertRaises(TypeError):
            safe_mean([2, True])

    def check_exercise_04(self) -> None:
        positive_total = self.require_function("positive_total")
        self.assertEqual(positive_total([3, -8, 2, 0]), 5)
        self.assertEqual(positive_total([-3, 0]), 0)
        self.assertEqual(positive_total([7, -1, 4]), 11)

        self.assertIsNotNone(self.learner_module_path)
        self.assertIsNotNone(self.learner_test_path)
        assert self.learner_module_path is not None
        assert self.learner_test_path is not None
        self.assertTrue(
            self.learner_test_path.is_file(),
            f"berkas tes peserta tidak ditemukan: {self.learner_test_path}",
        )

        def run_same_tests(module_bytes: bytes) -> subprocess.CompletedProcess[str]:
            with tempfile.TemporaryDirectory() as directory:
                work = Path(directory)
                (work / "positive_math.py").write_bytes(module_bytes)
                (work / "test_positive_math.py").write_bytes(
                    self.learner_test_path.read_bytes()
                )
                return subprocess.run(
                    [sys.executable, "-B", "-m", "unittest", "-v", "test_positive_math.py"],
                    cwd=work,
                    check=False,
                    capture_output=True,
                    text=True,
                )

        broken = run_same_tests(
            b"def positive_total(values):\n    return sum(values)\n"
        )
        broken_log = broken.stdout + broken.stderr
        broken_count = re.search(r"Ran (\d+) tests?", broken_log)
        self.assertIsNotNone(broken_count, broken_log)
        assert broken_count is not None
        self.assertGreaterEqual(int(broken_count.group(1)), 2)
        self.assertNotEqual(
            broken.returncode,
            0,
            "tes peserta tidak menjadi merah untuk implementasi sum(values) yang salah",
        )

        fixed = run_same_tests(self.learner_module_path.read_bytes())
        fixed_log = fixed.stdout + fixed.stderr
        fixed_count = re.search(r"Ran (\d+) tests?", fixed_log)
        self.assertIsNotNone(fixed_count, fixed_log)
        assert fixed_count is not None
        self.assertGreaterEqual(int(fixed_count.group(1)), 2)
        self.assertEqual(
            fixed.returncode,
            0,
            "tes peserta tidak menjadi hijau untuk modul akhir:\n" + fixed_log,
        )

    def check_exercise_05(self) -> None:
        write_demo_bundle = self.require_function("write_demo_bundle")
        with tempfile.TemporaryDirectory() as directory:
            output_dirs = (
                Path(directory) / "bundle-peserta-a",
                Path(directory) / "bundle-peserta-b",
            )
            for output_dir in output_dirs:
                write_demo_bundle(output_dir)
            expected_names = {
                "manifest.json",
                "measurements.csv",
                "summary.json",
                "values.txt",
            }
            for output_dir in output_dirs:
                self.assertEqual(
                    {path.name for path in output_dir.iterdir()}, expected_names
                )
            for name in expected_names:
                self.assertEqual(
                    (output_dirs[0] / name).read_bytes(),
                    (output_dirs[1] / name).read_bytes(),
                )
            manifest = json.loads(
                (output_dirs[0] / "manifest.json").read_text(encoding="utf-8")
            )
            self.assertEqual(manifest["schema"], "o002.p02.bundle-manifest.v1")
            records = {record["path"]: record for record in manifest["artifacts"]}
            self.assertEqual(set(records), expected_names - {"manifest.json"})
            for name, record in records.items():
                self.assertEqual(Path(record["path"]), Path(name))
                self.assertFalse(Path(record["path"]).is_absolute())
                content = (output_dirs[0] / name).read_bytes()
                self.assertEqual(record["bytes"], len(content))
                self.assertEqual(record["sha256"], hashlib.sha256(content).hexdigest())

            values_text = (output_dirs[0] / "values.txt").read_text(encoding="utf-8")
            self.assertTrue(values_text.endswith("\n"))
            values = [int(line) for line in values_text.splitlines()]
            self.assertTrue(values)

            with (output_dirs[0] / "measurements.csv").open(
                "r", encoding="utf-8", newline=""
            ) as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(reader.fieldnames, ["sample_id", "value"])
                rows = list(reader)
            self.assertEqual([int(row["value"]) for row in rows], values)
            sample_ids = [row["sample_id"] for row in rows]
            self.assertTrue(all(sample_ids))
            self.assertEqual(len(sample_ids), len(set(sample_ids)))

            summary = json.loads(
                (output_dirs[0] / "summary.json").read_text(encoding="utf-8")
            )
            expected_summary = {
                "count": len(values),
                "even_squares": [value * value for value in values if value % 2 == 0],
                "mean": sum(values) / len(values),
                "positive_total": sum(value for value in values if value > 0),
                "sample_ids": sample_ids,
                "schema": "o002.p02.summary.v1",
            }
            self.assertEqual(summary, expected_summary)

            manifest_core = {
                "artifacts": manifest["artifacts"],
                "schema": "o002.p02.bundle-manifest.v1",
            }
            self.assertEqual(
                manifest.get("core_sha256"),
                hashlib.sha256(
                    (json.dumps(manifest_core, indent=2, sort_keys=True) + "\n").encode(
                        "utf-8"
                    )
                ).hexdigest(),
            )


class Primer02ContractTests(unittest.TestCase):
    def test_reader_has_five_closed_learner_targeted_exercises(self) -> None:
        qmd = QMD_PATH.read_text(encoding="utf-8")
        for number in range(1, 6):
            self.assertEqual(qmd.count(f"#ex-o002-p02-{number:02d}"), 1)
            self.assertIn(
                f"--exercise {number:02d}",
                qmd,
            )
        self.assertEqual(qmd.count("--learner-module"), 5)
        self.assertEqual(qmd.count('title="Petunjuk"'), 5)
        self.assertEqual(qmd.count('title="Cek yang dapat dijalankan"'), 5)
        self.assertEqual(qmd.count('title="Jawaban dan solusi"'), 5)
        self.assertIn("#sec-o002-p02-generator", qmd)
        self.assertIn("tuple(expression for ...)", qmd)

        exercise_one = qmd.split("#ex-o002-p02-01", maxsplit=1)[1].split(
            "#ex-o002-p02-02", maxsplit=1
        )[0]
        self.assertIn("positions", exercise_one)
        self.assertIn("enumerate(values)", exercise_one)

    def test_invalid_collections_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            primer02.collection_report([])
        with self.assertRaises(TypeError):
            primer02.collection_report([1, 2.5])
        with self.assertRaises(TypeError):
            primer02.even_squares_explicit([2, True])

    def test_while_loop_contract(self) -> None:
        self.assertEqual(primer02.countdown(0), [0])
        with self.assertRaises(ValueError):
            primer02.countdown(-1)
        with self.assertRaises(TypeError):
            primer02.countdown(2.5)

    def test_parse_integer_lines_reports_the_source_line(self) -> None:
        self.assertEqual(primer02.parse_integer_lines("2\n\n-3\n"), [2, -3])
        with self.assertRaisesRegex(ValueError, "baris 3"):
            primer02.parse_integer_lines("2\n3\ntiga\n")

    def test_csv_reader_validates_columns_and_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "measurements.csv"
            path.write_text("sample_id,value\nS01,7\n", encoding="utf-8")
            self.assertEqual(
                primer02.read_csv_rows(path),
                [{"sample_id": "S01", "value": 7}],
            )
            path.write_text("sample_id,value\nS01,tujuh\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "baris 2"):
                primer02.read_csv_rows(path)

    def test_bundle_is_byte_deterministic_and_hash_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first"
            second = Path(directory) / "second"
            first_manifest = primer02.write_demo_bundle(first)
            second_manifest = primer02.write_demo_bundle(second)

            first_names = sorted(path.name for path in first.iterdir())
            second_names = sorted(path.name for path in second.iterdir())
            self.assertEqual(first_names, second_names)
            for name in first_names:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

            core = {
                key: value
                for key, value in first_manifest.items()
                if key != "core_sha256"
            }
            self.assertEqual(
                first_manifest["core_sha256"],
                hashlib.sha256(primer02.canonical_json_bytes(core)).hexdigest(),
            )
            summary = json.loads((first / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["mean"], 2.0)

    def test_import_has_no_output_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [sys.executable, "-c", f"import runpy; runpy.run_path({str(MODULE_PATH)!r})"],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_cli_writes_documented_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "result"
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--output-dir", str(output_dir)],
                cwd=directory,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertTrue((output_dir / "manifest.json").is_file())

    def test_learner_cli_uses_the_supplied_module_and_rejects_wrong_work(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            learner = Path(directory) / "latihan_p02.py"
            learner.write_text(
                textwrap.dedent(
                    '''
                    import hashlib
                    import json
                    from pathlib import Path

                    def collection_report(values):
                        if not values:
                            raise ValueError("kosong")
                        return {
                            "first": values[0], "last": values[-1],
                            "middle": values[1:-1],
                            "first_pair": tuple(values[:2]),
                            "unique_sorted": sorted(set(values)),
                            "positions": {
                                str(index): value
                                for index, value in enumerate(values)
                            },
                        }

                    def even_squares_explicit(values):
                        result = []
                        for value in values:
                            if value % 2 == 0:
                                result.append(value * value)
                        return result

                    def even_squares_comprehension(values):
                        return [value * value for value in values if value % 2 == 0]

                    def countdown(start):
                        if start < 0:
                            raise ValueError("negatif")
                        result = []
                        while start > 0:
                            result.append(start)
                            start -= 1
                        result.append(0)
                        return result

                    def safe_mean(values):
                        values = tuple(values)
                        if not values:
                            raise ValueError("kosong")
                        total = 0.0
                        for value in values:
                            if isinstance(value, bool) or not isinstance(value, (int, float)):
                                raise TypeError("bukan angka")
                            total += value
                        return total / len(values)

                    def positive_total(values):
                        total = 0
                        for value in values:
                            if value > 0:
                                total += value
                        return total

                    def write_demo_bundle(output_dir):
                        output_dir = Path(output_dir)
                        output_dir.mkdir(parents=True, exist_ok=True)
                        (output_dir / "values.txt").write_text(
                            "2\\n-1\\n5\\n2\\n", encoding="utf-8", newline="\\n"
                        )
                        (output_dir / "measurements.csv").write_text(
                            "sample_id,value\\nS01,2\\nS02,-1\\nS03,5\\nS04,2\\n",
                            encoding="utf-8", newline="\\n",
                        )
                        summary = {
                            "count": 4,
                            "even_squares": [4, 4],
                            "mean": 2.0,
                            "positive_total": 9,
                            "sample_ids": ["S01", "S02", "S03", "S04"],
                            "schema": "o002.p02.summary.v1",
                        }
                        (output_dir / "summary.json").write_text(
                            json.dumps(summary, indent=2, sort_keys=True) + "\\n",
                            encoding="utf-8", newline="\\n",
                        )
                        records = []
                        for name in ("values.txt", "measurements.csv", "summary.json"):
                            content = (output_dir / name).read_bytes()
                            records.append({
                                "bytes": len(content), "path": name,
                                "sha256": hashlib.sha256(content).hexdigest(),
                            })
                        manifest_core = {
                            "artifacts": records,
                            "schema": "o002.p02.bundle-manifest.v1",
                        }
                        manifest = dict(manifest_core)
                        manifest["core_sha256"] = hashlib.sha256(
                            (json.dumps(manifest_core, indent=2, sort_keys=True) + "\\n").encode(
                                "utf-8"
                            )
                        ).hexdigest()
                        (output_dir / "manifest.json").write_text(
                            json.dumps(manifest, indent=2, sort_keys=True) + "\\n",
                            encoding="utf-8", newline="\\n",
                        )
                        return manifest
                    '''
                ).lstrip(),
                encoding="utf-8",
                newline="\n",
            )
            learner_test = Path(directory) / "test_positive_math.py"
            learner_test.write_text(
                textwrap.dedent(
                    '''
                    import unittest

                    from positive_math import positive_total


                    class PositiveTotalTests(unittest.TestCase):
                        def test_mixed_values(self):
                            self.assertEqual(positive_total([3, -8, 2, 0]), 5)

                        def test_no_positive_values(self):
                            self.assertEqual(positive_total([-3, 0]), 0)


                    if __name__ == "__main__":
                        unittest.main()
                    '''
                ).lstrip(),
                encoding="utf-8",
                newline="\n",
            )
            for exercise in ("01", "02", "03", "04", "05"):
                command = [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--learner-module",
                    str(learner),
                    "--exercise",
                    exercise,
                ]
                if exercise == "04":
                    command.extend(["--learner-test", str(learner_test)])
                completed = subprocess.run(
                    command,
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)

            wrong = Path(directory) / "wrong.py"
            wrong.write_text(
                "def collection_report(values):\n    return {}\n",
                encoding="utf-8",
                newline="\n",
            )
            rejected = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--learner-module",
                    str(wrong),
                    "--exercise",
                    "01",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(rejected.returncode, 0)


def run_learner_check(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Jalankan satu cek P02 terhadap modul yang ditulis peserta."
    )
    parser.add_argument("--learner-module", type=Path, required=True)
    parser.add_argument("--learner-test", type=Path)
    parser.add_argument(
        "--exercise",
        choices=("01", "02", "03", "04", "05"),
        required=True,
    )
    args, _remaining = parser.parse_known_args(argv)
    if args.exercise == "04" and args.learner_test is None:
        parser.error("latihan 04 memerlukan --learner-test test_positive_math.py")
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    Primer02LearnerCheck.learner = load_learner_module(args.learner_module)
    Primer02LearnerCheck.learner_module_path = args.learner_module.resolve()
    Primer02LearnerCheck.learner_test_path = (
        args.learner_test.resolve() if args.learner_test is not None else None
    )
    suite = unittest.TestSuite(
        [Primer02LearnerCheck(f"check_exercise_{args.exercise}")]
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if "--learner-module" in sys.argv:
        raise SystemExit(run_learner_check(sys.argv[1:]))
    unittest.main()
