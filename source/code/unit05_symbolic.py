"""Komputasi eksak dan simbolik yang dapat diperiksa untuk Unit 5.

Kode asli proyek O002. SageMath hanya muncul sebagai jembatan opsional berupa
teks sumber; jalur dasar modul ini memerlukan Python, pustaka standar, dan
SymPy.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Any

import sympy as sp


def exact_fraction_sum() -> Fraction:
    """Kembalikan 1/10 + 2/10 sebagai bilangan rasional eksak."""

    return Fraction(1, 10) + Fraction(2, 10)


def expression_and_value(
    value: int | Fraction = 3,
) -> tuple[sp.Symbol, sp.Expr, sp.Expr]:
    """Bentuk ekspresi x^2-1 lalu evaluasi secara eksak pada ``value``."""

    x = sp.Symbol("x")
    expression = x**2 - 1
    if isinstance(value, Fraction):
        exact_value: sp.Expr = sp.Rational(value.numerator, value.denominator)
    else:
        exact_value = sp.Integer(value)
    evaluated = sp.simplify(expression.subs(x, exact_value))
    return x, expression, evaluated


def polynomial_identity_holds(left: sp.Expr, right: sp.Expr) -> bool:
    """Periksa identitas polinomial dengan mengekspansi selisihnya."""

    return sp.expand(left - right) == 0


def equivalence_example() -> tuple[sp.Symbol, sp.Expr, sp.Expr]:
    """Kembalikan dua ekspresi berbeda dengan polinom yang sama."""

    x = sp.Symbol("x")
    return x, (x + 1) ** 2, x**2 + 2 * x + 1


def domain_sensitive_cancellation() -> tuple[sp.Symbol, sp.Expr, sp.Expr, tuple[sp.Expr, ...]]:
    """Sederhanakan pecahan sambil mempertahankan titik terlarang asal."""

    x = sp.Symbol("x")
    original = sp.Mul(x**2 - 1, sp.Pow(x - 1, -1), evaluate=False)
    simplified = sp.cancel(original)
    excluded = tuple(sp.solve(sp.denom(original), x))
    return x, original, simplified, excluded


def square_root_under_assumptions() -> tuple[sp.Expr, sp.Expr]:
    """Bandingkan sqrt(x^2) untuk x real dan x positif."""

    x_real = sp.Symbol("x", real=True)
    x_positive = sp.Symbol("x", positive=True)
    real_result = sp.simplify(sp.sqrt(x_real**2))
    positive_result = sp.simplify(sp.sqrt(x_positive**2))
    return real_result, positive_result


def exact_factorization() -> tuple[sp.Symbol, sp.Expr, sp.Expr]:
    """Faktorkan x^4-1 secara eksak atas bilangan bulat."""

    x = sp.Symbol("x")
    polynomial = x**4 - 1
    return x, polynomial, sp.factor(polynomial)


def exact_real_solutions() -> tuple[sp.Expr, ...]:
    """Kembalikan akar real eksak x^2=2 dalam urutan teks kanonis lokal."""

    x = sp.Symbol("x", real=True)
    solution_set = sp.solveset(sp.Eq(x**2, 2), x, domain=sp.S.Reals)
    if not isinstance(solution_set, sp.FiniteSet):
        raise RuntimeError("himpunan solusi yang diharapkan harus berhingga")
    return tuple(sorted(solution_set, key=sp.sstr))


def canonical_expression(expression: sp.Expr) -> str:
    """Serialisasikan pohon ekspresi SymPy, bukan tampilan pretty-print."""

    return sp.srepr(expression)


def sage_bridge_source() -> str:
    """Kembalikan jembatan kecil yang dapat dijalankan oleh Python SageMath."""

    return (
        "from sage.all import PolynomialRing, QQ, SR, solve\n"
        "R = PolynomialRing(QQ, 'x')\n"
        "x = R.gen()\n"
        "print((x**4 - 1).factor())\n"
        "y = SR.var('y')\n"
        "print(solve(y**2 == 2, y))\n"
    )


def canonical_json_bytes(payload: object) -> bytes:
    """Kembalikan JSON UTF-8 dengan urutan medan, inden, dan LF tetap."""

    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    return text.encode("utf-8")


def build_results() -> dict[str, Any]:
    """Bangun rekaman deterministik bagi semua contoh utama Unit 5."""

    _, expression, value = expression_and_value()
    _, left, right = equivalence_example()
    _, original, cancelled, excluded = domain_sensitive_cancellation()
    real_sqrt, positive_sqrt = square_root_under_assumptions()
    _, polynomial, factored = exact_factorization()
    solutions = exact_real_solutions()

    core: dict[str, Any] = {
        "schema": "o002.unit05.symbolic.v1",
        "runtime": {"sympy": sp.__version__},
        "exact_fraction": {
            "expression": "1/10 + 2/10",
            "result": str(exact_fraction_sum()),
        },
        "expression_and_value": {
            "expression": canonical_expression(expression),
            "substitution": {"x": "3"},
            "value": sp.sstr(value),
        },
        "polynomial_equivalence": {
            "left": canonical_expression(left),
            "right": canonical_expression(right),
            "structurally_equal": left == right,
            "expanded_difference_is_zero": polynomial_identity_holds(left, right),
        },
        "domain_sensitive_cancellation": {
            "original": canonical_expression(original),
            "cancelled": canonical_expression(cancelled),
            "excluded_from_original_domain": [sp.sstr(item) for item in excluded],
            "same_values_on_common_domain": sp.simplify(original - cancelled) == 0,
            "same_function_with_original_domains": not bool(excluded),
        },
        "assumptions": {
            "sqrt_x_squared_for_real_x": canonical_expression(real_sqrt),
            "sqrt_x_squared_for_positive_x": canonical_expression(positive_sqrt),
        },
        "factorization": {
            "polynomial": canonical_expression(polynomial),
            "factored": canonical_expression(factored),
            "expands_back": sp.expand(factored - polynomial) == 0,
        },
        "exact_real_solutions": {
            "equation": "x**2 = 2",
            "solutions": [sp.sstr(item) for item in solutions],
            "zero_residuals": [sp.simplify(item**2 - 2) == 0 for item in solutions],
        },
        "sage_bridge": {
            "required_for_baseline": False,
            "source": sage_bridge_source(),
        },
    }
    digest = hashlib.sha256(canonical_json_bytes(core)).hexdigest()
    return {**core, "core_sha256": digest}


def write_results(payload: dict[str, Any], output: Path) -> None:
    """Tulis satu rekaman hasil kanonis."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(payload))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_results(build_results(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
