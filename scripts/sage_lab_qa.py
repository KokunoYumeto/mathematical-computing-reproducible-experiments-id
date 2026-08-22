from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
WSL_DISTRIBUTION = "Ubuntu-22.04"
SAGE = "/usr/bin/sage"
LAB = Path("source/code/unit05_sage_lab.py")
TEST = Path("tests/test_unit05_sage.py")
ENVIRONMENT_RECEIPT = Path("environment/SAGE_ENVIRONMENT_RECEIPT.json")
ENVIRONMENT_LOCK = Path("environment/sage-ubuntu22.04-dpkg-lock.txt")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def run_sage(arguments: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "wsl.exe",
            "-d",
            WSL_DISTRIBUTION,
            "--cd",
            str(ROOT),
            "--",
            SAGE,
            "-python",
            *arguments,
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
    )


def file_record(path: Path) -> dict[str, object]:
    resolved = (ROOT / path).resolve()
    return {
        "path": relative(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Execute and bind the compulsory local Unit 5 Sage lab."
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    receipt_path = args.receipt.resolve()
    output_relative = relative(output)
    relative(receipt_path)

    environment = json.loads((ROOT / ENVIRONMENT_RECEIPT).read_text(encoding="utf-8"))
    if (
        environment.get("matches_runtime") is not True
        or environment.get("sage", {}).get("version") != "9.5"
        or environment.get("lock", {}).get("sha256") != sha256(ROOT / ENVIRONMENT_LOCK)
    ):
        raise RuntimeError("receipt lingkungan Sage belum cocok dengan lock lokal")

    lab_run = run_sage([LAB.as_posix(), "--output", output_relative])
    if lab_run.returncode != 0:
        raise RuntimeError(f"eksekusi lab Sage gagal: {lab_run.stderr.strip()}")
    if not output.is_file():
        raise RuntimeError("lab Sage tidak menghasilkan JSON keluaran")
    result = json.loads(output.read_text(encoding="utf-8"))
    if (
        result.get("schema") != "o002.unit05.sage-lab.v1"
        or result.get("runtime", {}).get("sage") != "9.5"
        or result.get("runtime", {}).get("local_execution_required") is not True
        or result.get("runtime", {}).get("remote_service_satisfies_requirement") is not False
    ):
        raise RuntimeError("hasil lab Sage tidak memuat kontrak runtime wajib")

    test_run = run_sage([TEST.as_posix()])
    diagnostic = test_run.stdout + test_run.stderr
    test_match = re.search(r"Ran (\d+) tests?", diagnostic)
    if (
        test_run.returncode != 0
        or test_match is None
        or int(test_match.group(1)) < 7
        or not re.search(r"^OK\s*$", diagnostic, re.MULTILINE)
    ):
        raise RuntimeError(f"suite Sage gagal:\n{diagnostic.strip()}")

    receipt = {
        "schema": "o002.sage-lab-qa.v1",
        "successful": True,
        "runtime": {
            "wsl_distribution": WSL_DISTRIBUTION,
            "sage": "9.5",
            "environment_receipt": file_record(ENVIRONMENT_RECEIPT),
            "environment_lock": file_record(ENVIRONMENT_LOCK),
        },
        "source": file_record(LAB),
        "test_source": file_record(TEST),
        "result": file_record(Path(output_relative)),
        "tests": {
            "command": "sage -python tests/test_unit05_sage.py",
            "tests_run": int(test_match.group(1)),
            "failures": 0,
            "errors": 0,
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Sage lab QA passed: {receipt['tests']['tests_run']} tests; "
        f"result SHA-256 {receipt['result']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
