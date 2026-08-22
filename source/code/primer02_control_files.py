# SPDX-License-Identifier: MIT
"""Kode pendamping Primer P02: kontrol, koleksi, fungsi, modul, dan berkas."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Iterable, Sequence


SAMPLE_ROWS = (
    {"sample_id": "S01", "value": 2},
    {"sample_id": "S02", "value": -1},
    {"sample_id": "S03", "value": 5},
    {"sample_id": "S04", "value": 2},
)


def _require_integer(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} harus berupa bilangan bulat")
    return value


def collection_report(values: Sequence[int]) -> dict[str, object]:
    """Ringkas pengindeksan, pengirisan, tuple, dictionary, dan set."""
    items = list(values)
    if not items:
        raise ValueError("values tidak boleh kosong")
    for index, value in enumerate(items):
        _require_integer(value, f"values[{index}]")

    return {
        "first": items[0],
        "last": items[-1],
        "middle": items[1:-1],
        "first_pair": tuple(items[:2]),
        "unique_sorted": sorted(set(items)),
        "positions": {str(index): value for index, value in enumerate(items)},
    }


def even_squares_explicit(values: Iterable[int]) -> list[int]:
    """Pilih bilangan genap dan kuadratkan dengan if dan for eksplisit."""
    result: list[int] = []
    for index, value in enumerate(values):
        integer = _require_integer(value, f"values[{index}]")
        if integer % 2 == 0:
            result.append(integer * integer)
    return result


def even_squares_comprehension(values: Iterable[int]) -> list[int]:
    """Bentuk ringkas yang dipelajari setelah loop eksplisit dipahami."""
    checked: list[int] = []
    for index, value in enumerate(values):
        checked.append(_require_integer(value, f"values[{index}]"))
    return [value * value for value in checked if value % 2 == 0]


def countdown(start: int) -> list[int]:
    """Bangun hitung mundur dengan while dan varian yang terus mengecil."""
    current = _require_integer(start, "start")
    if current < 0:
        raise ValueError("start harus taknegatif")

    result: list[int] = []
    while current > 0:
        result.append(current)
        current -= 1
    result.append(0)
    return result


def safe_mean(values: Iterable[int | float]) -> float:
    """Kembalikan rata-rata; tolak koleksi kosong dan nilai bukan angka."""
    frozen = tuple(values)
    if not frozen:
        raise ValueError("values tidak boleh kosong")

    total = 0.0
    for index, value in enumerate(frozen):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"values[{index}] harus berupa angka")
        total += value
    return total / len(frozen)


def positive_total(values: Iterable[int]) -> int:
    """Solusi acuan untuk modul yang ditulis peserta pada Latihan 4."""
    total = 0
    for index, value in enumerate(values):
        integer = _require_integer(value, f"values[{index}]")
        if integer > 0:
            total += integer
    return total


def parse_integer_lines(text: str) -> list[int]:
    """Urai satu bilangan bulat per baris dan beri konteks pada galat."""
    values: list[int] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        token = raw_line.strip()
        if not token:
            continue
        try:
            values.append(int(token))
        except ValueError as error:
            raise ValueError(
                f"baris {line_number} bukan bilangan bulat: {token!r}"
            ) from error
    return values


def canonical_json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def canonical_csv_bytes(rows: Sequence[dict[str, int | str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=("sample_id", "value"),
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def read_csv_rows(path: Path) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    with path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["sample_id", "value"]:
            raise ValueError("kolom CSV harus sample_id,value")
        for line_number, row in enumerate(reader, start=2):
            sample_id = (row.get("sample_id") or "").strip()
            value_token = (row.get("value") or "").strip()
            if not sample_id:
                raise ValueError(f"sample_id kosong pada baris {line_number}")
            try:
                value = int(value_token)
            except ValueError as error:
                raise ValueError(
                    f"value pada baris {line_number} bukan bilangan bulat"
                ) from error
            rows.append({"sample_id": sample_id, "value": value})
    return rows


def _artifact_record(path: Path, relative_path: str) -> dict[str, object]:
    content = path.read_bytes()
    return {
        "bytes": len(content),
        "path": relative_path,
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def write_demo_bundle(output_dir: Path) -> dict[str, object]:
    """Tulis TXT, CSV, JSON, dan manifest deterministik untuk P02."""
    output_dir.mkdir(parents=True, exist_ok=True)

    values = [int(row["value"]) for row in SAMPLE_ROWS]
    text_path = output_dir / "values.txt"
    csv_path = output_dir / "measurements.csv"
    summary_path = output_dir / "summary.json"

    text_path.write_text(
        "".join(f"{value}\n" for value in values),
        encoding="utf-8",
        newline="\n",
    )
    csv_path.write_bytes(canonical_csv_bytes(SAMPLE_ROWS))

    parsed_text = parse_integer_lines(text_path.read_text(encoding="utf-8"))
    parsed_rows = read_csv_rows(csv_path)
    summary = {
        "count": len(parsed_rows),
        "even_squares": even_squares_explicit(parsed_text),
        "mean": safe_mean(parsed_text),
        "positive_total": positive_total(parsed_text),
        "sample_ids": [str(row["sample_id"]) for row in parsed_rows],
        "schema": "o002.p02.summary.v1",
    }
    summary_path.write_bytes(canonical_json_bytes(summary))

    artifacts = [
        _artifact_record(text_path, "values.txt"),
        _artifact_record(csv_path, "measurements.csv"),
        _artifact_record(summary_path, "summary.json"),
    ]
    manifest_core: dict[str, object] = {
        "artifacts": artifacts,
        "schema": "o002.p02.bundle-manifest.v1",
    }
    manifest = dict(manifest_core)
    manifest["core_sha256"] = hashlib.sha256(
        canonical_json_bytes(manifest_core)
    ).hexdigest()
    (output_dir / "manifest.json").write_bytes(canonical_json_bytes(manifest))
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Bangun bundel demonstrasi deterministik Primer P02."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output") / "primer02-demo",
    )
    args = parser.parse_args(argv)
    write_demo_bundle(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
