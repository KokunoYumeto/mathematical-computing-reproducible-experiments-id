"""Rancangan eksperimen deterministik untuk Unit 7.

Kode asli proyek O002; lihat LICENSE-CODE.md.
"""

from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import random
from typing import NamedTuple, Sequence


SCHEMA = "o002.unit07.experiment-design.v1"


class Case(NamedTuple):
    """Satu kasus buatan dengan skor bulat dan hasil biner."""

    score: int
    positive: bool


class ExperimentPlan(NamedTuple):
    """Keputusan eksperimen yang dibekukan sebelum data dibangkitkan."""

    parameter_grid: tuple[int, ...]
    reference_threshold: int
    minimum_meaningful_effect: Fraction
    development_seed: int
    development_repetitions: int
    development_cases_per_repetition: int
    holdout_seed: int
    holdout_repetitions: int
    holdout_cases_per_repetition: int


DEFAULT_PLAN = ExperimentPlan(
    parameter_grid=(3, 4, 5, 6, 7),
    reference_threshold=6,
    minimum_meaningful_effect=Fraction(1, 10),
    development_seed=1729,
    development_repetitions=20,
    development_cases_per_repetition=200,
    holdout_seed=271828,
    holdout_repetitions=12,
    holdout_cases_per_repetition=250,
)


def validate_plan(plan: ExperimentPlan) -> None:
    """Periksa bahwa rencana lengkap, terurut, dan memisahkan holdout."""

    grid = plan.parameter_grid
    if not grid or tuple(sorted(set(grid))) != grid:
        raise ValueError("parameter_grid harus unik dan terurut menaik")
    if plan.reference_threshold not in grid:
        raise ValueError("reference_threshold harus berada dalam parameter_grid")
    if not 0 <= plan.minimum_meaningful_effect <= 1:
        raise ValueError("minimum_meaningful_effect harus berada antara 0 dan 1")
    if plan.development_seed == plan.holdout_seed:
        raise ValueError("benih pengembangan dan holdout harus berbeda")
    if plan.development_seed < 0 or plan.holdout_seed < 0:
        raise ValueError("benih harus berupa bilangan bulat taknegatif")
    positive_counts = (
        plan.development_repetitions,
        plan.development_cases_per_repetition,
        plan.holdout_repetitions,
        plan.holdout_cases_per_repetition,
    )
    if any(value <= 0 for value in positive_counts):
        raise ValueError("banyak replikasi dan kasus harus positif")


def generate_cases(seed: int, count: int) -> tuple[Case, ...]:
    """Bangkitkan kasus acak semu dari satu benih yang tercatat."""

    if seed < 0:
        raise ValueError("seed harus taknegatif")
    if count <= 0:
        raise ValueError("count harus positif")

    generator = random.Random(seed)
    cases: list[Case] = []
    for _ in range(count):
        score = generator.randrange(10)
        successes_out_of_five = 4 if score >= 5 else 1
        positive = generator.randrange(5) < successes_out_of_five
        cases.append(Case(score=score, positive=positive))
    return tuple(cases)


def correct_predictions(cases: Sequence[Case], threshold: int) -> int:
    """Hitung prediksi benar untuk aturan `score >= threshold`."""

    return sum((case.score >= threshold) == case.positive for case in cases)


def fraction_record(value: Fraction) -> dict[str, object]:
    """Simpan pecahan eksak beserta desimal empat tempat untuk dibaca manusia."""

    return {
        "fraction": f"{value.numerator}/{value.denominator}",
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": f"{float(value):.4f}",
    }


def run_phase(
    *,
    base_seed: int,
    repetitions: int,
    cases_per_repetition: int,
    thresholds: Sequence[int],
) -> dict[str, object]:
    """Jalankan replikasi berpasangan untuk semua ambang pada data yang sama."""

    threshold_grid = tuple(thresholds)
    if not threshold_grid or len(set(threshold_grid)) != len(threshold_grid):
        raise ValueError("thresholds harus tidak kosong dan unik")
    if repetitions <= 0 or cases_per_repetition <= 0:
        raise ValueError("repetitions dan cases_per_repetition harus positif")

    totals = {threshold: 0 for threshold in threshold_grid}
    replication_records: list[dict[str, object]] = []
    for index in range(repetitions):
        seed = base_seed + index
        cases = generate_cases(seed, cases_per_repetition)
        counts = {
            threshold: correct_predictions(cases, threshold)
            for threshold in threshold_grid
        }
        for threshold, count in counts.items():
            totals[threshold] += count
        replication_records.append(
            {
                "index": index + 1,
                "seed": seed,
                "cases": cases_per_repetition,
                "correct_by_threshold": {
                    str(threshold): counts[threshold]
                    for threshold in threshold_grid
                },
            }
        )

    total_cases = repetitions * cases_per_repetition
    return {
        "base_seed": base_seed,
        "seed_schedule": "base_seed + repetition_index",
        "repetitions_completed": repetitions,
        "cases_per_repetition": cases_per_repetition,
        "total_cases": total_cases,
        "paired_cases_across_thresholds": True,
        "by_threshold": {
            str(threshold): {
                "correct": totals[threshold],
                "total": total_cases,
                "accuracy": fraction_record(Fraction(totals[threshold], total_cases)),
            }
            for threshold in threshold_grid
        },
        "replications": replication_records,
    }


