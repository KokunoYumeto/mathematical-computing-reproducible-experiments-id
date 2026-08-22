from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COLUMNS = ["path", "bytes", "sha256"]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"witness determinisme di luar lane O002: {path}") from error


def record(path: Path) -> dict[str, object]:
    resolved = path.resolve()
    return {
        "path": _relative(resolved),
        "bytes": resolved.stat().st_size,
        "sha256": sha256(resolved),
    }


def validate_manifest(path: Path) -> dict[str, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise RuntimeError(
                f"kolom manifest tidak sah {path.name}: {reader.fieldnames!r}"
            )
        rows = list(reader)
    if not rows:
        raise RuntimeError(f"manifest kosong: {path.name}")

    names: list[str] = []
    total_bytes = 0
    for row_number, row in enumerate(rows, start=2):
        name = str(row.get("path", ""))
        pure = PurePosixPath(name)
        if (
            not name
            or "\\" in name
            or pure.is_absolute()
            or any(part in {"", ".", ".."} for part in pure.parts)
            or pure.as_posix() != name
        ):
            raise RuntimeError(
                f"jalur manifest tidak aman pada baris {row_number}: {name!r}"
            )
        try:
            byte_count = int(str(row.get("bytes", "")))
        except ValueError as error:
            raise RuntimeError(
                f"jumlah byte tidak sah pada baris {row_number}: {path.name}"
            ) from error
        if byte_count < 0 or str(byte_count) != str(row.get("bytes", "")):
            raise RuntimeError(
                f"jumlah byte tidak kanonik pada baris {row_number}: {path.name}"
            )
        digest = str(row.get("sha256", ""))
        if SHA256_RE.fullmatch(digest) is None:
            raise RuntimeError(
                f"SHA-256 tidak sah pada baris {row_number}: {path.name}"
            )
        names.append(name)
        total_bytes += byte_count

    folded = [name.casefold() for name in names]
    if len(folded) != len(set(folded)):
        raise RuntimeError(f"jalur duplikat setelah case folding: {path.name}")
    if names != sorted(names, key=str.casefold):
        raise RuntimeError(f"baris manifest tidak diurutkan: {path.name}")
    return {"row_count": len(rows), "total_bytes": total_bytes}


def _write_receipt(path: Path, payload: dict[str, object]) -> None:
    data = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(data)
    if json.loads(temporary.read_bytes()) != payload:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("readback receipt determinisme gagal")
    temporary.replace(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prove two clean O002 source/output manifests are byte-identical."
    )
    parser.add_argument("--first-source", type=Path, required=True)
    parser.add_argument("--second-source", type=Path, required=True)
    parser.add_argument("--first-output", type=Path, required=True)
    parser.add_argument("--second-output", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    inputs = [
        args.first_source.resolve(),
        args.second_source.resolve(),
        args.first_output.resolve(),
        args.second_output.resolve(),
    ]
    for path in inputs:
        _relative(path)
        if not path.is_file():
            raise FileNotFoundError(path)
    if len(set(inputs)) != len(inputs):
        raise ValueError("empat witness manifest harus memakai empat jalur berbeda")

    receipt_path = args.receipt.resolve()
    _relative(receipt_path)
    if receipt_path in inputs:
        raise ValueError("receipt determinisme tidak boleh menggantikan witness")

    pairs = (
        ("source", inputs[0], inputs[1]),
        ("output", inputs[2], inputs[3]),
    )
    comparisons: list[dict[str, object]] = []
    builds: list[dict[str, object]] = [
        {"ordinal": 1, "source_manifest": record(inputs[0]), "output_manifest": record(inputs[2])},
        {"ordinal": 2, "source_manifest": record(inputs[1]), "output_manifest": record(inputs[3])},
    ]
    for kind, first, second in pairs:
        first_summary = validate_manifest(first)
        second_summary = validate_manifest(second)
        identical = first.read_bytes() == second.read_bytes()
        comparison = {
            "kind": kind,
            "first": {**record(first), **first_summary},
            "second": {**record(second), **second_summary},
            "byte_identical": identical,
            "row_count_identical": first_summary["row_count"] == second_summary["row_count"],
            "total_bytes_identical": first_summary["total_bytes"] == second_summary["total_bytes"],
        }
        comparisons.append(comparison)
        if not identical:
            raise RuntimeError(f"manifest {kind} berbeda antara dua build bersih")

    receipt = {
        "schema": "o002.build-determinism.v1",
        "successful": True,
        "clean_build_count": 2,
        "builds": builds,
        "comparisons": comparisons,
        "checks": {
            "four_distinct_witness_paths": True,
            "csv_schema_and_rows_valid": True,
            "source_manifests_byte_identical": True,
            "output_manifests_byte_identical": True,
        },
    }
    _write_receipt(receipt_path, receipt)
    print("build determinism passed: source and output manifests are byte-identical")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
