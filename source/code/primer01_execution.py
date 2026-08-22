"""Pendamping eksekusi untuk Primer P01.

Kode asli proyek O002 dan dilisensikan dengan lisensi MIT; lihat
``LICENSE-CODE.md``. Modul ini sengaja hanya memakai pustaka standar Python
agar eksperimen pertama dapat dijalankan pada lingkungan lokal yang bersih.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import platform
import sys
from typing import Any, Iterable, MutableMapping


SCHEMA = "o002.p01.execution.v1"


def scalar_snapshot() -> list[dict[str, Any]]:
    """Kembalikan contoh lima jenis nilai skalar dalam bentuk JSON-safe."""

    values = (
        ("jumlah", 8),
        ("toleransi", 0.01),
        ("label", "uji A"),
        ("lulus", True),
        ("catatan", None),
    )
    return [
        {"name": name, "type": type(value).__name__, "value": value}
        for name, value in values
    ]


def circle_area(radius: float) -> float:
    """Hitung luas lingkaran untuk jari-jari taknegatif."""

    if radius < 0:
        raise ValueError("radius tidak boleh negatif")
    return math.pi * radius**2


def computation_and_display(left: int, right: int) -> dict[str, Any]:
    """Pisahkan nilai hasil komputasi dari teks yang dipilih untuk ditampilkan."""

    value = left + right
    return {
        "computed_value": value,
        "display_text": f"{left} + {right} = {value}",
    }


def run_cells(
    cells: Iterable[str],
    namespace: MutableMapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Jalankan sel berurutan dan kembalikan nama buatan pengguna.

    Jika ``namespace`` dihilangkan, fungsi membuat ruang nama bersih. Memberi
    ruang nama lama meniru kernel notebook yang masih menyimpan keadaan. Fungsi
    ini hanya untuk potongan kode tepercaya yang ditulis pelajar sendiri.
    """

    working: MutableMapping[str, Any]
    working = {} if namespace is None else namespace
    for number, cell in enumerate(cells, start=1):
        compiled = compile(cell, f"<o002.p01.cell.{number}>", "exec")
        exec(compiled, working)
    return {
        name: value
        for name, value in working.items()
        if not name.startswith("__")
    }


def build_receipt() -> dict[str, Any]:
    """Bangun rekaman kecil yang mengikat contoh P01 pada runtime lokal."""

    clean = run_cells(("data = 7", "hasil = data * 2"))
    return {
        "schema": SCHEMA,
        "runtime": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
        },
        "scalars": scalar_snapshot(),
        "circle_area_radius_3": circle_area(3),
        "computation_and_display": computation_and_display(2, 3),
        "clean_run": {"data": clean["data"], "hasil": clean["hasil"]},
    }


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialisasi payload menjadi JSON UTF-8 yang kanonis untuk proyek ini."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_receipt(output: Path) -> None:
    """Tulis rekaman P01 secara deterministik."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(build_receipt()))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/p01-results.json"),
        help="jalur rekaman JSON",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write_receipt(args.output)
    print(f"Rekaman P01 ditulis ke {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
