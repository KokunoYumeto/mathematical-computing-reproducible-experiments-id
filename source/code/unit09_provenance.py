"""Manifest provenans deterministik untuk Unit 9.

Kode asli proyek O002; lihat LICENSE-CODE.md.
"""

from __future__ import annotations

import argparse
import csv
from decimal import Context, Decimal, DivisionByZero, InvalidOperation, Overflow, ROUND_HALF_EVEN
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import re
from typing import Mapping, Sequence
import unicodedata


SCHEMA = "o002.unit09.provenance-manifest.v1"
DECIMAL_PRECISION = 28
DECIMAL_EMIN = -999_999
DECIMAL_EMAX = 999_999
RAW_FIELDS = ("sample_id", "length_cm", "mass_g")
DERIVED_FIELDS = ("sample_id", "mass_per_length_g_per_cm")
FORBIDDEN_PRIVATE_FIELDS = frozenset(
    {"name", "email", "phone", "precise_location", "free_text"}
)

RAW_SCHEMA = {
    "schema": "o002.unit09.raw-measurements.v1",
    "fields": [
        {
            "name": "sample_id",
            "type": "string",
            "unit": None,
            "meaning": "pengenal sintetis, bukan identitas orang",
        },
        {
            "name": "length_cm",
            "type": "decimal string",
            "unit": "cm",
            "meaning": "panjang sampel",
        },
        {
            "name": "mass_g",
            "type": "decimal string",
            "unit": "g",
            "meaning": "massa sampel",
        },
    ],
}

DERIVED_SCHEMA = {
    "schema": "o002.unit09.mass-per-length.v1",
    "fields": [
        {
            "name": "sample_id",
            "type": "string",
            "unit": None,
            "source": "raw.sample_id",
            "meaning": "pengenal sintetis yang dipertahankan dari data mentah",
        },
        {
            "name": "mass_per_length_g_per_cm",
            "type": "decimal string",
            "unit": "g/cm",
            "formula": "mass_g / length_cm",
            "meaning": "massa sampel per satuan panjang sampel",
        },
    ],
}

RAW_RECORDS: tuple[dict[str, str], ...] = (
    {"sample_id": "S01", "length_cm": "10.0", "mass_g": "20.0"},
    {"sample_id": "S02", "length_cm": "12.0", "mass_g": "24.6"},
    {"sample_id": "S03", "length_cm": "8.0", "mass_g": "15.8"},
    {"sample_id": "S04", "length_cm": "14.0", "mass_g": "28.7"},
    {"sample_id": "S05", "length_cm": "11.0", "mass_g": "21.8"},
)

DEFAULT_CONFIG: dict[str, object] = {
    "schema": "o002.unit09.config.v1",
    "raw_path": "data/raw/unit09_measurements.csv",
    "derived_path": "data/derived/unit09_mass-per-length.csv",
    "ratio_decimal_places": 3,
    "rounding": "ROUND_HALF_EVEN",
}


def safe_relative_path(value: str) -> str:
    """Kembalikan jalur POSIX relatif kanonis atau tolak jalur berbahaya."""

    if not isinstance(value, str) or not value:
        raise ValueError("jalur harus berupa teks yang tidak kosong")
    if "\\" in value or "\x00" in value or re.match(r"^[A-Za-z]:", value):
        raise ValueError("jalur harus relatif, kanonis, dan memakai garis miring")

    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {".", ".."} for part in path.parts):
        raise ValueError("jalur tidak boleh absolut atau melintasi direktori induk")
    if str(path) != value:
        raise ValueError("jalur harus berada dalam bentuk relatif kanonis")
    return value


def portable_path_key(value: str) -> str:
    """Bentuk pembanding portabel bagi jalur logis yang telah divalidasi."""

    return unicodedata.normalize("NFC", safe_relative_path(value)).casefold()


