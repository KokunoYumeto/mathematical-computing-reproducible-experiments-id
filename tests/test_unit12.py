from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit12_capstone.py"
SPEC = importlib.util.spec_from_file_location("unit12_capstone", MODULE_PATH)
assert SPEC and SPEC.loader
unit12 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit12)


class Unit12CapstoneTests(unittest.TestCase):
    def sample_manifest(self, payload: bytes) -> dict[str, object]:
        return {
            "schema": "o002.run-manifest.v1",
            "command": ["python", "source/run.py"],
            "environment": {
                "runtime": "Python",
                "runtime_version": "3.13.1",
                "dependencies": [],
            },
            "parameters": {},
            "inputs": [],
            "outputs": ["outputs/result.txt"],
            "artifacts": [
                {
                    "path": "outputs/result.txt",
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
            ],
            "claims": [
                {
                    "id": "claim-001",
                    "kind": "empirical",
                    "statement": "Nilai contoh cocok pada domain uji.",
                    "evidence": "outputs/result.txt",
                    "limitations": "Belum merupakan bukti universal.",
                }
            ],
        }

    def test_valid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs" / "result.txt"
            output.parent.mkdir()
            output.write_bytes(b"42\n")
            result = unit12.verify_manifest(root, self.sample_manifest(b"42\n"))
            self.assertTrue(result["verified"])
            self.assertEqual(result["claims_checked"], 1)
            self.assertEqual(
                result["claim_evidence_bindings"],
                [
                    {
                        "claim_id": "claim-001",
                        "evidence_path": "outputs/result.txt",
                        "evidence_sha256": hashlib.sha256(b"42\n").hexdigest(),
                    }
                ],
            )

    def test_empty_artifact_or_claim_set_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self.sample_manifest(b"42\n")
            manifest["artifacts"] = []
            with self.assertRaisesRegex(ValueError, "setidaknya satu artefak"):
                unit12.verify_manifest(root, manifest)

            manifest = self.sample_manifest(b"42\n")
            manifest["claims"] = []
            with self.assertRaisesRegex(ValueError, "setidaknya satu klaim"):
                unit12.verify_manifest(root, manifest)

    def test_execution_contract_fields_are_required(self) -> None:
        manifest = self.sample_manifest(b"42\n")
        del manifest["command"]
        with self.assertRaisesRegex(ValueError, "medan manifest hilang: command"):
            unit12.verify_manifest(Path("."), manifest)

    def test_execution_contract_shapes_are_validated(self) -> None:
        manifest = self.sample_manifest(b"42\n")
        manifest["command"] = "python source/run.py"
        with self.assertRaisesRegex(ValueError, "command harus berupa larik"):
            unit12.verify_manifest(Path("."), manifest)

        manifest = self.sample_manifest(b"42\n")
        manifest["environment"] = {"runtime": "Python"}
        with self.assertRaisesRegex(ValueError, "medan environment hilang"):
            unit12.verify_manifest(Path("."), manifest)

    def test_claim_evidence_must_be_a_declared_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "inputs" / "result.txt"
            artifact.parent.mkdir()
            artifact.write_bytes(b"42\n")
            manifest = self.sample_manifest(b"42\n")
            manifest["artifacts"][0]["path"] = "inputs/result.txt"
            manifest["inputs"] = ["inputs/result.txt"]
            manifest["outputs"] = ["outputs/missing.txt"]
            manifest["claims"][0]["evidence"] = "inputs/result.txt"
            with self.assertRaisesRegex(ValueError, "outputs tidak merujuk"):
                unit12.verify_manifest(root, manifest)

    def test_changed_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs" / "result.txt"
            output.parent.mkdir()
            output.write_bytes(b"43\n")
            with self.assertRaises(ValueError):
                unit12.verify_manifest(root, self.sample_manifest(b"42\n"))

    def test_missing_artifact_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaisesRegex(FileNotFoundError, "artefak tidak ditemukan"):
                unit12.verify_manifest(root, self.sample_manifest(b"42\n"))

    def test_nonexistent_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs" / "result.txt"
            output.parent.mkdir()
            output.write_bytes(b"42\n")
            manifest = self.sample_manifest(b"42\n")
            manifest["claims"][0]["evidence"] = "outputs/missing.txt"
            with self.assertRaisesRegex(ValueError, "tidak merujuk artefak terdaftar"):
                unit12.verify_manifest(root, manifest)

    def test_existing_but_unadmitted_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outputs = root / "outputs"
            outputs.mkdir()
            (outputs / "result.txt").write_bytes(b"42\n")
            (outputs / "other.txt").write_bytes(b"support\n")
            manifest = self.sample_manifest(b"42\n")
            manifest["claims"][0]["evidence"] = "outputs/other.txt"
            with self.assertRaisesRegex(ValueError, "tidak merujuk artefak terdaftar"):
                unit12.verify_manifest(root, manifest)

    def test_duplicate_artifact_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs" / "result.txt"
            output.parent.mkdir()
            output.write_bytes(b"42\n")
            manifest = self.sample_manifest(b"42\n")
            manifest["artifacts"].append(dict(manifest["artifacts"][0]))
            with self.assertRaisesRegex(ValueError, "jalur artefak duplikat"):
                unit12.verify_manifest(root, manifest)

    def test_duplicate_claim_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs" / "result.txt"
            output.parent.mkdir()
            output.write_bytes(b"42\n")
            manifest = self.sample_manifest(b"42\n")
            manifest["claims"].append(dict(manifest["claims"][0]))
            with self.assertRaisesRegex(ValueError, "ID klaim duplikat"):
                unit12.verify_manifest(root, manifest)

    def test_parent_path_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                unit12.safe_member(Path(tmp), "../secret.txt")

    def test_unsafe_evidence_path_is_rejected_by_verifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "outputs" / "result.txt"
            output.parent.mkdir()
            output.write_bytes(b"42\n")
            manifest = self.sample_manifest(b"42\n")
            manifest["claims"][0]["evidence"] = "../secret.txt"
            with self.assertRaisesRegex(ValueError, "jalur paket tidak aman"):
                unit12.verify_manifest(root, manifest)

    def test_nonportable_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for unsafe in (
                "Z:/absolute/result.txt",
                "outputs\\result.txt",
                "outputs/./result.txt",
                "/outputs/result.txt",
            ):
                with self.subTest(path=unsafe):
                    with self.assertRaises(ValueError):
                        unit12.safe_member(root, unsafe)

    def test_unknown_claim_kind_is_rejected(self) -> None:
        errors = unit12.validate_claim(
            {
                "id": "claim-001",
                "kind": "opinion",
                "statement": "x",
                "evidence": "y",
                "limitations": "z",
            }
        )
        self.assertTrue(any("jenis klaim" in error for error in errors))

    def test_non_string_evidence_is_rejected(self) -> None:
        errors = unit12.validate_claim(
            {
                "id": "claim-001",
                "kind": "empirical",
                "statement": "x",
                "evidence": ["outputs/result.txt"],
                "limitations": "z",
            }
        )
        self.assertIn("medan klaim bukan string: evidence", errors)

    def test_canonical_json_is_stable(self) -> None:
        first = unit12.canonical_json_bytes({"b": 2, "a": 1})
        second = unit12.canonical_json_bytes({"a": 1, "b": 2})
        self.assertEqual(first, second)
        self.assertEqual(json.loads(first), {"a": 1, "b": 2})

    def test_concise_cli_uses_documented_default_layout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            working = Path(tmp)
            project = working / "project"
            artifact = project / "outputs" / "result.txt"
            artifact.parent.mkdir(parents=True)
            artifact.write_bytes(b"42\n")
            (project / "RUN_MANIFEST.json").write_text(
                json.dumps(self.sample_manifest(b"42\n")),
                encoding="utf-8",
                newline="\n",
            )
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "verify"],
                cwd=working,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(
                (working / "output" / "unit12-results.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertTrue(result["verified"])


if __name__ == "__main__":
    unittest.main()
