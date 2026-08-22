from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

from jsonschema import Draft202012Validator

from pdf_visual_receipt import verify_receipt


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    index = OUTPUT / "index.html"
    source_receipt_path = OUTPUT / "SOURCE_QA.json"
    test_receipt_path = OUTPUT / "TEST_QA.json"
    toolchain_receipt_path = OUTPUT / "TOOLCHAIN_QA.json"
    pdf_visual_receipt_path = OUTPUT / "PDF_VISUAL_QA.json"
    pdf_visual_control_path = ROOT / "00_control" / "PDF_VISUAL_QA.json"
    schema_path = ROOT / "backend" / "catalog.schema.json"
    catalog_path = ROOT / "backend" / "catalog.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(catalog), key=lambda error: list(error.path))
    require(not errors, "backend tidak cocok dengan skema: " + "; ".join(error.message for error in errors))

    source_ids = [source["id"] for source in catalog["sources"]]
    component_ids = [component["id"] for component in catalog["components"]]
    unit_ids = [unit["id"] for unit in catalog["units"]]
    require(len(source_ids) == len(set(source_ids)), "ID sumber backend tidak unik")
    require(len(component_ids) == len(set(component_ids)), "ID komponen backend tidak unik")
    require(len(unit_ids) == len(set(unit_ids)), "ID unit backend tidak unik")
    require(len(catalog["units"]) == 12, f"diharapkan 12 unit, ditemukan {len(catalog['units'])}")
    require(all(len(unit["exercises"]) == 5 for unit in catalog["units"]), "setiap unit harus memuat lima latihan")
    require(sum(len(unit["exercises"]) for unit in catalog["units"]) == 60, "backend tidak memuat tepat 60 latihan")
    require(catalog["cursor"].get("edition_complete") is True, "backend belum menandai edisi lengkap")
    require(catalog["cursor"].get("last_complete_unit") == "o002.u12", "cursor backend bukan Unit 12")
    require(catalog["cursor"].get("next_unit") is None, "backend masih memuat unit berikutnya")
    qa_statuses = {record["id"]: record["status"] for record in catalog["qa"]}
    expected_qa_statuses = {
        "qa-o002-source-structure": "pass",
        "qa-o002-tests": "pass",
        "qa-o002-reader-build": "pass",
        "qa-o002-pdf-visual": "pass",
        "qa-o002-audio": "not_applicable",
    }
    require(qa_statuses == expected_qa_statuses, "status QA backend belum merupakan batas final")

    units: list[Path] = []
    results: list[Path] = []
    extra_artifacts: list[Path] = []
    for number, unit_record in enumerate(catalog["units"], start=1):
        source_path = Path(unit_record["reader_path"])
        require(source_path.parts[:2] == ("source", "units"), f"jalur pembaca tidak aman: {source_path}")
        unit_path = OUTPUT / source_path.with_suffix(".html")
        units.append(unit_path)
        if number == 4:
            unit04_files = [
                OUTPUT / "unit04" / "unit04-data.csv",
                OUTPUT / "unit04" / "unit04-figure.svg",
                OUTPUT / "unit04" / "unit04-alt.txt",
                OUTPUT / "unit04" / "unit04-manifest.json",
            ]
            extra_artifacts.extend(unit04_files[:-1])
            results.append(unit04_files[-1])
        else:
            results.append(OUTPUT / f"unit{number:02d}-results.json")

    pdfs = sorted(OUTPUT.glob("*.pdf"))
    require(index.is_file(), "output/index.html tidak ditemukan")
    require(len(pdfs) == 1, f"diharapkan tepat satu PDF, ditemukan {len(pdfs)}")
    require(pdfs[0].read_bytes().startswith(b"%PDF-"), "tanda tangan PDF tidak sah")
    require(pdf_visual_receipt_path.is_file(), "PDF_VISUAL_QA.json tidak ditemukan")
    require(pdf_visual_control_path.is_file(), "receipt visual PDF kontrol tidak ditemukan")
    require(
        pdf_visual_receipt_path.read_bytes() == pdf_visual_control_path.read_bytes(),
        "receipt visual PDF keluaran tidak identik dengan receipt kontrol",
    )
    verify_receipt(pdf_visual_receipt_path, pdfs[0])
    pdf_visual_receipt = json.loads(pdf_visual_receipt_path.read_text(encoding="utf-8"))

    for component in catalog["components"]:
        require(component["source"] in source_ids, f"sumber komponen tidak dikenal: {component['id']}")
        require((ROOT / component["path"]).is_file(), f"jalur komponen hilang: {component['path']}")
    mathml_elements = 0
    external_runtime_pattern = re.compile(
        r'<(?:script|link|img|source|video|audio)\b[^>]*(?:src|href)="https?://',
        re.IGNORECASE,
    )
    for unit_record, unit_path in zip(catalog["units"], units, strict=True):
        require(unit_path.is_file(), f"halaman unit tidak ditemukan: {unit_path.name}")
        require(unit_record["reader_path"] == unit_path.relative_to(OUTPUT).as_posix().replace(".html", ".qmd"),
                f"jalur pembaca backend tidak cocok: {unit_record['id']}")
        require(set(unit_record["components"]).issubset(component_ids), f"komponen unit tidak dikenal: {unit_record['id']}")
        html = unit_path.read_text(encoding="utf-8")
        require(not external_runtime_pattern.search(html), f"sumber daya runtime eksternal: {unit_path.name}")
        require("mathjax" not in html.casefold(), f"MathJax eksternal masih dirujuk: {unit_path.name}")
        mathml_elements += len(re.findall(r"<math(?:\s|>)", html))
        require(re.search(r'<html[^>]+lang="id"', html) is not None, f"lang HTML bukan id: {unit_path.name}")
        html_ids = re.findall(r'(?:^|[\s<])id="([^"]+)"', html)
        require(len(html_ids) == len(set(html_ids)), f"ID HTML duplikat: {unit_path.name}")
        for anchor in [*unit_record["sections"], *unit_record["exercises"]]:
            require(f'id="{anchor}"' in html, f"ID backend tidak dirender: {anchor}")
    index_html = index.read_text(encoding="utf-8")
    require(not external_runtime_pattern.search(index_html), "sumber daya runtime eksternal: index.html")
    require(mathml_elements > 0, "MathML tidak ditemukan pada pembaca HTML")
    for license_name in (
        "LICENSE-TEXT.md",
        "LICENSE-CODE.md",
        "THIRD_PARTY.md",
        "RUNTIME-LICENSES.md",
        "LICENSE-RUNTIME-APACHE-2.0.txt",
    ):
        require((OUTPUT / license_name).is_file(), f"berkas lisensi pembaca hilang: {license_name}")
    require("CC BY-SA 4.0" in index_html and "MIT" in index_html, "pemberitahuan lisensi tidak ada di pembaca")
    require("RUNTIME-LICENSES.md" in index_html, "tautan lisensi runtime tidak ada di pembaca")
    require(
        "LICENSE-RUNTIME-APACHE-2.0.txt"
        in (OUTPUT / "RUNTIME-LICENSES.md").read_text(encoding="utf-8"),
        "inventaris runtime tidak menautkan salinan lokal Apache-2.0",
    )
    packaged_records = (
        (catalog_path, OUTPUT / "backend" / "catalog.json"),
        (ROOT / "00_control" / "SOURCE_SELECTION.md", OUTPUT / "00_control" / "SOURCE_SELECTION.md"),
    )
    for source_record, packaged_record in packaged_records:
        require(packaged_record.is_file(), f"rekaman provenans tidak dikemas: {packaged_record.relative_to(OUTPUT)}")
        require(
            source_record.read_bytes() == packaged_record.read_bytes(),
            f"rekaman provenans keluaran tidak identik: {packaged_record.relative_to(OUTPUT)}",
        )

    for result in [*results, *extra_artifacts]:
        require(result.is_file(), f"artefak eksperimen tidak ditemukan: {result}")
    result_payloads = [json.loads(path.read_text(encoding="utf-8")) for path in results]
    for number, payload in enumerate(result_payloads, start=1):
        require(isinstance(payload.get("schema"), str), f"skema hasil Unit {number} hilang")

    unit01 = result_payloads[0]
    require(unit01["exact_arithmetic"]["result"] == "3/10", "hasil eksak salah")
    require(unit01["floating_arithmetic"]["isclose"] is True, "pemeriksaan float gagal")
    require(unit01["finite_check"]["proves_universal_claim"] is False, "batas bukti hilang")
    unit02 = result_payloads[1]
    require(unit02["mean"] == "5/12", "rata-rata eksak Unit 2 salah")
    require(unit02["scale"]["input_unchanged"] is True, "fungsi Unit 2 mengubah masukan")
    require(unit02["scale"]["length_preserved"] is True, "invarian panjang Unit 2 gagal")
    require(result_payloads[11]["verified"] is True, "verifikasi paket Unit 12 gagal")

    require(source_receipt_path.is_file(), "SOURCE_QA.json tidak ditemukan")
    require(test_receipt_path.is_file(), "TEST_QA.json tidak ditemukan")
    require(toolchain_receipt_path.is_file(), "TOOLCHAIN_QA.json tidak ditemukan")
    source_receipt = json.loads(source_receipt_path.read_text(encoding="utf-8"))
    test_receipt = json.loads(test_receipt_path.read_text(encoding="utf-8"))
    toolchain_receipt = json.loads(toolchain_receipt_path.read_text(encoding="utf-8"))
    require(source_receipt.get("schema") == "o002.source-qa.v1", "skema receipt QA sumber salah")
    require(source_receipt.get("successful") is True, "QA sumber tidak lulus")
    require(source_receipt.get("unit_triplets") == 12, "jumlah triplet unit pada QA sumber salah")
    require(test_receipt.get("schema") == "o002.test-qa.v1", "skema receipt tes salah")
    require(test_receipt.get("successful") is True, "suite tes tidak lulus")
    require(test_receipt.get("tests_run", 0) > 0, "receipt tes tidak memuat tes")
    require(test_receipt.get("failures") == 0, "receipt tes memuat kegagalan")
    require(test_receipt.get("errors") == 0, "receipt tes memuat galat")
    require(
        test_receipt.get("command")
        == "python -B scripts/run_tests.py --receipt tmp/build-receipts/TEST_QA.json",
        "receipt tes tidak merekam invokasi build yang sebenarnya",
    )
    require(toolchain_receipt.get("schema") == "o002.toolchain-qa.v1", "skema receipt toolchain salah")
    require(toolchain_receipt.get("matches_expected") is True, "toolchain tidak cocok dengan versi beku")

    public_files = sorted(
        (path for path in OUTPUT.rglob("*") if path.is_file() and path.name != "BUILD_QA.json"),
        key=lambda item: item.relative_to(ROOT).as_posix().casefold(),
    )
    for path in public_files:
        data = path.read_bytes()
        require(b"C:\\Users\\" not in data, f"jalur profil lokal bocor: {path.name}")
        require(b"C:/Users/" not in data, f"jalur profil lokal bocor: {path.name}")
        require(b"file:///C:/Users/" not in data, f"URI profil lokal bocor: {path.name}")

    receipt = {
        "schema": "o002.build-qa.v1",
        "source_qa": source_receipt,
        "tests": test_receipt,
        "toolchain": toolchain_receipt,
        "pdf_visual_qa": pdf_visual_receipt,
        "files": [
            {"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(public_files, key=lambda item: item.relative_to(ROOT).as_posix().casefold())
        ],
        "checks": {
            "backend_schema_and_references": True,
            "complete_12_unit_reader": True,
            "html_ids_unique_per_document": True,
            "html_lang_id": True,
            "html_runtime_resources_local": True,
            "html_mathml_offline": True,
            "reader_license_notice_and_files": True,
            "reader_provenance_records_packaged": True,
            "runtime_component_inventory": True,
            "frozen_toolchain_versions": True,
            "test_receipt_invocation_exact": True,
            "pdf_all_pages_visual_pass": True,
            "stable_reader_ids": True,
            "experiment_json": True,
            "unit04_artifact_closure": True,
            "unit12_package_verification": True,
            "local_profile_paths_absent": True,
        },
    }
    (OUTPUT / "BUILD_QA.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
