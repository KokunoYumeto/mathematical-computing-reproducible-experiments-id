from __future__ import annotations

import argparse
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
UNIT_FILES = [
    "01-komputasi-bukti.qmd",
    "02-objek-fungsi.qmd",
    "03-array-vektorisasi.qmd",
    "04-visualisasi-integritas.qmd",
    "05-eksak-simbolik-sage.qmd",
    "06-titik-mengambang-stabilitas.qmd",
    "07-rancangan-eksperimen.qmd",
    "08-pengujian-validasi.qmd",
    "09-data-konfigurasi-provenans.qmd",
    "10-otomasi-pipa.qmd",
    "11-eksperimen-numerik.qmd",
    "12-proyek-akhir.qmd",
]


def parse_unit(number: int, filename: str) -> tuple[dict[str, object], list[dict[str, str]]]:
    path = ROOT / "source" / "units" / filename
    text = path.read_text(encoding="utf-8")
    title_match = re.search(r'^title:\s*"([^"]+)"\s*$', text, flags=re.MULTILINE)
    identifier_match = re.search(r'^identifier:\s*(o002\.u\d{2})\s*$', text, flags=re.MULTILINE)
    if not title_match or not identifier_match:
        raise RuntimeError(f"front matter tidak lengkap: {path}")
    expected_id = f"o002.u{number:02d}"
    if identifier_match.group(1) != expected_id:
        raise RuntimeError(f"ID unit tidak cocok: {path}")

    sections = re.findall(r'\{#(sec-o002-u\d{2}[a-z0-9-]*)\}', text)
    exercises = re.findall(r'\{#(ex-o002-u\d{2}-\d{2})\}', text)
    expected_exercises = [f"ex-o002-u{number:02d}-{item:02d}" for item in range(1, 6)]
    if exercises != expected_exercises:
        raise RuntimeError(f"urutan latihan tidak cocok: {path}")
    if len(sections) != len(set(sections)):
        raise RuntimeError(f"ID seksi tidak unik: {path}")

    code_matches = sorted((ROOT / "source" / "code").glob(f"unit{number:02d}_*.py"))
    if len(code_matches) != 1:
        raise RuntimeError(f"diharapkan tepat satu skrip Unit {number}: {code_matches}")
    test_path = ROOT / "tests" / f"test_unit{number:02d}.py"
    if not test_path.is_file():
        raise RuntimeError(f"tes unit hilang: {test_path}")

    text_component = f"cmp-o002-u{number:02d}-text"
    code_component = f"cmp-o002-u{number:02d}-code"
    unit = {
        "id": expected_id,
        "title": title_match.group(1),
        "status": "complete",
        "reader_path": path.relative_to(ROOT).as_posix(),
        "sections": sections,
        "exercises": exercises,
        "components": [text_component, code_component],
    }
    components = [
        {
            "id": text_component,
            "kind": "reader_text",
            "source": "src-o002-original",
            "license": "CC BY-SA 4.0",
            "path": path.relative_to(ROOT).as_posix(),
        },
        {
            "id": code_component,
            "kind": "software",
            "source": "src-o002-original",
            "license": "MIT",
            "path": code_matches[0].relative_to(ROOT).as_posix(),
        },
    ]
    return unit, components


def build_catalog(qa_status: str, pdf_visual_status: str) -> dict[str, object]:
    units: list[dict[str, object]] = []
    components: list[dict[str, str]] = []
    for number, filename in enumerate(UNIT_FILES, start=1):
        unit, unit_components = parse_unit(number, filename)
        units.append(unit)
        components.extend(unit_components)

    relations: list[dict[str, str]] = []
    for number in range(1, len(units)):
        relations.append(
            {"type": "precedes", "from": f"o002.u{number:02d}", "to": f"o002.u{number + 1:02d}"}
        )
    for unit in units:
        for component in unit["components"]:  # type: ignore[index]
            relations.append({"type": "uses_component", "from": unit["id"], "to": component})  # type: ignore[index]

    return {
        "schema_version": "o002.backend.v1",
        "language": "id-ID",
        "course": {
            "id": "B80",
            "project_id": "O002",
            "title": "Komputasi Matematis dan Eksperimen yang Dapat Direproduksi",
            "prerequisite": "A30",
        },
        "sources": [
            {
                "id": "src-o002-original",
                "title": "O002 original Indonesian coursebook",
                "role": "original",
                "license": "CC BY-SA 4.0 text; MIT code",
                "identity": "local independently authored source",
                "used_in_current_units": True,
            },
            {
                "id": "src-o002-walls",
                "title": "Mathematical Python",
                "role": "bounded_donor",
                "license": "CC BY-NC-SA 4.0; separate/unclear component rights retained",
                "identity": "commit 0687916182ab3ddc9e922d4a6eb603609ba91c36; tree b66a9c79aa7144a75d3f83ba53bba4ff8961f91b",
                "used_in_current_units": False,
            },
            {
                "id": "src-o002-rse",
                "title": "Research Software Engineering with Python",
                "role": "bounded_donor",
                "license": "CC BY 4.0 text; MIT code; excluded components remain separate",
                "identity": "commit 62217e6606842ab9752fcf8e73954d1eb4a3cf07; tree f570f30bb8ace202550c474e81eb3414e8976be5",
                "used_in_current_units": False,
            },
            {
                "id": "src-o002-spl",
                "title": "Scientific Python Lectures",
                "role": "comparison_only",
                "license": "CC BY 4.0",
                "identity": "comparison freeze 817a97d8d9a26eeb4e735a402420cd34dd7e89fc; archive not yet admitted",
                "used_in_current_units": False,
            },
        ],
        "components": components,
        "units": units,
        "relations": relations,
        "qa": [
            {
                "id": "qa-o002-source-structure",
                "status": qa_status,
                "evidence": "12 units; stable IDs; five hint-and-solution exercises per unit",
            },
            {
                "id": "qa-o002-tests",
                "status": qa_status,
                "evidence": "complete standard-library/scientific-Python test suite at final boundary",
            },
            {
                "id": "qa-o002-reader-build",
                "status": qa_status,
                "evidence": "Quarto HTML and LuaLaTeX PDF build at final boundary",
            },
            {
                "id": "qa-o002-pdf-visual",
                "status": pdf_visual_status,
                "evidence": "all final PDF pages rendered and inspected",
            },
            {
                "id": "qa-o002-audio",
                "status": "not_applicable",
                "evidence": "no audio or interactive widget surface in this edition",
            },
        ],
        "cursor": {
            "last_complete_unit": "o002.u12",
            "next_unit": None,
            "boundary": "complete 12-unit id-ID edition",
            "edition_complete": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-status", choices=("pending", "pass"), default="pending")
    parser.add_argument(
        "--pdf-visual-status", choices=("pending", "pass"), default="pending"
    )
    args = parser.parse_args()
    output = ROOT / "backend" / "catalog.json"
    output.write_text(
        json.dumps(
            build_catalog(args.qa_status, args.pdf_visual_status),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
