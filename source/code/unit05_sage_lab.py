"""Lab SageMath lokal wajib untuk Unit 5 O002.

Kode asli proyek O002; lihat LICENSE-CODE.md. Jalankan modul ini dengan
SageMath 9.5 melalui ``/usr/bin/sage -python``. Modul tidak memakai jaringan
dan hanya menulis jalur keluaran yang diberikan secara eksplisit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from sage.all import PolynomialRing, QQ, RR, SR, ZZ, solve
from sage.env import SAGE_VERSION


EXPECTED_SAGE_VERSION = "9.5"
SCHEMA = "o002.unit05.sage-lab.v1"


def require_frozen_runtime() -> None:
    """Tolak runtime selain versi SageMath yang dibekukan untuk lab ini."""

    if SAGE_VERSION != EXPECTED_SAGE_VERSION:
        raise RuntimeError(
            f"lab memerlukan SageMath {EXPECTED_SAGE_VERSION}; ditemukan {SAGE_VERSION}"
        )


def parent_and_coercion_record() -> dict[str, Any]:
    """Catat parent empat domain dan peta coercion yang dipakai lab."""

    integer = ZZ(6)
    rational = QQ(1) / 3
    real = RR(rational)
    symbolic = SR(rational)
    mixed = integer + rational
    return {
        "objects": {
            "integer": {"value": str(integer), "parent": str(integer.parent())},
            "rational": {
                "value": str(rational),
                "parent": str(rational.parent()),
            },
            "real": {
                "value": str(real),
                "parent": str(real.parent()),
                "precision_bits": int(real.parent().precision()),
            },
            "symbolic": {
                "value": str(symbolic),
                "parent": str(symbolic.parent()),
            },
        },
        "coercion_maps": {
            "ZZ_to_QQ": bool(QQ.has_coerce_map_from(ZZ)),
            "QQ_to_RR": bool(RR.has_coerce_map_from(QQ)),
            "QQ_to_SR": bool(SR.has_coerce_map_from(QQ)),
        },
        "mixed_ZZ_plus_QQ": {
            "value": str(mixed),
            "parent": str(mixed.parent()),
        },
    }


def polynomial_record() -> dict[str, Any]:
    """Bangun gelang polinom atas QQ dan faktorkan x^4-1 secara eksak."""

    ring = PolynomialRing(QQ, "x")
    x = ring.gen()
    polynomial = x**4 - 1
    factorization = polynomial.factor()
    factors = [
        {"factor": str(factor), "multiplicity": int(multiplicity)}
        for factor, multiplicity in factorization
    ]
    return {
        "base_ring": str(ring.base_ring()),
        "parent": str(ring),
        "generator": str(x),
        "polynomial": str(polynomial),
        "factorization": str(factorization),
        "factors": factors,
        "expands_back": bool(factorization.prod() == polynomial),
    }


def solve_record() -> dict[str, Any]:
    """Selesaikan y^2=2 dalam SR dan periksa residual simbolik eksak."""

    y = SR.var("y")
    raw_solutions = solve(y**2 == 2, y, solution_dict=True)
    values = sorted((solution[y] for solution in raw_solutions), key=str)
    return {
        "parent": str(y.parent()),
        "equation": "y^2 == 2",
        "solutions": [str(value) for value in values],
        "zero_residuals": [bool((value**2 - 2).simplify_full() == 0) for value in values],
    }


def approximation_record() -> dict[str, Any]:
    """Konversi eksplisit nilai eksak ke RR dan pertahankan kedua objek."""

    exact = QQ(1) / 3
    approximate = RR(exact)
    difference = approximate - RR(exact)
    return {
        "exact": {"value": str(exact), "parent": str(exact.parent())},
        "conversion": "RR(QQ(1)/3)",
        "approximate": {
            "value": str(approximate),
            "parent": str(approximate.parent()),
            "precision_bits": int(approximate.parent().precision()),
        },
        "repeat_conversion_difference": str(difference),
        "conversion_is_explicit": True,
    }


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasi JSON UTF-8 dengan kunci terurut dan akhir baris LF."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_results() -> dict[str, Any]:
    """Bangun rekaman lengkap lab Sage yang deterministik."""

    require_frozen_runtime()
    core: dict[str, Any] = {
        "schema": SCHEMA,
        "runtime": {
            "sage": SAGE_VERSION,
            "required_sage": EXPECTED_SAGE_VERSION,
            "invocation": "/usr/bin/sage -python",
            "local_execution_required": True,
            "remote_service_satisfies_requirement": False,
        },
        "parents_and_coercion": parent_and_coercion_record(),
        "polynomial_ring": polynomial_record(),
        "symbolic_solving": solve_record(),
        "explicit_approximation": approximation_record(),
        "proof_boundary": (
            "Parent, coercion, factorization, solusi, dan residual diperiksa pada "
            "objek ini. Keluaran Sage tidak menggantikan pembuktian klaim umum."
        ),
    }
    digest = hashlib.sha256(canonical_json_bytes(core)).hexdigest()
    return {**core, "core_sha256": digest}


def write_results(output: Path) -> None:
    """Tulis rekaman lab pada jalur relatif atau absolut yang diberikan."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(build_results()))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    write_results(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
