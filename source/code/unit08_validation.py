"""Pengujian dan validasi deterministik untuk Unit 8.

Kode asli proyek O002; hanya memakai pustaka standar Python. Implementasi
penjumlahan berulang divalidasi terhadap rumus pasangan yang diturunkan secara
terpisah.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from math import isclose, isfinite
from pathlib import Path
from typing import Any, Callable


REFERENCE_VALUES: tuple[tuple[int, int], ...] = (
    (0, 0),
    (1, 1),
    (2, 3),
    (10, 55),
    (100, 5050),
)


def require_nonnegative_integer(value: object, *, name: str) -> int:
    """Validasi bilangan bulat taknegatif; ``bool`` ditolak secara eksplisit."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} harus berupa bilangan bulat")
    if value < 0:
        raise ValueError(f"{name} harus taknegatif")
    return value


def triangular_iterative(n: int) -> int:
    """Hitung 1+...+n dengan penjumlahan berulang."""

    n = require_nonnegative_integer(n, name="n")
    total = 0
    for k in range(1, n + 1):
        previous = total
        total += k
        assert total >= previous  # invarian internal, bukan validasi masukan
    return total


def triangular_pairing_formula(n: int) -> int:
    """Hitung hasil referensi n(n+1)/2 dari argumen pasangan."""

    n = require_nonnegative_integer(n, name="n")
    return n * (n + 1) // 2


def sqrt2_newton(iterations: int = 5) -> float:
    """Dekati akar dua dengan sejumlah iterasi Newton yang dinyatakan."""

    iterations = require_nonnegative_integer(iterations, name="iterations")
    if iterations == 0:
        raise ValueError("iterations harus positif")
    estimate = 1.0
    for _ in range(iterations):
        estimate = 0.5 * (estimate + 2.0 / estimate)
    return estimate


def sqrt2_residual_check(
    *, iterations: int = 5, absolute_tolerance: float = 1e-12
) -> dict[str, object]:
    """Periksa pendekatan akar dua melalui residual kuadrat bertoleransi."""

    if not isinstance(absolute_tolerance, (int, float)) or isinstance(
        absolute_tolerance, bool
    ):
        raise TypeError("absolute_tolerance harus berupa bilangan real")
    tolerance = float(absolute_tolerance)
    if not isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("absolute_tolerance harus berhingga dan taknegatif")

    estimate = sqrt2_newton(iterations)
    residual = estimate * estimate - 2.0
    return {
        "iterations": iterations,
        "estimate": repr(estimate),
        "squared_residual": repr(residual),
        "relative_tolerance": "0.0",
        "absolute_tolerance": repr(tolerance),
        "passed": isclose(
            estimate * estimate,
            2.0,
            rel_tol=0.0,
            abs_tol=tolerance,
        ),
    }


def reference_value_checks() -> list[dict[str, object]]:
    """Bandingkan implementasi dengan tabel nilai yang dibekukan sebelumnya."""

    records: list[dict[str, object]] = []
    for n, expected in REFERENCE_VALUES:
        actual = triangular_iterative(n)
        records.append(
            {
                "n": n,
                "expected": expected,
                "actual": actual,
                "passed": actual == expected,
            }
        )
    return records


def property_violations(limit: int) -> dict[str, list[int]]:
    """Cari pelanggaran tiga sifat pada domain berhingga 0 <= n <= limit."""

    limit = require_nonnegative_integer(limit, name="limit")
    formula_mismatches: list[int] = []
    increment_violations: list[int] = []
    doubling_violations: list[int] = []

    for n in range(limit + 1):
        value = triangular_iterative(n)
        if value != triangular_pairing_formula(n):
            formula_mismatches.append(n)
        if triangular_iterative(n + 1) - value != n + 1:
            increment_violations.append(n)
        if triangular_iterative(2 * n) != 2 * value + n * n:
            doubling_violations.append(n)

    return {
        "pairing_formula": formula_mismatches,
        "increment_relation": increment_violations,
        "doubling_relation": doubling_violations,
    }


def rejects_exception(
    function: Callable[..., object], exception: type[Exception], *args: object
) -> bool:
    """Kembalikan benar hanya jika pemanggilan menolak dengan jenis yang tepat."""

    try:
        function(*args)
    except exception:
        return True
    except Exception:
        return False
    return False


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasikan JSON UTF-8 dengan kunci, inden, dan akhir baris tetap."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_validation_report(limit: int = 1000) -> dict[str, Any]:
    """Bangun laporan validasi terpadu tanpa waktu, jaringan, atau keacakan."""

    limit = require_nonnegative_integer(limit, name="limit")
    references = reference_value_checks()
    violations = property_violations(limit)
    approximate = sqrt2_residual_check()
    edge_checks = {
        "n_zero_returns_zero": triangular_iterative(0) == 0,
        "negative_n_rejected": rejects_exception(
            triangular_iterative, ValueError, -1
        ),
        "noninteger_n_rejected": rejects_exception(
            triangular_iterative, TypeError, 2.5
        ),
        "boolean_n_rejected": rejects_exception(
            triangular_iterative, TypeError, True
        ),
    }
    all_passed = (
        all(record["passed"] for record in references)
        and all(not items for items in violations.values())
        and bool(approximate["passed"])
        and all(edge_checks.values())
    )

    core: dict[str, Any] = {
        "schema": "o002.unit08.validation.v1",
        "parameters": {"finite_property_limit": limit},
        "unit_examples": references,
        "independent_oracle": {
            "implementation": "penjumlahan berulang 1+...+n",
            "reference": "rumus pasangan n(n+1)/2",
            "domain_checked": f"0 <= n <= {limit}",
            "mismatches": violations["pairing_formula"],
        },
        "metamorphic_properties": {
            "increment": {
                "relation": "T(n+1)-T(n)=n+1",
                "violations": violations["increment_relation"],
            },
            "doubling": {
                "relation": "T(2n)=2*T(n)+n^2",
                "violations": violations["doubling_relation"],
            },
        },
        "edge_and_domain_checks": edge_checks,
        "tolerant_numeric_assertion": approximate,
        "test_layers": {
            "unit": "fungsi tunggal diperiksa pada contoh, batas, dan sifat",
            "integration": "laporan menggabungkan oracle, sifat, dan serialisasi",
            "regression": "kasus n=0 dibekukan untuk mencegah galat batas berulang",
        },
        "coverage_limit": (
            "Tidak ditemukannya pelanggaran pada domain berhingga bukan bukti "
            "bahwa implementasi benar untuk setiap bilangan bulat taknegatif."
        ),
        "all_required_checks_passed": all_passed,
    }
    core_digest = hashlib.sha256(canonical_json_bytes(core)).hexdigest()
    return {**core, "core_sha256": core_digest}


def write_report(report: dict[str, Any], output: Path) -> None:
    """Tulis laporan validasi kanonis."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(report))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path("output/unit08-results.json"))
    args = parser.parse_args()
    report = build_validation_report(args.limit)
    write_report(report, args.output)
    return 0 if report["all_required_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
