"""Eksperimen titik-mengambang deterministik untuk Unit 6.

Kode asli proyek O002; lihat LICENSE-CODE.md.
"""

from __future__ import annotations

import argparse
from decimal import Decimal, localcontext
import hashlib
import json
import math
from pathlib import Path
import platform
import scipy
from scipy import special
import sys
from typing import Any


SCHEMA = "o002.unit06.floating.v2"
SCIPY_EXPREL_LAB_MIN_ABS = math.ulp(0.0)
SCIPY_EXPREL_LAB_MAX_ABS = 1e-4
SCIPY_EXPREL_DECIMAL_MIN_PRECISION = 80
SCIPY_EXPREL_DECIMAL_GUARD_DIGITS = 50


def decimal_text(value: Decimal) -> str:
    """Format Decimal dengan 20 angka di belakang koma dalam notasi ilmiah."""

    return format(value, ".20E")


def binary64_profile() -> dict[str, object]:
    """Kembalikan jarak representabel dan batas rentang binary64 Python."""

    epsilon = sys.float_info.epsilon
    next_one = math.nextafter(1.0, math.inf)
    large = float(2**53)
    smallest_subnormal = math.ulp(0.0)
    overflowed = sys.float_info.max * 2.0

    return {
        "epsilon": repr(epsilon),
        "epsilon_hex": epsilon.hex(),
        "unit_roundoff_for_round_to_nearest": repr(epsilon / 2.0),
        "one_hex": (1.0).hex(),
        "next_after_one_hex": next_one.hex(),
        "gap_after_one": repr(next_one - 1.0),
        "ulp_at_one": repr(math.ulp(1.0)),
        "ulp_at_two_to_53": repr(math.ulp(large)),
        "two_to_53_plus_one_is_unchanged": large + 1.0 == large,
        "largest_finite": repr(sys.float_info.max),
        "overflow_result": "inf" if math.isinf(overflowed) else repr(overflowed),
        "smallest_positive_normal": repr(sys.float_info.min),
        "smallest_positive_subnormal": repr(smallest_subnormal),
        "half_smallest_subnormal_is_zero": smallest_subnormal / 2.0 == 0.0,
    }


def cancellation_report(x_integer: int = 10**16) -> dict[str, object]:
    """Bandingkan pengurangan langsung dengan bentuk yang dirasionalkan."""

    if x_integer <= 0:
        raise ValueError("x_integer harus positif")

    x = float(x_integer)
    direct = math.sqrt(x + 1.0) - math.sqrt(x)
    stable = 1.0 / (math.sqrt(x + 1.0) + math.sqrt(x))

    with localcontext() as context:
        context.prec = 80
        exact_x = Decimal(x_integer)
        reference = (exact_x + 1).sqrt() - exact_x.sqrt()
        direct_error = abs(Decimal.from_float(direct) - reference)
        stable_error = abs(Decimal.from_float(stable) - reference)
        direct_relative = direct_error / abs(reference)
        stable_relative = stable_error / abs(reference)

    return {
        "x": str(x_integer),
        "x_plus_one_rounds_to_x": x + 1.0 == x,
        "direct": repr(direct),
        "rationalized": repr(stable),
        "high_precision_reference": decimal_text(reference),
        "direct_relative_forward_error": decimal_text(direct_relative),
        "rationalized_relative_forward_error": decimal_text(stable_relative),
        "rationalized_is_more_accurate": stable_error < direct_error,
    }


def naive_exprel(x: float) -> float:
    """Hitung (exp(x)-1)/x secara langsung, termasuk ekstensi di nol."""

    if not math.isfinite(x):
        raise ValueError("x harus berhingga")
    if x == 0.0:
        return 1.0
    return (math.exp(x) - 1.0) / x


def _decimal_exprel_reference(x: Decimal) -> Decimal:
    """Hitung exprel dengan deret pangkat tanpa pembatalan pengurangan."""

    if x == 0:
        return Decimal(1)

    total = Decimal(1)
    term = Decimal(1)
    for order in range(1, 10_000):
        term = term * x / Decimal(order + 1)
        updated = total + term
        if updated == total:
            return total
        total = updated
    raise ArithmeticError("deret exprel tidak konvergen pada batas iterasi")