def validate_unique_artifact_paths(paths: Mapping[str, object]) -> dict[str, str]:
    """Tolak alias jalur lintas-peran, termasuk perbedaan kapitalisasi saja."""

    validated: dict[str, str] = {}
    owner_by_key: dict[str, str] = {}
    for role, candidate in paths.items():
        path = safe_relative_path(candidate)
        key = portable_path_key(path)
        previous = owner_by_key.get(key)
        if previous is not None:
            raise ValueError(
                f"jalur artefak harus unik secara portabel: {previous} dan {role}"
            )
        owner_by_key[key] = role
        validated[role] = path
    return validated


def deterministic_decimal_context() -> Context:
    """Buat konteks desimal baru yang tidak mewarisi keadaan proses pemanggil."""

    return Context(
        prec=DECIMAL_PRECISION,
        rounding=ROUND_HALF_EVEN,
        Emin=DECIMAL_EMIN,
        Emax=DECIMAL_EMAX,
        capitals=1,
        clamp=0,
        flags=[],
        traps=[InvalidOperation, DivisionByZero, Overflow],
    )


def decimal_context_identity() -> dict[str, object]:
    """Serialisasikan seluruh pengaturan konteks yang memengaruhi perhitungan."""

    context = deterministic_decimal_context()
    return {
        "precision": context.prec,
        "rounding": context.rounding,
        "emin": context.Emin,
        "emax": context.Emax,
        "capitals": context.capitals,
        "clamp": context.clamp,
        "traps": sorted(
            signal.__name__
            for signal, enabled in context.traps.items()
            if enabled
        ),
    }


def validate_config(config: Mapping[str, object]) -> None:
    """Periksa kontrak konfigurasi yang disimpan terpisah dari kode."""

    expected = {
        "schema",
        "raw_path",
        "derived_path",
        "ratio_decimal_places",
        "rounding",
    }
    if set(config) != expected:
        raise ValueError("medan konfigurasi tidak sesuai schema")
    if config["schema"] != "o002.unit09.config.v1":
        raise ValueError("schema konfigurasi tidak dikenal")
    safe_relative_path(config["raw_path"])
    safe_relative_path(config["derived_path"])
    places = config["ratio_decimal_places"]
    if isinstance(places, bool) or not isinstance(places, int) or not 0 <= places <= 9:
        raise ValueError("ratio_decimal_places harus bilangan bulat antara 0 dan 9")
    if config["rounding"] != "ROUND_HALF_EVEN":
        raise ValueError("hanya ROUND_HALF_EVEN yang didukung baseline")


def validate_raw_records(records: Sequence[Mapping[str, str]]) -> None:
    """Periksa schema, satuan tersirat nama kolom, nilai, dan bidang privat."""

    if not records:
        raise ValueError("data mentah tidak boleh kosong")

    seen_ids: set[str] = set()
    for record in records:
        private = FORBIDDEN_PRIVATE_FIELDS.intersection(
            key.casefold() for key in record
        )
        if private:
            raise ValueError(f"bidang privat dilarang: {sorted(private)}")
        if set(record) != set(RAW_FIELDS):
            raise ValueError("medan data mentah tidak sesuai schema")

        sample_id = record["sample_id"]
        if not re.fullmatch(r"S[0-9]{2}", sample_id):
            raise ValueError("sample_id harus berbentuk S diikuti dua digit")
        if sample_id in seen_ids:
            raise ValueError("sample_id harus unik")
        seen_ids.add(sample_id)

        for field in ("length_cm", "mass_g"):
            raw_value = record[field]
            if not isinstance(raw_value, str):
                raise ValueError(f"{field} harus berupa teks desimal")
            try:
                value = Decimal(raw_value)
            except (InvalidOperation, ValueError) as error:
                raise ValueError(f"{field} harus berupa desimal sah") from error
            if not value.is_finite() or value <= 0:
                raise ValueError(f"{field} harus berhingga dan positif")


