from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from typing import Any, Sequence


REQUIRED_CLAIM_FIELDS = {"id", "kind", "statement", "evidence", "limitations"}
REQUIRED_MANIFEST_FIELDS = {
    "schema",
    "command",
    "environment",
    "parameters",
    "inputs",
    "outputs",
    "artifacts",
    "claims",
}
ALLOWED_CLAIM_KINDS = {"mathematical", "implementation", "empirical"}
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_member_path(relative: str) -> str:
    """Validate and return one portable, canonical POSIX package path."""

    if (
        not isinstance(relative, str)
        or not relative
        or relative != relative.strip()
    ):
        raise ValueError(f"jalur paket tidak aman: {relative!r}")
    if "\\" in relative or "\x00" in relative:
        raise ValueError(f"jalur paket tidak aman: {relative}")
    posix = PurePosixPath(relative)
    if (
        posix.is_absolute()
        or not posix.parts
        or ".." in posix.parts
        or any(":" in part for part in posix.parts)
        or posix.as_posix() != relative
    ):
        raise ValueError(f"jalur paket tidak aman: {relative}")
    return posix.as_posix()


def safe_member(root: Path, relative: str) -> Path:
    relative = canonical_member_path(relative)
    posix = PurePosixPath(relative)
    candidate = (root / Path(*posix.parts)).resolve()
    resolved_root = root.resolve()
    if candidate != resolved_root and resolved_root not in candidate.parents:
        raise ValueError(f"jalur keluar dari paket: {relative}")
    return candidate


def validate_claim(claim: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_CLAIM_FIELDS - claim.keys()
    if missing:
        errors.append("medan klaim hilang: " + ", ".join(sorted(missing)))
    if claim.get("kind") not in ALLOWED_CLAIM_KINDS:
        errors.append(f"jenis klaim tidak dikenal: {claim.get('kind')}")
    for field in REQUIRED_CLAIM_FIELDS - {"kind"}:
        if field in claim and not isinstance(claim[field], str):
            errors.append(f"medan klaim bukan string: {field}")
        elif field in claim and not claim[field].strip():
            errors.append(f"medan klaim kosong: {field}")
        elif field in claim and claim[field] != claim[field].strip():
            errors.append(f"medan klaim memiliki spasi tepi: {field}")
    return errors


def canonical_path_list(value: object, field: str, *, nonempty: bool) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} harus berupa daftar")
    if nonempty and not value:
        raise ValueError(f"{field} harus memuat setidaknya satu jalur")
    paths: list[str] = []
    folded: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"jalur {field} bukan string")
        path = canonical_member_path(item)
        key = path.casefold()
        if key in folded:
            raise ValueError(f"jalur {field} duplikat: {path}")
        folded.add(key)
        paths.append(path)
    return paths


def validate_execution_contract(
    manifest: dict[str, Any],
) -> tuple[list[str], dict[str, Any], dict[str, Any], list[str], list[str]]:
    missing = REQUIRED_MANIFEST_FIELDS - manifest.keys()
    if missing:
        raise ValueError("medan manifest hilang: " + ", ".join(sorted(missing)))

    command = manifest["command"]
    if (
        not isinstance(command, list)
        or not command
        or any(
            not isinstance(argument, str)
            or not argument.strip()
            or argument != argument.strip()
            for argument in command
        )
    ):
        raise ValueError("command harus berupa larik argumen string yang tidak kosong")

    environment = manifest["environment"]
    if not isinstance(environment, dict):
        raise ValueError("environment harus berupa objek")
    required_environment = {"runtime", "runtime_version", "dependencies"}
    missing_environment = required_environment - environment.keys()
    if missing_environment:
        raise ValueError(
            "medan environment hilang: " + ", ".join(sorted(missing_environment))
        )
    for field in ("runtime", "runtime_version"):
        value = environment[field]
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ValueError(f"environment.{field} harus berupa string yang tidak kosong")
    dependencies = environment["dependencies"]
    if not isinstance(dependencies, list) or any(
        not isinstance(item, str) or not item.strip() or item != item.strip()
        for item in dependencies
    ):
        raise ValueError("environment.dependencies harus berupa daftar string")

    parameters = manifest["parameters"]
    if not isinstance(parameters, dict) or any(
        not isinstance(key, str) or not key.strip() or key != key.strip()
        for key in parameters
    ):
        raise ValueError("parameters harus berupa objek dengan kunci string kanonis")

    inputs = canonical_path_list(manifest["inputs"], "inputs", nonempty=False)
    outputs = canonical_path_list(manifest["outputs"], "outputs", nonempty=True)
    return command, environment, parameters, inputs, outputs