def _decimal_exprel_derivative(x: Decimal) -> Decimal:
    """Hitung turunan exprel dengan deret yang bebas pembatalan."""

    if x == 0:
        return Decimal(1) / 2

    total = Decimal(0)
    power = Decimal(1)
    factorial = Decimal(2)
    for order in range(1, 10_000):
        term = Decimal(order) * power / factorial
        updated = total + term
        if updated == total:
            return total
        total = updated
        power *= x
        factorial *= Decimal(order + 2)
    raise ArithmeticError("deret turunan exprel tidak konvergen pada batas iterasi")


def _decimal_exprel_precision(x: Decimal) -> int:
    """Pertahankan koreksi O(x) bahkan bagi masukan binary64 terkecil."""

    return max(
        SCIPY_EXPREL_DECIMAL_MIN_PRECISION,
        -x.copy_abs().adjusted() + SCIPY_EXPREL_DECIMAL_GUARD_DIGITS,
    )


def scipy_exprel_report(x: float = 1e-8) -> dict[str, object]:
    """Bandingkan scipy.special.exprel dengan evaluasi naif dekat nol.

    Laporan rinci dibatasi ke 0 < |x| <= 1e-4. Oracle menaikkan presisi
    menurut eksponen x dan memakai deret yang bebas pembatalan, sehingga
    masukan subnormal binary64 terkecil pun masih mempunyai referensi terurai.
    Batas atas menjaga aproksimasi galat mundur lokal sesuai tujuan lab.
    """

    if not math.isfinite(x):
        raise ValueError("x harus berhingga")
    magnitude = abs(x)
    if not SCIPY_EXPREL_LAB_MIN_ABS <= magnitude <= SCIPY_EXPREL_LAB_MAX_ABS:
        raise ValueError(
            "domain lab harus memenuhi 0 < |x| <= 1e-4 untuk nilai binary64"
        )

    naive = naive_exprel(x)
    stable = float(special.exprel(x))
    exact_x = Decimal.from_float(x)
    decimal_precision = _decimal_exprel_precision(exact_x)
    with localcontext() as context:
        context.prec = decimal_precision
        reference = _decimal_exprel_reference(exact_x)
        derivative = _decimal_exprel_derivative(exact_x)
        condition_number = abs(exact_x * derivative / reference)

        naive_forward = abs(Decimal.from_float(naive) - reference)
        stable_forward = abs(Decimal.from_float(stable) - reference)
        naive_backward_absolute = naive_forward / abs(derivative)
        stable_backward_absolute = stable_forward / abs(derivative)
        naive_backward_relative = naive_backward_absolute / abs(exact_x)
        stable_backward_relative = stable_backward_absolute / abs(exact_x)

    extreme_x = 1e-16
    extreme_naive = naive_exprel(extreme_x)
    extreme_stable = float(special.exprel(extreme_x))
    return {
        "function": "E(x)=(exp(x)-1)/x, dengan ekstensi kontinu E(0)=1",
        "mathematical_domain": "semua x real",
        "laboratory_domain": "0 < |x| <= 1e-4 untuk masukan binary64",
        "decimal_oracle": {
            "method": "deret pangkat bebas pembatalan untuk E dan E'",
            "precision_digits": decimal_precision,
            "minimum_precision_digits": SCIPY_EXPREL_DECIMAL_MIN_PRECISION,
            "guard_digits_beyond_x": SCIPY_EXPREL_DECIMAL_GUARD_DIGITS,
            "lower_absolute_bound": repr(SCIPY_EXPREL_LAB_MIN_ABS),
            "upper_absolute_bound": repr(SCIPY_EXPREL_LAB_MAX_ABS),
            "scope": (
                "Presisi bertambah bersama kecilnya x agar koreksi berorde x "
                "tetap terurai sampai masukan subnormal binary64 terkecil."
            ),
        },
        "tested_x": repr(x),
        "scipy": {
            "function": "scipy.special.exprel",
            "version": scipy.__version__,
        },
        "values": {
            "naive": repr(naive),
            "scipy_special_exprel": repr(stable),
            "high_precision_reference": decimal_text(reference),
        },
        "conditioning": {
            "relative_condition_number": decimal_text(condition_number),
            "formula": "abs(x*E'(x)/E(x))",
            "classification": "berkondisi baik dekat nol",
            "reason": "nilai kondisi mendekati |x|/2 ketika x mendekati nol",
        },
        "forward_error": {
            "naive_absolute": decimal_text(naive_forward),
            "naive_relative": decimal_text(naive_forward / abs(reference)),
            "scipy_absolute": decimal_text(stable_forward),
            "scipy_relative": decimal_text(stable_forward / abs(reference)),
            "scipy_is_more_accurate": stable_forward < naive_forward,
        },
        "backward_error": {
            "method": "aproksimasi orde pertama abs(delta_x) ~= abs(delta_y)/abs(E'(x))",
            "naive_absolute_estimate": decimal_text(naive_backward_absolute),
            "naive_relative_estimate": decimal_text(naive_backward_relative),
            "scipy_absolute_estimate": decimal_text(stable_backward_absolute),
            "scipy_relative_estimate": decimal_text(stable_backward_relative),
            "is_exact_inverse_solution": False,
        },
        "extreme_cancellation": {
            "x": repr(extreme_x),
            "naive": repr(extreme_naive),
            "scipy_special_exprel": repr(extreme_stable),
            "math_exp_x_equals_one": math.exp(extreme_x) == 1.0,
        },
        "evidence_boundary": {
            "executed_case_only": True,
            "proves_stability_for_all_real_inputs": False,
            "claim": (
                "Pelaksanaan ini menunjukkan pembatalan dan perbaikan pada nilai yang "
                "dicatat; klaim umum memerlukan analisis algoritme dan model pembulatan."
            ),
        },
    }


