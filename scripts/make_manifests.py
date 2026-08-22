from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROL = ROOT / "00_control"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def regular_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file():
            files.append(root)
        elif root.is_dir():
            files.extend(
                path
                for path in root.rglob("*")
                if path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix.casefold() != ".pyc"
            )
        else:
            raise FileNotFoundError(root)
    relative = [path.relative_to(ROOT).as_posix() for path in files]
    folded = [path.casefold() for path in relative]
    if len(folded) != len(set(folded)):
        raise RuntimeError("case-fold path collision in manifest scope")
    return sorted(files, key=lambda path: path.relative_to(ROOT).as_posix().casefold())


def write_manifest(path: Path, files: list[Path]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["path", "bytes", "sha256"])
        for item in files:
            writer.writerow([item.relative_to(ROOT).as_posix(), item.stat().st_size, sha256(item)])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-output", action="store_true")
    args = parser.parse_args()

    authority = regular_files([ROOT / "authority"])
    source_roots = [
        ROOT / "README.md",
        ROOT / "LICENSE-TEXT.md",
        ROOT / "LICENSE-CODE.md",
        ROOT / "THIRD_PARTY.md",
        ROOT / "RUNTIME-LICENSES.md",
        ROOT / "LICENSE-RUNTIME-APACHE-2.0.txt",
        ROOT / "requirements-build.txt",
        ROOT / "_quarto.yml",
        ROOT / "styles.css",
        ROOT / "index.qmd",
        ROOT / "00_control" / "SOURCE_SELECTION.md",
        ROOT / "00_control" / "COVERAGE_AND_OVERLAP.csv",
        ROOT / "00_control" / "PDF_VISUAL_QA.json",
        ROOT / "00_control" / "PDF_VISUAL_RENDER_MANIFEST.csv",
        ROOT / "source",
        ROOT / "scripts",
        ROOT / "tests",
        ROOT / "backend",
        ROOT / "build-support",
    ]
    source = regular_files(source_roots)
    write_manifest(CONTROL / "AUTHORITY_FILE_MANIFEST.csv", authority)
    write_manifest(CONTROL / "SOURCE_FILE_MANIFEST.csv", source)
    if args.include_output:
        write_manifest(CONTROL / "OUTPUT_FILE_MANIFEST.csv", regular_files([ROOT / "output"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
