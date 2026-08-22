from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable, Sequence
import zipfile


ROOT = Path(__file__).resolve().parents[1]
FIXED_ZIP_TIME = (2026, 8, 22, 0, 0, 0)
VERSION_RE = re.compile(r"^[0-9]{4}\.[0-9]{2}\.[0-9]{2}(?:\.[0-9]+)?$")
SOURCE_ROOT_FILES = (
    ".gitattributes",
    ".gitignore",
    "_quarto.yml",
    "accessibility.html",
    "CITATION.cff",
    "index.qmd",
    "LICENSE-CODE.md",
    "LICENSE-RUNTIME-APACHE-2.0.txt",
    "LICENSE-TEXT.md",
    "README.md",
    "requirements-build.txt",
    "RUNTIME-LICENSES.md",
    "styles.css",
    "THIRD_PARTY.md",
)
SOURCE_DIRECTORIES = (
    "backend",
    "build-support",
    "environment",
    "scripts",
    "source",
    "tests",
)
SOURCE_CONTROL_FILES = (
    "00_control/AUTHORITY_FILE_MANIFEST.csv",
    "00_control/BUILD_BASELINE.md",
    "00_control/SAGE_LAB_QA.json",
    "00_control/SAGE_LAB_RESULT.json",
    "00_control/SOURCE_SELECTION.md",
)
READER_ARTIFACTS = (
    "index.html",
    "Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf",
    "Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.epub",
)
RESERVED_ARCHIVE_MEMBER = "BUNDLE_MANIFEST.json"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def include_file(path: Path) -> bool:
    return (
        path.is_file()
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.suffix.casefold() not in {".pyc", ".pyo"}
        and path.name not in {".DS_Store", "BUILD_IN_PROGRESS"}
        and ".quarto_ipynb" not in path.name
    )


def _inside(path: Path, directory: Path) -> bool:
    try:
        path.resolve().relative_to(directory.resolve())
    except ValueError:
        return False
    return True


def _overlap(first: Path, second: Path) -> bool:
    return _inside(first, second) or _inside(second, first)


def _relative(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"jalur berada di luar akar yang diizinkan: {path}") from error


def validate_version(version: str) -> None:
    if VERSION_RE.fullmatch(version) is None:
        raise ValueError(f"versi rilis tidak sah: {version!r}")


def source_files(root: Path = ROOT) -> list[Path]:
    root = root.resolve()
    files = [root / name for name in (*SOURCE_ROOT_FILES, *SOURCE_CONTROL_FILES)]
    for directory_name in SOURCE_DIRECTORIES:
        directory = root / directory_name
        files.extend(path for path in directory.rglob("*") if include_file(path))
    missing = [_relative(path, root) for path in files if not path.is_file()]
    if missing:
        raise RuntimeError(f"berkas sumber wajib hilang: {missing}")
    unique = {path.resolve(): path for path in files}
    result = sorted(unique.values(), key=lambda path: _relative(path, root).casefold())
    relative = [_relative(path, root) for path in result]
    folded = [name.casefold() for name in relative]
    if len(folded) != len(set(folded)):
        raise RuntimeError("jalur sumber bertabrakan setelah case folding")
    return result


def offline_files(output_root: Path) -> list[Path]:
    output_root = output_root.resolve()
    files = [
        path
        for path in output_root.rglob("*")
        if include_file(path) and path.suffix.casefold() != ".zip"
    ]
    if not files:
        raise RuntimeError("keluaran pembaca offline kosong")
    forbidden = [
        _relative(path, output_root)
        for path in files
        if _relative(path, output_root).startswith(("docs/", "release/", "tmp/"))
    ]
    if forbidden:
        raise RuntimeError(
            "pembaca offline memuat pohon kerja/rilis bersarang: "
            f"{sorted(forbidden)[:10]}"
        )
    return sorted(files, key=lambda path: _relative(path, output_root).casefold())


