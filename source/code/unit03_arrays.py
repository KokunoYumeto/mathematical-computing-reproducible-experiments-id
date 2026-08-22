"""Array NumPy dan keluaran deterministik untuk Unit 3.

Kode asli proyek O002; lihat LICENSE-CODE.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Sequence

import numpy as np


Numeric = int | float


def make_vector(
    values: Sequence[Numeric] | np.ndarray,
    *,
    dtype: str = "float64",
) -> np.ndarray:
    """Kembalikan salinan array satu dimensi dengan dtype yang dinyatakan."""

    vector = np.array(values, dtype=np.dtype(dtype), copy=True)
    if vector.ndim != 1:
        raise ValueError("values harus membentuk array satu dimensi")
    if vector.dtype.kind not in "ifu":
        raise TypeError("dtype harus berupa tipe numerik")
    return vector


def affine_transform(
    values: np.ndarray,
    scale: Numeric,
    shift: Numeric,
) -> np.ndarray:
    """Hitung scale*values+shift secara vektorisasi tanpa mengubah masukan."""

    vector = np.asarray(values)
    if vector.ndim != 1:
        raise ValueError("values harus berupa vektor satu dimensi")
    if vector.dtype.kind not in "ifu":
        raise TypeError("values harus mempunyai dtype numerik")
    return scale * vector + shift


def add_column_offsets(table: np.ndarray, offsets: np.ndarray) -> np.ndarray:
    """Tambahkan satu offset per kolom dengan pemeriksaan bentuk eksplisit."""

    matrix = np.asarray(table)
    vector = np.asarray(offsets)
    if matrix.ndim != 2:
        raise ValueError("table harus berupa array dua dimensi")
    if vector.ndim != 1:
        raise ValueError("offsets harus berupa array satu dimensi")
    if matrix.shape[1] != vector.shape[0]:
        raise ValueError("jumlah offset harus sama dengan jumlah kolom")
    if matrix.dtype.kind not in "ifu" or vector.dtype.kind not in "ifu":
        raise TypeError("table dan offsets harus mempunyai dtype numerik")
    return matrix + vector


def copy_view_trace() -> dict[str, object]:
    """Tunjukkan efek perubahan melalui view dan melalui salinan terpisah."""

    base = np.arange(6, dtype=np.int64)
    window = base[1:4]
    detached = base[1:4].copy()

    window[0] = -10
    detached[1] = 99

    return {
        "base": base.tolist(),
        "view": window.tolist(),
        "copy": detached.tolist(),
        "view_shares_memory": bool(np.shares_memory(base, window)),
        "copy_shares_memory": bool(np.shares_memory(base, detached)),
    }


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasikan payload sebagai JSON UTF-8 kanonis proyek."""

    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def build_results() -> dict[str, object]:
    """Bangun rekaman eksperimen deterministik Unit 3."""

    values = make_vector([1, 2, 3, 4], dtype="int64")
    original = values.copy()
    transformed = affine_transform(values, scale=3, shift=-2)
    scalar_reference = np.array(
        [3 * int(value) - 2 for value in values],
        dtype=np.int64,
    )

    table = np.array([[10, 20, 30], [40, 50, 60]], dtype=np.int64)
    offsets = np.array([1, -2, 3], dtype=np.int64)
    adjusted = add_column_offsets(table, offsets)

    decimals = np.array([0.1, 0.2, 0.3], dtype=np.float64)
    decimal_sum = float(np.sum(decimals))

    vectorized_matches = bool(np.array_equal(transformed, scalar_reference))
    payload: dict[str, object] = {
        "schema": "o002.unit03-results.v1",
        "runtime": {"numpy": np.__version__},
        "vectorization": {
            "formula": "3*x-2",
            "input": values.tolist(),
            "input_dtype": str(values.dtype),
            "input_shape": list(values.shape),
            "result": transformed.tolist(),
            "result_shape": list(transformed.shape),
            "scalar_reference": scalar_reference.tolist(),
            "matches_scalar_reference": vectorized_matches,
            "input_unchanged": bool(np.array_equal(values, original)),
            "shape_preserved": transformed.shape == values.shape,
            "sum_invariant": bool(
                int(np.sum(transformed))
                == 3 * int(np.sum(values)) - 2 * values.size
            ),
        },
        "broadcasting": {
            "table_shape": list(table.shape),
            "offset_shape": list(offsets.shape),
            "result_shape": list(adjusted.shape),
            "result": adjusted.tolist(),
        },
        "copy_vs_view": copy_view_trace(),
        "floating_point": {
            "expression": "sum([0.1, 0.2, 0.3])",
            "result": repr(decimal_sum),
            "close_to_0.6": bool(
                np.isclose(decimal_sum, 0.6, rtol=1e-12, atol=1e-15)
            ),
            "is_exactly_0.6": decimal_sum == 0.6,
        },
        "proof_boundary": {
            "checked_case": values.tolist(),
            "vectorized_matches_scalar_reference": vectorized_matches,
            "proves_for_every_compatible_array": False,
            "reason": (
                "Pemeriksaan satu array menguji implementasi pada kasus itu; "
                "klaim umum memerlukan argumen per komponen."
            ),
        },
    }
    payload["payload_sha256"] = hashlib.sha256(
        canonical_json_bytes(payload)
    ).hexdigest()
    return payload


def write_result(result: dict[str, object], output: Path) -> None:
    """Tulis hasil dengan urutan kunci, inden, encoding, dan akhir baris tetap."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_result(build_results(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