def sqrt_forward_backward_report(value: int = 2) -> dict[str, object]:
    """Ukur galat maju dan galat mundur relatif bagi akar kuadrat."""

    if value <= 0:
        raise ValueError("value harus positif")

    computed = math.sqrt(float(value))
    with localcontext() as context:
        context.prec = 80
        exact_value = Decimal(value)
        reference = exact_value.sqrt()
        computed_decimal = Decimal.from_float(computed)
        relative_forward = abs(computed_decimal - reference) / reference
        relative_backward = abs(
            computed_decimal * computed_decimal - exact_value
        ) / exact_value

    return {
        "problem": f"sqrt({value})",
        "computed": repr(computed),
        "computed_hex": computed.hex(),
        "high_precision_reference": decimal_text(reference),
        "relative_forward_error": decimal_text(relative_forward),
        "relative_backward_error": decimal_text(relative_backward),
        "backward_interpretation": (
            "Perubahan relatif pada masukan agar kuadrat hasil menjadi masukan tepat."
        ),
    }


def reciprocal_gap(x: float) -> float:
    """Hitung 1/(1-x), dengan titik singular ditolak secara eksplisit."""

    if not math.isfinite(x):
        raise ValueError("x harus berhingga")
    if x == 1.0:
        raise ValueError("x tidak boleh sama dengan 1")
    return 1.0 / (1.0 - x)


def conditioning_report(
    x: float = 0.99999999,
    perturbation: float = 1e-12,
) -> dict[str, object]:
    """Ukur penguatan gangguan masukan untuk f(x)=1/(1-x)."""

    if not math.isfinite(perturbation) or perturbation == 0.0:
        raise ValueError("perturbation harus berhingga dan tidak nol")
    perturbed = x + perturbation
    original_output = reciprocal_gap(x)
    perturbed_output = reciprocal_gap(perturbed)
    actual_change = perturbed - x
    relative_input_change = abs(actual_change) / abs(x)
    relative_output_change = abs(perturbed_output - original_output) / abs(
        original_output
    )
    amplification = relative_output_change / relative_input_change
    local_condition_estimate = abs(x / (1.0 - x))

    return {
        "function": "1/(1-x)",
        "x": repr(x),
        "requested_perturbation": repr(perturbation),
        "actual_perturbation": repr(actual_change),
        "output": repr(original_output),
        "perturbed_output": repr(perturbed_output),
        "relative_input_change": repr(relative_input_change),
        "relative_output_change": repr(relative_output_change),
        "observed_amplification": repr(amplification),
        "local_condition_estimate": repr(local_condition_estimate),
        "ill_conditioning_is_a_problem_property": True,
    }