def archive_entries(
    files: Iterable[Path],
    base: Path,
) -> list[tuple[str, bytes]]:
    entries: list[tuple[str, bytes]] = []
    for path in files:
        relative = _relative(path, base)
        if relative.casefold() == RESERVED_ARCHIVE_MEMBER.casefold():
            raise RuntimeError(
                f"anggota sumber memakai nama manifest yang dicadangkan: {relative}"
            )
        entries.append((relative, path.read_bytes()))
    entries.sort(key=lambda entry: entry[0].casefold())
    names = [name.casefold() for name, _ in entries]
    if len(names) != len(set(names)):
        raise RuntimeError("jalur arsip bertabrakan setelah case folding")
    return entries


def _entry_record(name: str, data: bytes) -> dict[str, object]:
    return {"path": name, "bytes": len(data), "sha256": sha256_bytes(data)}


def _file_record(path: Path, base: Path) -> dict[str, object]:
    data = path.read_bytes()
    return _entry_record(_relative(path, base), data)


def write_archive(
    path: Path,
    entries: list[tuple[str, bytes]],
    bundle_kind: str,
    version: str,
    *,
    record_base: Path = ROOT,
) -> dict[str, object]:
    validate_version(version)
    if not entries:
        raise RuntimeError(f"arsip {bundle_kind} tidak boleh kosong")
    folded = [name.casefold() for name, _ in entries]
    if len(folded) != len(set(folded)):
        raise RuntimeError("jalur arsip bertabrakan setelah case folding")
    if RESERVED_ARCHIVE_MEMBER.casefold() in folded:
        raise RuntimeError("nama BUNDLE_MANIFEST.json dicadangkan")

    content_inventory = [_entry_record(name, data) for name, data in entries]
    manifest = {
        "schema": "o002.bundle-manifest.v1",
        "bundle_kind": bundle_kind,
        "version": version,
        "content_entry_count": len(content_inventory),
        "content_bytes": sum(int(record["bytes"]) for record in content_inventory),
        "entries": content_inventory,
    }
    manifest_data = canonical_json(manifest)
    complete_entries = [
        (RESERVED_ARCHIVE_MEMBER, manifest_data),
        *entries,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.unlink(missing_ok=True)
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            strict_timestamps=True,
        ) as archive:
            for name, data in complete_entries:
                info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(
                    info,
                    data,
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )

        with zipfile.ZipFile(temporary, mode="r") as archive:
            names = archive.namelist()
            expected_names = [name for name, _ in complete_entries]
            if names != expected_names or len(names) != len(set(names)):
                raise RuntimeError(f"inventaris ZIP tidak cocok: {path.name}")
            for name, data in complete_entries:
                readback = archive.read(name)
                if len(readback) != len(data) or sha256_bytes(readback) != sha256_bytes(data):
                    raise RuntimeError(f"readback ZIP gagal: {path.name}:{name}")
            embedded = json.loads(archive.read(RESERVED_ARCHIVE_MEMBER))
            if embedded != manifest:
                raise RuntimeError(f"manifest tertanam berubah saat readback: {path.name}")
            bad_member = archive.testzip()
            if bad_member is not None:
                raise RuntimeError(f"CRC ZIP gagal: {path.name}:{bad_member}")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)

    archive_data = path.read_bytes()
    archive_inventory = [
        _entry_record(RESERVED_ARCHIVE_MEMBER, manifest_data),
        *content_inventory,
    ]
    return {
        "bundle_kind": bundle_kind,
        "path": _relative(path, record_base),
        "bytes": len(archive_data),
        "sha256": sha256_bytes(archive_data),
        "entry_count": len(archive_inventory),
        "content_entry_count": len(content_inventory),
        "content_bytes": int(manifest["content_bytes"]),
        "embedded_manifest": archive_inventory[0],
        "entries": archive_inventory,
        "verified_readback": {
            "inventory": True,
            "bytes": True,
            "sha256": True,
            "crc": True,
            "embedded_manifest": True,
        },
    }