def derive_records(
    records: Sequence[Mapping[str, str]],
    decimal_places: int,
) -> tuple[dict[str, str], ...]:
    """Turunkan rasio massa per panjang dengan pembulatan yang dibekukan."""

    validate_raw_records(records)
    if isinstance(decimal_places, bool) or not isinstance(decimal_places, int):
        raise TypeError("decimal_places harus bilangan bulat")
    if not 0 <= decimal_places <= 9:
        raise ValueError("decimal_places harus antara 0 dan 9")

    quantum = Decimal(1).scaleb(-decimal_places)
    context = deterministic_decimal_context()
    derived: list[dict[str, str]] = []
    for record in records:
        ratio = context.divide(
            Decimal(record["mass_g"]), Decimal(record["length_cm"])
        )
        rounded = context.quantize(ratio, quantum)
        derived.append(
            {
                "sample_id": record["sample_id"],
                "mass_per_length_g_per_cm": f"{rounded:.{decimal_places}f}",
            }
        )
    return tuple(derived)


def canonical_csv_bytes(
    records: Sequence[Mapping[str, str]],
    fields: Sequence[str],
) -> bytes:
    """Serialisasikan tabel ke CSV UTF-8 dengan urutan kolom dan LF tetap."""

    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(fields), lineterminator="\n")
    writer.writeheader()
    for record in records:
        if set(record) != set(fields):
            raise ValueError("medan rekaman tidak cocok dengan urutan CSV")
        writer.writerow({field: record[field] for field in fields})
    return stream.getvalue().encode("utf-8")


def canonical_json_bytes(payload: object) -> bytes:
    """Serialisasikan JSON UTF-8 dengan kunci, inden, dan LF tetap."""

    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    """Kembalikan SHA-256 payload sebagai teks heksadesimal kecil."""

    return hashlib.sha256(payload).hexdigest()


def artifact_binding(
    *,
    logical_path: str,
    payload: bytes,
    media_type: str,
    role: str,
    provenance: str,
    rights: Mapping[str, object],
) -> dict[str, object]:
    """Ikat satu komponen pada jalur logis, ukuran, hash, asal, dan haknya."""

    return {
        "logical_path": safe_relative_path(logical_path),
        "media_type": media_type,
        "role": role,
        "bytes": len(payload),
        "sha256": sha256_bytes(payload),
        "provenance": provenance,
        "rights": dict(rights),
    }


