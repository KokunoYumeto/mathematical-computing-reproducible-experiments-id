from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "00_control"
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
REQUIRED_UNIT_FILES = (
    "source/units/p01-menjalankan-eksperimen-python.qmd",
    "source/units/p02-kontrol-koleksi-fungsi-modul-berkas.qmd",
    "source/units/01-komputasi-bukti.qmd",
    "source/units/02-objek-fungsi.qmd",
    "source/units/03-array-vektorisasi.qmd",
    "source/units/04-visualisasi-integritas.qmd",
    "source/units/05-eksak-simbolik-sage.qmd",
    "source/units/06-titik-mengambang-stabilitas.qmd",
    "source/units/07-rancangan-eksperimen.qmd",
    "source/units/08-pengujian-validasi.qmd",
    "source/units/09-data-konfigurasi-provenans.qmd",
    "source/units/10-otomasi-pipa.qmd",
    "source/units/11-eksperimen-numerik.qmd",
    "source/units/12-proyek-akhir.qmd",
)
REQUIRED_EXPANDED_SOURCE_FILES = (
    *REQUIRED_UNIT_FILES,
    "source/code/primer01_execution.py",
    "source/code/primer02_control_files.py",
    "source/code/unit05_sage_lab.py",
    "source/notebooks/o002-p01-clean-kernel.ipynb",
    "tests/test_primer01.py",
    "tests/test_primer02.py",
    "tests/test_unit05_sage.py",
    "environment/python-lock.txt",
    "environment/PYTHON_ENVIRONMENT_RECEIPT.json",
    "environment/sage-ubuntu22.04-dpkg-lock.txt",
    "environment/SAGE_ENVIRONMENT_RECEIPT.json",
    "00_control/SAGE_LAB_QA.json",
    "00_control/SAGE_LAB_RESULT.json",
    "backend/catalog.json",
    "backend/catalog.schema.json",
)
REQUIRED_OUTPUT_FILES = (
    "output/index.html",
    "output/Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf",
    "output/Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.epub",
    "output/backend/catalog.json",
    "output/environment/python-lock.txt",
    "output/environment/PYTHON_ENVIRONMENT_RECEIPT.json",
    "output/environment/sage-ubuntu22.04-dpkg-lock.txt",
    "output/environment/SAGE_ENVIRONMENT_RECEIPT.json",
    "output/00_control/SAGE_LAB_QA.json",
    "output/00_control/SAGE_LAB_RESULT.json",
    "output/source/notebooks/o002-p01-clean-kernel.ipynb",
    *(f"output/{path.removesuffix('.qmd')}.html" for path in REQUIRED_UNIT_FILES),
)
TRANSIENT_NAMES = {".DS_Store", "BUILD_IN_PROGRESS"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(path: Path, base: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"jalur manifest berada di luar lane: {path}") from error


def include_file(path: Path) -> bool:
    return (
        path.is_file()
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
        and path.suffix.casefold() not in {".pyc", ".pyo"}
        and path.name not in TRANSIENT_NAMES
        and ".quarto_ipynb" not in path.name
    )


def regular_files(roots: list[Path], *, base: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            if include_file(root):
                files.append(root)
        elif root.is_dir():
            files.extend(path for path in root.rglob("*") if include_file(path))
        else:
            raise FileNotFoundError(root)
    resolved = [path.resolve() for path in files]
    relative = [_relative(path, base) for path in resolved]
    folded = [path.casefold() for path in relative]
    if len(folded) != len(set(folded)):
        raise RuntimeError("case-fold path collision or duplicate in manifest scope")
    return [
        path
        for _, path in sorted(
            zip(relative, resolved), key=lambda item: item[0].casefold()
        )
    ]


def _require_paths(files: list[Path], required: Sequence[str], label: str) -> None:
    inventory = {_relative(path) for path in files}
    missing = sorted(set(required) - inventory, key=str.casefold)
    if missing:
        raise RuntimeError(f"{label} tidak lengkap; berkas wajib hilang: {missing}")


def validate_expanded_source(files: list[Path]) -> None:
    _require_paths(files, REQUIRED_EXPANDED_SOURCE_FILES, "manifest sumber 14 unit")
    actual_units = {
        relative
        for path in files
        if (relative := _relative(path)).startswith("source/units/")
        and path.suffix.casefold() == ".qmd"
    }
    expected_units = set(REQUIRED_UNIT_FILES)
    if actual_units != expected_units:
        raise RuntimeError(
            "census unit sumber bukan tepat 14; "
            f"hilang={sorted(expected_units - actual_units)}, "
            f"tambahan={sorted(actual_units - expected_units)}"
        )


def validate_expanded_output(files: list[Path]) -> None:
    _require_paths(files, REQUIRED_OUTPUT_FILES, "manifest output 14 unit")
    nested_release_trees = {
        relative
        for path in files
        if (relative := _relative(path)).startswith(
            ("output/docs/", "output/release/", "output/tmp/")
        )
    }
    if nested_release_trees:
        raise RuntimeError(
            "output memuat salinan pohon kerja/rilis yang dilarang: "
            f"{sorted(nested_release_trees)[:10]}"
        )
    actual_unit_pages = {
        relative
        for path in files
        if (relative := _relative(path)).startswith("output/source/units/")
        and path.suffix.casefold() == ".html"
    }
    expected_unit_pages = {
        f"output/{path.removesuffix('.qmd')}.html" for path in REQUIRED_UNIT_FILES
    }
    if actual_unit_pages != expected_unit_pages:
        raise RuntimeError(
            "census halaman unit output bukan tepat 14; "
            f"hilang={sorted(expected_unit_pages - actual_unit_pages)}, "
            f"tambahan={sorted(actual_unit_pages - expected_unit_pages)}"
        )


def write_manifest(path: Path, files: list[Path], *, base: Path = ROOT) -> None:
    resolved_path = path.resolve()
    if resolved_path in {item.resolve() for item in files}:
        raise ValueError(f"manifest tidak boleh mencantumkan dirinya sendiri: {path}")
    _relative(resolved_path, base)
    rows = [
        [_relative(item, base), str(item.stat().st_size), sha256(item)]
        for item in files
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256"])
        writer.writerows(rows)
    with temporary.open("r", encoding="utf-8", newline="") as handle:
        readback = list(csv.reader(handle))
    if readback != [["path", "bytes", "sha256"], *rows]:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"readback manifest gagal: {path}")
    temporary.replace(path)


def source_inventory() -> list[Path]:
    roots = [ROOT / name for name in (*SOURCE_ROOT_FILES, *SOURCE_CONTROL_FILES)]
    roots.extend(ROOT / name for name in SOURCE_DIRECTORIES)
    return regular_files(roots)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-output", action="store_true")
    args = parser.parse_args(argv)

    authority = regular_files([ROOT / "authority"])
    write_manifest(CONTROL / "AUTHORITY_FILE_MANIFEST.csv", authority)

    source = source_inventory()
    validate_expanded_source(source)
    write_manifest(CONTROL / "SOURCE_FILE_MANIFEST.csv", source)
    if args.include_output:
        output = regular_files([ROOT / "output"])
        validate_expanded_output(output)
        write_manifest(CONTROL / "OUTPUT_FILE_MANIFEST.csv", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
