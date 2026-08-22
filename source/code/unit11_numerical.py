from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from fractions import Fraction
import json
import math
from pathlib import Path
from typing import Callable, Iterable


@dataclass(frozen=True)
class BisectionResult:
    left: float
    right: float
    midpoint: float
    width: float
    iterations: int


def square_minus_two(value: float) -> float:
    """Kembalikan nilai fungsi acuan ``x*x - 2``."""

    return value * value - 2.0


def square(value: float) -> float:
    """Kembalikan kuadrat nilai untuk contoh kuadratur."""

    return value * value


def identity_derivative(_time: float, state: float) -> float:
    """Kembalikan turunan ``y' = y`` untuk contoh Euler."""

    return state


def finite_function_value(
    function: Callable[[float], float],
    point: float,
    *,
    label: str,
) -> float:
    """Evaluasi fungsi dan tolak hasil yang bukan bilangan real berhingga."""

    try:
        value = float(function(point))
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"nilai fungsi pada {label} harus berupa bilangan real berhingga") from error
    if not math.isfinite(value):
        raise ValueError(f"nilai fungsi pada {label} harus berhingga")
    return value


def bisection(
    function: Callable[[float], float],
    left: float,
    right: float,
    *,
    width_tolerance: float,
    max_iterations: int = 10_000,
) -> BisectionResult:
    if not all(math.isfinite(value) for value in (left, right, width_tolerance)):
        raise ValueError("ujung selang dan width_tolerance harus berhingga")
    if not left < right:
        raise ValueError("left harus lebih kecil daripada right")
    if not width_tolerance > 0:
        raise ValueError("width_tolerance harus positif")
    f_left = finite_function_value(function, left, label="ujung kiri")
    f_right = finite_function_value(function, right, label="ujung kanan")
    if f_left == 0:
        return BisectionResult(left, left, left, 0.0, 0)
    if f_right == 0:
        return BisectionResult(right, right, right, 0.0, 0)
    if (f_left < 0) == (f_right < 0):
        raise ValueError("ujung selang harus mempunyai tanda berbeda")

    iterations = 0
    width = right - left
    if not math.isfinite(width):
        raise ValueError("lebar selang harus berhingga")
    while width > width_tolerance:
        if iterations >= max_iterations:
            raise RuntimeError("batas iterasi tercapai")
        midpoint = left + width / 2
        if not math.isfinite(midpoint):
            raise ValueError("titik tengah harus berhingga")
        f_midpoint = finite_function_value(function, midpoint, label="titik tengah")
        if f_midpoint == 0:
            return BisectionResult(midpoint, midpoint, midpoint, 0.0, iterations + 1)
        if (f_left < 0) != (f_midpoint < 0):
            right = midpoint
            f_right = f_midpoint
        else:
            left = midpoint
            f_left = f_midpoint
        iterations += 1
        width = right - left
    midpoint = left + width / 2
    if not math.isfinite(midpoint):
        raise ValueError("titik tengah harus berhingga")
    return BisectionResult(left, right, midpoint, width, iterations)


def trapezoid(function: Callable[[float], float], left: float, right: float, intervals: int) -> float:
    if intervals <= 0:
        raise ValueError("intervals harus positif")
    width = (right - left) / intervals
    interior = sum(function(left + index * width) for index in range(1, intervals))
    return width * ((function(left) + function(right)) / 2 + interior)


def solve_2x2_exact(
    matrix: tuple[tuple[int, int], tuple[int, int]],
    vector: tuple[int, int],
) -> tuple[Fraction, Fraction]:
    (a, b), (c, d) = matrix
    e, f = vector
    determinant = a * d - b * c
    if determinant == 0:
        raise ValueError("matriks singular")
    return Fraction(e * d - b * f, determinant), Fraction(a * f - e * c, determinant)


def residual(
    matrix: tuple[tuple[float, float], tuple[float, float]],
    vector: tuple[float, float],
    solution: tuple[float, float],
) -> tuple[float, float]:
    return tuple(
        vector[row] - sum(matrix[row][column] * solution[column] for column in range(2))
        for row in range(2)
    )  # type: ignore[return-value]