def build_manifest(
    config: Mapping[str, object] = DEFAULT_CONFIG,
    raw_records: Sequence[Mapping[str, str]] = RAW_RECORDS,
) -> dict[str, object]:
    """Bangun manifest yang mengikat data, konfigurasi, kode, dan lingkungan."""

    validate_config(config)
    validate_raw_records(raw_records)
    logical_paths = validate_unique_artifact_paths(
        {
            "raw_data": config["raw_path"],
            "derived_data": config["derived_path"],
            "configuration": "config/unit09.json",
            "environment_lock": "environment/unit09-python-lock.json",
            "code": "source/code/unit09_provenance.py",
        }
    )
    decimal_places = config["ratio_decimal_places"]
    assert isinstance(decimal_places, int)
    derived_records = derive_records(raw_records, decimal_places)

    raw_bytes = canonical_csv_bytes(raw_records, RAW_FIELDS)
    derived_bytes = canonical_csv_bytes(derived_records, DERIVED_FIELDS)
    config_bytes = canonical_json_bytes(dict(config))
    code_bytes = Path(__file__).read_bytes()

    environment_identity = {
        "implementation": platform.python_implementation(),
        "python": platform.python_version(),
        "external_dependencies": [],
        "stdlib_only": True,
        "decimal_context": decimal_context_identity(),
    }
    environment_bytes = canonical_json_bytes(environment_identity)

    project_authored_rights = {
        "component_status": "dibuat khusus untuk Unit 9",
        "third_party_material": False,
        "blanket_claim_applied": False,
    }
    artifacts = {
        "raw_data": artifact_binding(
            logical_path=logical_paths["raw_data"],
            payload=raw_bytes,
            media_type="text/csv; charset=utf-8",
            role="data mentah sintetis",
            provenance="nilai sumber ditetapkan dalam unit09_provenance.py",
            rights=project_authored_rights,
        ),
        "derived_data": artifact_binding(
            logical_path=logical_paths["derived_data"],
            payload=derived_bytes,
            media_type="text/csv; charset=utf-8",
            role="data turunan",
            provenance=(
                "mass_g dibagi length_cm lalu dibulatkan menurut konfigurasi"
            ),
            rights=project_authored_rights,
        ),
        "configuration": artifact_binding(
            logical_path=logical_paths["configuration"],
            payload=config_bytes,
            media_type="application/json",
            role="konfigurasi run yang terpisah dari kode",
            provenance="DEFAULT_CONFIG atau konfigurasi tervalidasi pemanggil",
            rights=project_authored_rights,
        ),
        "environment_lock": artifact_binding(
            logical_path=logical_paths["environment_lock"],
            payload=environment_bytes,
            media_type="application/json",
            role="identitas lingkungan minimum",
            provenance="diturunkan dari runtime Python aktif",
            rights={
                "component_status": "fakta lingkungan yang dihasilkan",
                "third_party_material": False,
                "blanket_claim_applied": False,
            },
        ),
        "code": artifact_binding(
            logical_path=logical_paths["code"],
            payload=code_bytes,
            media_type="text/x-python; charset=utf-8",
            role="kode transformasi dan manifest",
            provenance="kode asli proyek O002",
            rights={
                "license": "MIT",
                "license_file": "LICENSE-CODE.md",
                "third_party_material": False,
            },
        ),
    }

    manifest: dict[str, object] = {
        "schema": SCHEMA,
        "run": {
            "command": (
                "python source/code/unit09_provenance.py "
                "--output output/unit09-manifest.json"
            ),
            "working_directory": "akar proyek",
            "network_required": False,
            "current_time_recorded": False,
        },
        "configuration": dict(config),
        "environment_identity": environment_identity,
        "datasets": {
            "raw": {
                "schema": RAW_SCHEMA,
                "records": [dict(record) for record in raw_records],
            },
            "derived": {
                "schema": DERIVED_SCHEMA,
                "records": [dict(record) for record in derived_records],
            },
        },
        "artifacts": artifacts,
        "lineage": {
            "input": artifacts["raw_data"]["sha256"],
            "configuration": artifacts["configuration"]["sha256"],
            "code": artifacts["code"]["sha256"],
            "output": artifacts["derived_data"]["sha256"],
            "transformation": "mass_per_length = mass_g / length_cm",
        },
        "privacy": {
            "contains_personal_data": False,
            "excluded_fields": sorted(FORBIDDEN_PRIVATE_FIELDS),
            "policy": (
                "manifes menolak medan privat; gunakan pengenal sintetis dan "
                "jangan memasukkan data sensitif hanya demi reproduksibilitas"
            ),
        },
        "reproducibility": {
            "deterministic_replay": True,
            "byte_reproducibility": (
                "kode, konfigurasi, data mentah, dan lingkungan terkunci yang "
                "sama menghasilkan byte kanonis serta hash yang sama"
            ),
            "semantic_reproducibility": (
                "implementasi atau serialisasi lain dapat menghasilkan nilai "
                "dan satuan sama walaupun byte serta SHA-256 berbeda"
            ),
            "hash_limit": (
                "SHA-256 mengikat byte dan ukuran; hash tidak membuktikan makna, "
                "hak, kebenaran rumus, atau kelengkapan provenans"
            ),
        },
    }
    manifest["core_sha256"] = sha256_bytes(canonical_json_bytes(manifest))
    return manifest


def write_manifest(manifest: Mapping[str, object], output: Path) -> None:
    """Tulis satu manifest JSON kanonis."""

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_json_bytes(dict(manifest)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    write_manifest(build_manifest(), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