def select_threshold(
    development: dict[str, object],
    parameter_grid: Sequence[int],
) -> int:
    """Pilih akurasi pengembangan tertinggi; ikatan dimenangkan ambang terkecil."""

    by_threshold = development["by_threshold"]
    assert isinstance(by_threshold, dict)

    def selection_key(threshold: int) -> tuple[int, int]:
        record = by_threshold[str(threshold)]
        assert isinstance(record, dict)
        correct = record["correct"]
        assert isinstance(correct, int)
        return correct, -threshold

    return max(parameter_grid, key=selection_key)


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasikan JSON UTF-8 dengan urutan, inden, dan akhir baris tetap."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def build_results(plan: ExperimentPlan = DEFAULT_PLAN) -> dict[str, object]:
    """Jalankan rencana pengembangan lalu nilai pilihan sekali pada holdout."""

    validate_plan(plan)
    minimum_effect = fraction_record(plan.minimum_meaningful_effect)
    minimum_effect_sentence = str(minimum_effect["decimal"]).replace(".", ",")
    development = run_phase(
        base_seed=plan.development_seed,
        repetitions=plan.development_repetitions,
        cases_per_repetition=plan.development_cases_per_repetition,
        thresholds=plan.parameter_grid,
    )
    selected = select_threshold(development, plan.parameter_grid)

    holdout_thresholds = tuple(sorted({selected, plan.reference_threshold}))
    holdout = run_phase(
        base_seed=plan.holdout_seed,
        repetitions=plan.holdout_repetitions,
        cases_per_repetition=plan.holdout_cases_per_repetition,
        thresholds=holdout_thresholds,
    )
    by_threshold = holdout["by_threshold"]
    assert isinstance(by_threshold, dict)
    selected_record = by_threshold[str(selected)]
    reference_record = by_threshold[str(plan.reference_threshold)]
    assert isinstance(selected_record, dict)
    assert isinstance(reference_record, dict)
    selected_correct = selected_record["correct"]
    reference_correct = reference_record["correct"]
    total_cases = holdout["total_cases"]
    assert isinstance(selected_correct, int)
    assert isinstance(reference_correct, int)
    assert isinstance(total_cases, int)

    effect = Fraction(selected_correct - reference_correct, total_cases)
    hypothesis_supported = effect >= plan.minimum_meaningful_effect

    payload: dict[str, object] = {
        "schema": SCHEMA,
        "runtime": {
            "implementation": platform.python_implementation(),
            "python": platform.python_version(),
            "random_generator": "random.Random",
        },
        "question": (
            "Apakah ambang yang dipilih pada data pengembangan meningkatkan "
            f"akurasi holdout sedikitnya {minimum_effect['fraction']} "
            f"(sekitar {minimum_effect_sentence}) dibanding ambang referensi "
            f"{plan.reference_threshold}?"
        ),
        "hypothesis": {
            "direction": "akurasi ambang terpilih lebih tinggi",
            "minimum_meaningful_effect": minimum_effect,
            "declared_before_run": True,
        },
        "variables": {
            "independent": "ambang keputusan dalam parameter_grid",
            "dependent": "proporsi prediksi benar",
            "controlled": [
                "aturan pembangkitan kasus",
                "jumlah kasus per replikasi",
                "jumlah replikasi",
                "jadwal benih",
                "kasus yang sama untuk setiap ambang dalam satu replikasi",
            ],
        },
        "plan": {
            "parameter_grid": list(plan.parameter_grid),
            "reference_threshold": plan.reference_threshold,
            "minimum_meaningful_effect": minimum_effect,
            "development_seed": plan.development_seed,
            "development_repetitions": plan.development_repetitions,
            "development_cases_per_repetition": (
                plan.development_cases_per_repetition
            ),
            "holdout_seed": plan.holdout_seed,
            "holdout_repetitions": plan.holdout_repetitions,
            "holdout_cases_per_repetition": plan.holdout_cases_per_repetition,
            "selection_rule": (
                "akurasi pengembangan tertinggi; jika seri pilih ambang terkecil"
            ),
            "stopping_rule": {
                "development": (
                    f"tepat {plan.development_repetitions} replikasi x "
                    f"{plan.development_cases_per_repetition} kasus"
                ),
                "holdout": (
                    f"tepat {plan.holdout_repetitions} replikasi x "
                    f"{plan.holdout_cases_per_repetition} kasus"
                ),
                "early_stopping_allowed": False,
            },
            "holdout_policy": (
                "holdout tidak dipakai untuk memilih ambang dan dinilai sekali "
                "setelah pilihan dibekukan"
            ),
        },
        "randomness": {
            "kind": "acak semu dengan benih tercatat",
            "replayable": True,
            "genuine_nondeterminism_note": (
                "Benih tidak dapat mengulang gangguan fisik, penjadwalan sistem, "
                "atau sumber nondeterminisme nyata yang tidak direkam."
            ),
        },
        "development": development,
        "selected_threshold": selected,
        "holdout": holdout,
        "conclusion": {
            "selected_accuracy": selected_record["accuracy"],
            "reference_accuracy": reference_record["accuracy"],
            "effect_size": fraction_record(effect),
            "effect_unit": "selisih proporsi; kalikan 100 untuk poin persentase",
            "hypothesis_supported": hypothesis_supported,
            "result_label": (
                "mendukung hipotesis awal"
                if hypothesis_supported
                else "hasil negatif terhadap ambang efek yang ditetapkan"
            ),
            "minimum_effect_was_not_changed_after_run": True,
        },
        "proof_boundary": {
            "proves_selected_threshold_is_universally_best": False,
            "reason": (
                "Eksperimen memeriksa kisi, generator, benih, dan sampel "
                "berhingga; klaim umum memerlukan argumen lain."
            ),
        },
    }
    payload["core_sha256"] = hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
    return payload


def write_result(result: dict[str, object], output: Path) -> None:
    """Tulis satu rekaman JSON kanonis."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(result))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_result(build_results(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
