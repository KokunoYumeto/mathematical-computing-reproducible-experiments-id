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
import sys
from typing import Any


SCHEMA = "o002.unit06.floating.v1"


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
            "float_format": "IEEE 754 binary64 pada build CPython yang diuji",
        },
        "binary64": binary64_profile(),
        "cancellation": cancellation_report(),
        "forward_backward_error": sqrt_forward_backward_report(),
        "conditioning": conditioning_report(),
        "summation": summation_report(),
        "error_budget": error_budget_report(),
        "proof_boundary": {
            "experiments_executed": [
                "binary64_spacing_and_range",
                "cancellation",
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
