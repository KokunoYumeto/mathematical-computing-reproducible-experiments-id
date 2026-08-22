"""Eksperimen deterministik untuk Unit 1.

Kode asli proyek O002; lihat LICENSE-CODE.md.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import json
from math import isclose
from pathlib import Path
import platform
import sys
from typing import Any


def exact_sum() -> Fraction:
    """Kembalikan 1/10 + 2/10 secara eksak."""

    return Fraction(1, 10) + Fraction(2, 10)


def floating_sum() -> float:
    """Kembalikan penjumlahan titik-mengambang 0.1 + 0.2."""

    return 0.1 + 0.2


def close_to_three_tenths(value: float) -> bool:
    """Periksa kedekatan memakai toleransi yang dinyatakan."""

    return isclose(value, 0.3, rel_tol=1e-12, abs_tol=1e-15)


def even_expression_holds(n: int) -> bool:
    """Periksa apakah n^2+n genap untuk satu bilangan bulat."""

    return (n * n + n) % 2 == 0


def first_euler_counterexample() -> dict[str, int]:
    """Kembalikan contoh penyangkal pertama bagi n^2+n+41 selalu prima."""

    n = 40
    value = n * n + n + 41
    return {"n": n, "value": value, "factor": 41}


def run_experiment(limit: int) -> dict[str, Any]:
    """Jalankan eksperimen dan kembalikan rekaman terurut yang serializable."""

    if limit <= 0:
        raise ValueError("limit harus berupa bilangan bulat positif")

    exact = exact_sum()
    floating = floating_sum()
    violations = [n for n in range(limit) if not even_expression_holds(n)]

    return {
        "schema": "o002.unit01.experiment.v1",
        "runtime": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
        },
        "parameters": {"limit": limit},
        "exact_arithmetic": {
            "expression": "1/10 + 2/10",
            "result": f"{exact.numerator}/{exact.denominator}",
        },
        "floating_arithmetic": {
            "expression": "0.1 + 0.2",
            "result": repr(floating),
            "difference_from_0.3": repr(floating - 0.3),
            "isclose": close_to_three_tenths(floating),
            "relative_tolerance": 1e-12,
            "absolute_tolerance": 1e-15,
        },
        "finite_check": {
            "claim": "n^2+n genap",
            "domain_checked": f"0 <= n < {limit}",
            "violations": violations,
            "proves_universal_claim": False,
        },
        "counterexample": {
            "claim": "n^2+n+41 prima untuk setiap n bulat taknegatif",
            **first_euler_counterexample(),
        },
    }


def write_result(result: dict[str, Any], output: Path) -> None:
    """Tulis JSON UTF-8 deterministik dengan satu baris akhir."""

    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    output.write_text(payload, encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--output", type=Path, default=Path("output/unit01-results.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_result(run_experiment(args.limit), args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