def naive_sum(values: list[float]) -> float:
    """Jumlahkan dari kiri ke kanan tanpa kompensasi tambahan."""

    total = 0.0
    for value in values:
        total += value
    return total


def summation_report() -> dict[str, object]:
    """Bandingkan algoritme naif, sum bawaan, dan math.fsum."""

    values = [1e16, 1.0, -1e16]
    reordered = [1e16, -1e16, 1.0]
    return {
        "values": [repr(value) for value in values],
        "mathematical_sum": "1",
        "naive_left_to_right": repr(naive_sum(values)),
        "reordered_naive_sum": repr(naive_sum(reordered)),
        "builtin_sum_for_recorded_runtime": repr(sum(values)),
        "math_fsum": repr(math.fsum(values)),
        "naive_is_order_sensitive": naive_sum(values) != naive_sum(reordered),
        "fsum_matches_mathematical_sum": math.fsum(values) == 1.0,
    }


def within_error_budget(
    computed: float,
    reference: float,
    *,
    absolute_budget: float,
    relative_budget: float,
) -> bool:
    """Periksa |computed-reference| <= A + R*|reference|."""

    values = (computed, reference, absolute_budget, relative_budget)
    if not all(math.isfinite(item) for item in values):
        raise ValueError("semua nilai anggaran harus berhingga")
    if absolute_budget < 0.0 or relative_budget < 0.0:
        raise ValueError("anggaran galat tidak boleh negatif")
    error = abs(computed - reference)
    allowance = absolute_budget + relative_budget * abs(reference)
    return error <= allowance


def error_budget_report() -> dict[str, object]:
    """Kembalikan satu keputusan toleransi yang parameternya dinyatakan."""

    computed = 1.0000000004
    reference = 1.0
    absolute_budget = 1e-10
    relative_budget = 5e-10
    error = abs(computed - reference)
    allowance = absolute_budget + relative_budget * abs(reference)
    return {
        "rule": "absolute_error <= absolute_budget + relative_budget*abs(reference)",
        "computed": repr(computed),
        "reference": repr(reference),
        "absolute_budget": repr(absolute_budget),
        "relative_budget": repr(relative_budget),
        "observed_absolute_error": repr(error),
        "allowed_absolute_error": repr(allowance),
        "passes": within_error_budget(
            computed,
            reference,
            absolute_budget=absolute_budget,
            relative_budget=relative_budget,
        ),
        "policy": "Anggaran ditetapkan dari kebutuhan masalah sebelum hasil dilihat.",
    }


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasikan JSON UTF-8 dengan urutan kunci, inden, dan LF tetap."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_results() -> dict[str, Any]:
    """Bangun rekaman lengkap dan deterministik bagi contoh Unit 6."""

    core: dict[str, Any] = {
        "schema": SCHEMA,
        "runtime": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
            "scipy": scipy.__version__,
            "float_format": "IEEE 754 binary64 pada build CPython yang diuji",
        },
        "binary64": binary64_profile(),
        "cancellation": cancellation_report(),
        "scipy_special_exprel": scipy_exprel_report(),
        "forward_backward_error": sqrt_forward_backward_report(),
        "conditioning": conditioning_report(),
        "summation": summation_report(),
        "error_budget": error_budget_report(),
        "proof_boundary": {
            "experiments_executed": [
                "binary64_spacing_and_range",
                "cancellation",
                "scipy_special_exprel",
                "sqrt_forward_backward_error",
                "conditioning",
                "summation",
                "error_budget",
            ],
            "proves_every_binary64_operation_correct": False,
            "claim": (
                "Hasil merekam perilaku kasus tertentu pada lingkungan tercatat; "
                "batas umum memerlukan model pembulatan dan analisis matematika."
            ),
        },
    }
    digest = hashlib.sha256(canonical_json_bytes(core)).hexdigest()
    return {**core, "core_sha256": digest}


def write_results(payload: dict[str, Any], output: Path) -> None:
    """Tulis satu berkas hasil kanonis."""

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