def _validate_layout(
    output_root: Path,
    release_root: Path,
    receipt_path: Path,
    root: Path,
) -> None:
    for path in (output_root, release_root, receipt_path):
        _relative(path, root)
    if _overlap(output_root, release_root):
        raise ValueError("direktori output dan release tidak boleh bertumpang tindih")
    if _inside(receipt_path, output_root) or _inside(receipt_path, release_root):
        raise ValueError("receipt bundle harus berada di luar output dan release")

    protected_directories = [root / name for name in SOURCE_DIRECTORIES]
    protected_files = [root / name for name in (*SOURCE_ROOT_FILES, *SOURCE_CONTROL_FILES)]
    for candidate, label in ((release_root, "release"), (output_root, "output")):
        if any(_overlap(candidate, directory) for directory in protected_directories):
            raise ValueError(f"direktori {label} bertumpang tindih dengan sumber")
        if any(candidate.resolve() == path.resolve() for path in protected_files):
            raise ValueError(f"direktori {label} bertabrakan dengan berkas sumber")
    if any(_inside(receipt_path, directory) for directory in protected_directories):
        raise ValueError("receipt bundle tidak boleh berada di direktori sumber")
    if any(receipt_path.resolve() == path.resolve() for path in protected_files):
        raise ValueError("receipt bundle tidak boleh menggantikan berkas sumber")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Create deterministic editable-source and offline-reader ZIPs."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--output-root", type=Path, default=ROOT / "output")
    parser.add_argument("--release-root", type=Path, default=ROOT / "release")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    validate_version(args.version)
    output_root = args.output_root.resolve()
    release_root = args.release_root.resolve()
    receipt_path = args.receipt.resolve()
    _validate_layout(output_root, release_root, receipt_path, ROOT)
    if not output_root.is_dir():
        raise FileNotFoundError(output_root)

    stem = args.version.replace(".", "-")
    source_archive = release_root / f"O002_B80_ID_EDITABLE_SOURCE_{stem}.zip"
    offline_archive = release_root / f"O002_B80_ID_OFFLINE_READER_{stem}.zip"
    reader_artifacts = []
    for relative in READER_ARTIFACTS:
        artifact = output_root / relative
        if not artifact.is_file():
            raise FileNotFoundError(f"artefak pembaca wajib hilang: {artifact}")
        reader_artifacts.append(_file_record(artifact, ROOT))

    source_content = archive_entries(source_files(), ROOT)
    offline_content = archive_entries(offline_files(output_root), output_root)
    source_record = write_archive(
        source_archive,
        source_content,
        "editable_source",
        args.version,
    )
    offline_record = write_archive(
        offline_archive,
        offline_content,
        "offline_reader",
        args.version,
    )

    receipt = {
        "schema": "o002.bundle-receipt.v1",
        "successful": True,
        "version": args.version,
        "tag": f"v{args.version}",
        "reader_artifacts": reader_artifacts,
        "archives": [source_record, offline_record],
        "deterministic_zip_timestamp": "2026-08-22T00:00:00",
        "self_reference_policy": {
            "receipt_excluded_from_archives": True,
            "release_directory_excluded_from_offline_archive": True,
            "embedded_manifest_excludes_its_own_digest": True,
        },
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_data = canonical_json(receipt)
    temporary = receipt_path.with_name(f".{receipt_path.name}.tmp")
    temporary.write_bytes(receipt_data)
    if json.loads(temporary.read_bytes()) != receipt:
        temporary.unlink(missing_ok=True)
        raise RuntimeError("readback receipt bundle gagal")
    temporary.replace(receipt_path)
    print(
        f"release bundles verified: {source_record['entry_count']} source entries, "
        f"{offline_record['entry_count']} offline entries"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
