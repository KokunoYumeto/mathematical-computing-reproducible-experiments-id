"""Bangun notebook P01 deterministik yang menguji keadaan kernel aktual."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "source" / "notebooks" / "o002-p01-clean-kernel.ipynb"


def markdown_cell(cell_id: str, source: str, *tags: str) -> dict[str, Any]:
    return {
        "cell_type": "markdown",
        "id": cell_id,
        "metadata": {"tags": list(tags)},
        "source": source,
    }


def code_cell(cell_id: str, source: str, *tags: str) -> dict[str, Any]:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": cell_id,
        "metadata": {"tags": list(tags)},
        "outputs": [],
        "source": source,
    }


def build_notebook() -> dict[str, Any]:
    """Kembalikan notebook nbformat 4 tanpa waktu atau jalur absolut."""

    cells = [
        markdown_cell(
            "o002-p01-nb-intro",
            """# P01 — Keadaan tersembunyi dan kernel bersih

Notebook asli berbahasa Indonesia ini memakai keadaan kernel Jupyter yang
sebenarnya, bukan simulasi ruang nama. Sel A mendefinisikan `data`; Sel B
memakainya. Sumber lengkap harus berhasil setelah **Restart Kernel and Run All
Cells**, sedangkan Sel B sendirian pada kernel baru harus gagal dengan
`NameError`.
""",
            "o002-p01",
            "learner-facing",
        ),
        markdown_cell(
            "o002-p01-nb-protocol",
            """## Protokol interaktif

1. Jalankan Sel A, lalu Sel B. Sel B berhasil karena `data` sudah ada di kernel.
2. Pilih **Restart Kernel**, lalu jalankan Sel B lebih dahulu. `NameError`
   adalah hasil yang benar dan memperlihatkan dependensi tersembunyi.
3. Terakhir, pilih **Restart Kernel and Run All Cells**. Notebook lengkap harus
   selesai dan menghasilkan 14.

Tes proyek menjalankan Sel B sendirian pada kernel Jupyter baru dan juga
menjalankan notebook lengkap pada kernel Jupyter baru. Dengan demikian, kedua
keadaan itu diperiksa sebagai perilaku kernel aktual.
""",
            "o002-p01",
            "protocol",
        ),
        markdown_cell(
            "o002-p01-nb-source-a-heading",
            "## Sel A — sumber nilai",
            "o002-p01",
            "source-a",
        ),
        code_cell(
            "o002-p01-nb-source-a",
            """data = 7
print("Sel A menyimpan data =", data)
""",
            "o002-p01",
            "source-a",
            "must-pass",
        ),
        markdown_cell(
            "o002-p01-nb-source-b-heading",
            """## Sel B — memakai nilai sebelumnya

Pada kernel baru, menjalankan sel ini sebelum Sel A harus menghasilkan
`NameError`.
""",
            "o002-p01",
            "source-b",
        ),
        code_cell(
            "o002-p01-nb-source-b",
            """hasil = data * 2
assert hasil == 14
print("Sel B menghasilkan", hasil)
""",
            "o002-p01",
            "source-b",
            "must-pass",
        ),
        markdown_cell(
            "o002-p01-nb-interpretation",
            """## Interpretasi yang sah

- Keberhasilan Sel B setelah klik lama tidak membuktikan bahwa sumber notebook
  lengkap.
- `NameError` saat Sel B dijalankan lebih dahulu pada kernel baru mengungkap
  dependensi yang hilang.
- Keberhasilan restart/run-all membuktikan bahwa urutan sel yang direkam dapat
  dijalankan pada lingkungan ini.
- Pemeriksaan tersebut belum membuktikan bahwa model matematika benar atau
  bahwa lingkungan lain menghasilkan byte identik.
""",
            "o002-p01",
            "interpretation",
        ),
        code_cell(
            "o002-p01-nb-final-check",
            """assert data == 7
assert hasil == 14
restart_run_all_success = True
print("Restart dan Run All berhasil dari urutan sumber yang direkam.")
""",
            "o002-p01",
            "final-check",
            "must-pass",
        ),
    ]

    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "o002-frozen",
                "language": "python",
                "name": "o002-frozen",
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbconvert_exporter": "python",
                "pygments_lexer": "ipython3",
                "version": "3.13.1",
            },
            "o002": {
                "code_license": "MIT",
                "deterministic_source": True,
                "identifier": "o002.p01.notebook.clean-kernel",
                "language": "id-ID",
                "network_required": False,
                "text_license": "CC BY-SA 4.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def canonical_notebook_bytes(notebook: dict[str, Any]) -> bytes:
    return (
        json.dumps(notebook, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    ).encode("utf-8")


def write_notebook(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_notebook_bytes(build_notebook()))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(argv)
    write_notebook(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