def verify_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise ValueError("manifest harus berupa objek")
    if manifest.get("schema") != "o002.run-manifest.v1":
        raise ValueError("skema manifest tidak didukung")
    command, environment, parameters, inputs, outputs = validate_execution_contract(
        manifest
    )
    records = manifest.get("artifacts")
    claims = manifest.get("claims")
    if not isinstance(records, list) or not isinstance(claims, list):
        raise ValueError("artifacts dan claims harus berupa daftar")
    if not records:
        raise ValueError("manifest harus memuat setidaknya satu artefak")
    if not claims:
        raise ValueError("manifest harus memuat setidaknya satu klaim")

    checked: list[dict[str, Any]] = []
    artifact_by_path: dict[str, dict[str, Any]] = {}
    folded_artifact_paths: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("rekaman artefak harus berupa objek")
        relative = record.get("path")
        if not isinstance(relative, str) or not relative.strip():
            raise ValueError("jalur artefak hilang")
        relative = canonical_member_path(relative)
        folded = relative.casefold()
        if folded in folded_artifact_paths:
            raise ValueError(f"jalur artefak duplikat: {relative}")
        folded_artifact_paths.add(folded)
        expected_size = record.get("bytes")
        expected_hash = record.get("sha256")
        if (
            isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or expected_size < 0
        ):
            raise ValueError(f"ukuran artefak tidak sah: {relative}")
        if (
            not isinstance(expected_hash, str)
            or not SHA256_RE.fullmatch(expected_hash)
        ):
            raise ValueError(f"SHA-256 artefak tidak sah: {relative}")
        path = safe_member(root, relative)
        if not path.is_file():
            raise FileNotFoundError(f"artefak tidak ditemukan: {relative}")
        actual_size = path.stat().st_size
        actual_hash = sha256(path)
        if actual_size != expected_size or actual_hash != expected_hash.casefold():
            raise ValueError(f"artefak tidak cocok: {relative}")
        verified_record = {
            "path": relative,
            "bytes": actual_size,
            "sha256": actual_hash,
        }
        checked.append(verified_record)
        artifact_by_path[relative] = verified_record

    for field, paths in (("inputs", inputs), ("outputs", outputs)):
        for path in paths:
            if path not in artifact_by_path:
                raise ValueError(f"{field} tidak merujuk artefak terdaftar: {path}")
    output_paths = set(outputs)

    claim_errors: list[str] = []
    claim_ids: set[str] = set()
    claim_bindings: list[dict[str, str]] = []
    for index, claim in enumerate(claims, start=1):
        if not isinstance(claim, dict):
            claim_errors.append(f"klaim {index}: klaim harus berupa objek")
            continue
        claim_label = claim.get("id", f"klaim-{index}")
        validation_errors = validate_claim(claim)
        claim_errors.extend(f"{claim_label}: {message}" for message in validation_errors)
        claim_id = claim.get("id")
        if isinstance(claim_id, str) and claim_id.strip():
            if claim_id in claim_ids:
                claim_errors.append(f"ID klaim duplikat: {claim_id}")
            claim_ids.add(claim_id)

        evidence = claim.get("evidence")
        if isinstance(evidence, str) and evidence.strip() and evidence == evidence.strip():
            try:
                evidence = canonical_member_path(evidence)
            except ValueError as exc:
                claim_errors.append(f"{claim_label}: {exc}")
                continue
            artifact = artifact_by_path.get(evidence)
            if artifact is None:
                claim_errors.append(
                    f"{claim_label}: evidence tidak merujuk artefak terdaftar: {evidence}"
                )
            elif evidence not in output_paths:
                claim_errors.append(
                    f"{claim_label}: evidence tidak merujuk keluaran terdaftar: {evidence}"
                )
            elif not validation_errors and isinstance(claim_id, str):
                claim_bindings.append(
                    {
                        "claim_id": claim_id,
                        "evidence_path": evidence,
                        "evidence_sha256": artifact["sha256"],
                    }
                )
    if claim_errors:
        raise ValueError("; ".join(claim_errors))

    return {
        "schema": "o002.unit12-verification.v1",
        "manifest_schema": manifest["schema"],
        "command": command,
        "environment": environment,
        "parameters": parameters,
        "inputs_checked": inputs,
        "outputs_checked": outputs,
        "artifacts_checked": checked,
        "claims_checked": len(claims),
        "claim_evidence_bindings": claim_bindings,
        "verified": True,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--root", type=Path, default=Path("project"))
    verify.add_argument(
        "--manifest", type=Path, default=Path("project/RUN_MANIFEST.json")
    )
    verify.add_argument(
        "--output", type=Path, default=Path("output/unit12-results.json")
    )
    args = parser.parse_args(argv)

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = verify_manifest(args.root, manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
