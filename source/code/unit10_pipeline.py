from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import secrets
import sys
from typing import Mapping, Sequence


Graph = Mapping[str, Sequence[str]]
MAXIMUM_TEMP_ATTEMPTS = 128


def topological_order(graph: Graph) -> list[str]:
    names = set(graph)
    for task, dependencies in graph.items():
        unknown = set(dependencies) - names
        if unknown:
            raise ValueError(f"dependensi tidak dikenal untuk {task}: {sorted(unknown)}")

    remaining = {task: set(dependencies) for task, dependencies in graph.items()}
    order: list[str] = []
    while remaining:
        ready = sorted(task for task, dependencies in remaining.items() if not dependencies)
        if not ready:
            raise ValueError("graf tugas mengandung siklus")
        for task in ready:
            order.append(task)
            del remaining[task]
        for dependencies in remaining.values():
            dependencies.difference_update(ready)
    return order


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def runtime_environment() -> dict[str, str]:
    """Rekam identitas runtime aktual tanpa jalur profil atau nama mesin."""

    return {
        "byteorder": sys.byteorder,
        "machine": platform.machine(),
        "operating_system": platform.system(),
        "python_cache_tag": sys.implementation.cache_tag or "",
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
    }


def temporary_open_flags() -> int:
    """Gunakan pembuatan eksklusif dan larangan mengikuti tautan bila tersedia."""

    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    return flags


def open_unique_same_directory_temp(output: Path) -> tuple[int, Path]:
    """Buka berkas sementara unik di direktori tujuan tanpa menimpa nama lama."""

    for _ in range(MAXIMUM_TEMP_ATTEMPTS):
        token = secrets.token_hex(16)
        candidate = output.parent / f".{output.name}.{token}.tmp"
        try:
            descriptor = os.open(candidate, temporary_open_flags(), 0o600)
        except FileExistsError:
            continue
        return descriptor, candidate
    raise FileExistsError("tidak dapat membuat nama sementara unik")


def atomic_write_bytes(output: Path, payload: bytes) -> None:
    """Tulis byte lengkap lalu ganti nama tujuan secara atomik.

    Berkas sementara selalu berada di direktori tujuan. ``O_EXCL`` mencegah
    nama yang sudah ada dibuka atau ditimpa; ``O_NOFOLLOW`` ditambahkan pada
    sistem yang menyediakannya. Kegagalan sebelum ``os.replace`` mempertahankan
    keluaran resmi lama dan mencoba membersihkan berkas sementara.
    """

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor: int | None = None
    temporary: Path | None = None
    try:
        descriptor, temporary = open_unique_same_directory_temp(output)
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = None
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        temporary = None
    except BaseException:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
        raise


def task_fingerprint_preimage(
    *,
    inputs: Mapping[str, bytes],
    code: bytes,
    parameters: Mapping[str, object],
    environment: Mapping[str, str],
) -> dict[str, object]:
    """Bangun rekaman kanonis yang byte-nya menjadi preimage fingerprint."""

    return {
        "inputs": {name: sha256_bytes(data) for name, data in sorted(inputs.items())},
        "code_sha256": sha256_bytes(code),
        "parameters": dict(sorted(parameters.items())),
        "environment": dict(sorted(environment.items())),
    }


def task_fingerprint(
    *,
    inputs: Mapping[str, bytes],
    code: bytes,
    parameters: Mapping[str, object],
    environment: Mapping[str, str],
) -> str:
    preimage = task_fingerprint_preimage(
        inputs=inputs,
        code=code,
        parameters=parameters,
        environment=environment,
    )
    return sha256_bytes(canonical_json_bytes(preimage))


def is_fresh(
    expected_fingerprint: str,
    recorded_fingerprint: str,
    outputs: Mapping[str, tuple[bytes, str]],
    *,
    expected_output_names: Sequence[str] | None = None,
) -> bool:
    """Periksa fingerprint dan setiap keluaran yang wajib ada.

    Kontrak unit ini selalu mempunyai sedikitnya satu keluaran. Pemetaan kosong,
    nama keluaran wajib yang hilang, atau nama tambahan yang tidak dideklarasikan
    karena itu tidak pernah dianggap mutakhir.
    """

    if expected_fingerprint != recorded_fingerprint:
        return False
    if not outputs:
        return False
    if expected_output_names is not None:
        expected_names = tuple(expected_output_names)
        if not expected_names or len(expected_names) != len(set(expected_names)):
            return False
        if set(outputs) != set(expected_names):
            return False
    return all(sha256_bytes(data) == recorded_hash for data, recorded_hash in outputs.values())


def build_results() -> dict[str, object]:
    graph = {
        "data": [],
        "fit": ["data"],
        "plot": ["data", "fit"],
        "report": ["plot"],
    }
    inputs = {"inputs/data.csv": b"x,y\n0,1\n1,3\n"}
    code = b"model = lambda x: 2*x + 1\n"
    parameters = {"model": "linear", "intercept": True}
    environment = runtime_environment()
    fingerprint_preimage = task_fingerprint_preimage(
        inputs=inputs,
        code=code,
        parameters=parameters,
        environment=environment,
    )
    fingerprint = sha256_bytes(canonical_json_bytes(fingerprint_preimage))
    output = b"slope,intercept\n2,1\n"
    output_name = "fit.csv"
    output_hash = sha256_bytes(output)
    return {
        "schema": "o002.unit10-results.v1",
        "graph": graph,
        "order": topological_order(graph),
        "fingerprint_preimage": fingerprint_preimage,
        "task_fingerprint": fingerprint,
        "expected_outputs": {
            output_name: {"bytes": len(output), "sha256": output_hash},
        },
        "output_sha256": output_hash,
        "fresh_replay": is_fresh(
            fingerprint,
            fingerprint,
            {output_name: (output, output_hash)},
            expected_output_names=(output_name,),
        ),
        "proof_boundary": "alur kerja hijau membuktikan pemeriksaan terprogram lulus, bukan teorema lengkap",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    atomic_write_bytes(args.output, canonical_json_bytes(build_results()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
