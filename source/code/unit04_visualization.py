"""Artefak visualisasi deterministik untuk Unit 4.

Kode asli proyek O002; lihat LICENSE-CODE.md.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
import hashlib
import io
import json
from math import isfinite
from pathlib import Path
from typing import Sequence

import matplotlib


matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402


SCHEMA = "o002.unit04.visualization.v1"
FIGURE_TITLE = "Jarak terukur dan model gerak berkecepatan tetap"
ALT_TEXT = (
    "Grafik garis dan titik untuk tujuh pengamatan pada waktu 0 sampai 6 detik. "
    "Sumbu mendatar menyatakan waktu dalam detik dan sumbu tegak menyatakan "
    "jarak dalam meter, keduanya dimulai dari nol. Titik lingkaran menunjukkan "
    "jarak terukur 1,0; 3,1; 4,8; 7,2; 9,0; 10,9; dan 13,1 meter, masing-masing "
    "dengan batang ketidakpastian plus-minus 0,4 meter. Garis putus-putus "
    "menunjukkan model d sama dengan 2t plus 1; seluruh nilai model berada di "
    "dalam interval ketidakpastian pengamatan."
)


@dataclass(frozen=True)
class Observation:
    """Satu pengamatan jarak dengan satuan dan ketidakpastian eksplisit."""

    time_s: int
    measured_distance_m: float
    uncertainty_m: float
    model_distance_m: float


OBSERVATIONS = (
    Observation(0, 1.0, 0.4, 1.0),
    Observation(1, 3.1, 0.4, 3.0),
    Observation(2, 4.8, 0.4, 5.0),
    Observation(3, 7.2, 0.4, 7.0),
    Observation(4, 9.0, 0.4, 9.0),
    Observation(5, 10.9, 0.4, 11.0),
    Observation(6, 13.1, 0.4, 13.0),
)


def validate_observations(observations: Sequence[Observation]) -> None:
    """Tolak data kosong, tak berhingga, tak terurut, atau tanpa galat positif."""

    if not observations:
        raise ValueError("observations tidak boleh kosong")

    times = [observation.time_s for observation in observations]
    if times != sorted(times) or len(set(times)) != len(times):
        raise ValueError("waktu harus unik dan terurut menaik")

    for observation in observations:
        numeric_values = (
            observation.time_s,
            observation.measured_distance_m,
            observation.uncertainty_m,
            observation.model_distance_m,
        )
        if not all(isfinite(value) for value in numeric_values):
            raise ValueError("semua nilai harus berhingga")
        if observation.uncertainty_m <= 0:
            raise ValueError("ketidakpastian harus positif")


def model_is_within_uncertainty(observation: Observation) -> bool:
    """Periksa apakah nilai model berada dalam interval pengamatan."""

    lower = observation.measured_distance_m - observation.uncertainty_m
    upper = observation.measured_distance_m + observation.uncertainty_m
    return lower <= observation.model_distance_m <= upper


def visible_height_ratio(lower_value: float, upper_value: float, baseline: float) -> float:
    """Hitung rasio tinggi tampak dua nilai relatif terhadap garis dasar."""

    if not all(isfinite(value) for value in (lower_value, upper_value, baseline)):
        raise ValueError("nilai dan garis dasar harus berhingga")
    if upper_value < lower_value:
        raise ValueError("upper_value tidak boleh lebih kecil dari lower_value")
    if baseline >= lower_value:
        raise ValueError("garis dasar harus lebih kecil dari kedua nilai")
    return (upper_value - baseline) / (lower_value - baseline)


def canonical_csv_bytes(observations: Sequence[Observation] = OBSERVATIONS) -> bytes:
    """Serialisasikan data dan satuannya ke CSV UTF-8 dengan baris akhir LF."""

    validate_observations(observations)
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(
        (
            "time_s",
            "measured_distance_m",
            "uncertainty_m",
            "model_distance_m",
        )
    )
    for observation in observations:
        writer.writerow(
            (
                str(observation.time_s),
                f"{observation.measured_distance_m:.1f}",
                f"{observation.uncertainty_m:.1f}",
                f"{observation.model_distance_m:.1f}",
            )
        )
    return stream.getvalue().encode("utf-8")


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasikan JSON secara kanonis untuk perbandingan berbasis hash."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def create_figure(
    observations: Sequence[Observation] = OBSERVATIONS,
) -> tuple[Figure, Axes]:
    """Buat grafik dengan satuan, skala jujur, dan pengodean redundan."""

    validate_observations(observations)
    times = [observation.time_s for observation in observations]
    measured = [observation.measured_distance_m for observation in observations]
    uncertainty = [observation.uncertainty_m for observation in observations]
    model = [observation.model_distance_m for observation in observations]

    figure, axes = plt.subplots(figsize=(8.0, 4.8))
    axes.errorbar(
        times,
        measured,
        yerr=uncertainty,
        fmt="o",
        markersize=6,
        capsize=4,
        color="#0072B2",
        ecolor="#4D4D4D",
        label="Pengukuran (±0,4 m)",
    )
    axes.plot(
        times,
        model,
        color="#D55E00",
        linestyle="--",
        linewidth=2,
        label="Model d = 2t + 1",
    )
    axes.set_title(FIGURE_TITLE)
    axes.set_xlabel("Waktu, t (s)")
    axes.set_ylabel("Jarak, d (m)")
    axes.set_xlim(0, 6.25)
    axes.set_ylim(0, 14)
    axes.set_xticks(times)
    axes.set_yticks(range(0, 15, 2))
    axes.grid(True, color="#D9D9D9", linewidth=0.8)
    axes.set_axisbelow(True)
    axes.legend(loc="upper left", frameon=True)
    figure.subplots_adjust(left=0.11, right=0.97, bottom=0.15, top=0.87)
    return figure, axes


def write_svg(
    output: Path,
    observations: Sequence[Observation] = OBSERVATIONS,
) -> None:
    """Tulis SVG stabil dengan judul dan deskripsi aksesibel."""

    output.parent.mkdir(parents=True, exist_ok=True)
    with matplotlib.rc_context(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.fonttype": "none",
            "svg.hashsalt": "o002-unit04-visualization-v1",
        }
    ):
        figure, _ = create_figure(observations)
        try:
            figure.savefig(
                output,
                format="svg",
                metadata={
                    "Title": FIGURE_TITLE,
                    "Description": ALT_TEXT,
                    "Creator": "O002",
                    "Date": None,
                },
            )
        finally:
            plt.close(figure)


def sha256_file(path: Path) -> str:
    """Kembalikan SHA-256 berkas sebagai teks heksadesimal kecil."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_artifacts(output_dir: Path) -> dict[str, Path]:
    """Tulis data, gambar, teks alternatif, dan manifes yang deterministik."""

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "data": output_dir / "unit04-data.csv",
        "figure": output_dir / "unit04-figure.svg",
        "alt_text": output_dir / "unit04-alt.txt",
        "manifest": output_dir / "unit04-manifest.json",
    }

    paths["data"].write_bytes(canonical_csv_bytes())
    paths["alt_text"].write_text(ALT_TEXT + "\n", encoding="utf-8", newline="\n")
    write_svg(paths["figure"])

    manifest = {
        "schema": SCHEMA,
        "question": "Apakah data pengukuran konsisten dengan model d = 2t + 1?",
        "units": {"distance": "m", "time": "s", "uncertainty": "m"},
        "encoding": {
            "measurement": "titik lingkaran",
            "model": "garis putus-putus",
            "uncertainty": "batang galat vertikal",
        },
        "axis_policy": {"x_starts_at_zero": True, "y_starts_at_zero": True},
        "all_model_values_within_uncertainty": all(
            model_is_within_uncertainty(observation)
            for observation in OBSERVATIONS
        ),
        "claim_limit": (
            "Grafik menunjukkan konsistensi pada tujuh pengamatan; grafik tidak "
            "membuktikan model untuk semua waktu."
        ),
        "artifacts": {
            paths["data"].name: sha256_file(paths["data"]),
            paths["figure"].name: sha256_file(paths["figure"]),
            paths["alt_text"].name: sha256_file(paths["alt_text"]),
        },
    }
    paths["manifest"].write_bytes(canonical_json_bytes(manifest))
    return paths


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_artifacts(args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