def euler(
    derivative: Callable[[float, float], float],
    initial_time: float,
    initial_value: float,
    step: float,
    steps: int,
) -> float:
    if step <= 0 or steps < 0:
        raise ValueError("step harus positif dan steps tidak boleh negatif")
    time = initial_time
    value = initial_value
    for _ in range(steps):
        value += step * derivative(time, value)
        time += step
    return value


def canonical_json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_results() -> dict[str, object]:
    bisection_left = 1.0
    bisection_right = 2.0
    bisection_tolerance = 1e-12
    bisection_max_iterations = 10_000
    root = bisection(
        square_minus_two,
        bisection_left,
        bisection_right,
        width_tolerance=bisection_tolerance,
        max_iterations=bisection_max_iterations,
    )

    quadrature_left = 0.0
    quadrature_right = 1.0
    quadrature_grid = (4, 8, 16, 32)
    quadrature_reference = Fraction(1, 3)
    quadrature = []
    for intervals in quadrature_grid:
        value = trapezoid(
            square,
            quadrature_left,
            quadrature_right,
            intervals,
        )
        quadrature.append(
            {
                "intervals": intervals,
                "value": value,
                "absolute_error": abs(value - float(quadrature_reference)),
            }
        )

    matrix = ((2, 1), (1, -1))
    vector = (7, 1)
    exact_solution = solve_2x2_exact(matrix, vector)
    float_solution = tuple(float(value) for value in exact_solution)
    system_residual = residual(matrix, vector, float_solution)  # type: ignore[arg-type]

    euler_initial_time = 0.0
    euler_initial_value = 1.0
    euler_target_time = 1.0
    euler_steps_grid = (10, 20, 40)
    euler_reference = math.exp(euler_target_time)
    euler_rows = []
    for steps in euler_steps_grid:
        step = (euler_target_time - euler_initial_time) / steps
        value = euler(
            identity_derivative,
            euler_initial_time,
            euler_initial_value,
            step,
            steps,
        )
        euler_rows.append(
            {
                "steps": steps,
                "step": step,
                "value": value,
                "absolute_error": abs(value - euler_reference),
            }
        )

    return {
        "schema": "o002.unit11-results.v1",
        "bisection": {
            **asdict(root),
            "function": {
                "id": "square_minus_two",
                "expression": "x*x - 2.0",
            },
            "initial_interval": [bisection_left, bisection_right],
            "width_tolerance": bisection_tolerance,
            "max_iterations": bisection_max_iterations,
            "reference_root": {
                "kind": "akar positif eksak",
                "expression": "sqrt(2)",
                "decimal": repr(math.sqrt(2.0)),
            },
        },
        "quadrature_x_squared": quadrature,
        "quadrature_parameters": {
            "function": {"id": "square", "expression": "x*x"},
            "bounds": [quadrature_left, quadrature_right],
            "interval_grid": list(quadrature_grid),
            "reference_integral": {
                "kind": "nilai eksak",
                "fraction": str(quadrature_reference),
                "decimal": float(quadrature_reference),
            },
        },
        "linear_system": {
            "matrix": [list(row) for row in matrix],
            "right_hand_side": list(vector),
            "exact_solution": [str(value) for value in exact_solution],
            "floating_solution": list(float_solution),
            "residual": list(system_residual),
        },
        "euler_y_prime_y": euler_rows,
        "euler_parameters": {
            "derivative": {
                "id": "identity_derivative",
                "expression": "y",
            },
            "initial_time": euler_initial_time,
            "initial_value": euler_initial_value,
            "target_time": euler_target_time,
            "steps_grid": list(euler_steps_grid),
            "step_rule": "(target_time - initial_time) / steps",
            "reference_solution": {
                "expression": "exp(t)",
                "value_at_target": repr(euler_reference),
            },
        },
        "proof_boundary": "eksperimen memeriksa kasus; jaminan umum memerlukan teorema metode",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(build_results()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
