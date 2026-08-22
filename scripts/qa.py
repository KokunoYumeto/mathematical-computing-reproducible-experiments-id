from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Sequence

from jsonschema import Draft202012Validator

import backend_truth_qa
from pdf_visual_receipt import verify_receipt as verify_pdf_receipt
from update_backend import validate_epub, validate_html


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
CONTROL = ROOT / "00_control"
PDF_NAME = "Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf"
EPUB_NAME = "Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.epub"
REQUIRED_UNIT_IDS = [
    "o002.p01",
    "o002.p02",
    *[f"o002.u{number:02d}" for number in range(1, 13)],
]
REQUIRED_LICENSES = (
    "LICENSE-TEXT.md",
    "LICENSE-CODE.md",
    "THIRD_PARTY.md",
    "RUNTIME-LICENSES.md",
    "LICENSE-RUNTIME-APACHE-2.0.txt",
)
PACKAGED_IDENTITIES = (
    "backend/catalog.json",
    "00_control/SOURCE_SELECTION.md",
    "00_control/SAGE_LAB_QA.json",
    "00_control/SAGE_LAB_RESULT.json",
    "environment/python-lock.txt",
    "environment/PYTHON_ENVIRONMENT_RECEIPT.json",
    "environment/sage-ubuntu22.04-dpkg-lock.txt",
    "environment/SAGE_ENVIRONMENT_RECEIPT.json",
    "requirements-build.txt",
    "source/notebooks/o002-p01-clean-kernel.ipynb",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def load_json(path: Path, label: str) -> dict[str, object]:
    require(path.is_file(), f"{label} tidak ditemukan: {path.relative_to(ROOT)}")
    document = json.loads(path.read_text(encoding="utf-8"))
    require(isinstance(document, dict), f"{label} bukan objek JSON")
    return document


def validate_file_record(record: object, path: Path, label: str) -> None:
    require(isinstance(record, dict), f"rekaman {label} tidak lengkap")
    relative = path.relative_to(ROOT).as_posix()
    require(record.get("path") == relative, f"jalur rekaman {label} salah")
    require(path.is_file(), f"berkas terikat {label} hilang")
    require(record.get("bytes") == path.stat().st_size, f"ukuran rekaman {label} salah")
    require(record.get("sha256") == sha256(path), f"hash rekaman {label} salah")


def validate_environment_receipt(
    receipt_path: Path,
    *,
    schema: str,
    lock_path: Path,
    expected_packages: int,
) -> dict[str, object]:
    receipt = load_json(receipt_path, receipt_path.name)
    require(receipt.get("schema") == schema, f"skema {receipt_path.name} salah")
    require(receipt.get("matches_runtime") is True, f"runtime {receipt_path.name} tidak cocok")
    lock_record = receipt.get("lock")
    require(isinstance(lock_record, dict), f"rekaman lock hilang: {receipt_path.name}")
    validate_file_record(lock_record, lock_path, f"lock {receipt_path.name}")
    package_count = receipt.get("package_count", lock_record.get("installed_package_count"))
    require(package_count == expected_packages, f"jumlah paket {receipt_path.name} salah")
    return receipt


def validate_html_static_receipt(path: Path) -> dict[str, object]:
    receipt = load_json(path, "HTML_STATIC_QA.json")
    require(receipt.get("schema") == "o002.html-static-qa.v1", "skema QA HTML statis salah")
    require(receipt.get("successful") is True, "QA HTML statis tidak lulus")
    checks = receipt.get("checks")
    require(isinstance(checks, dict) and checks, "QA HTML statis tidak memuat pemeriksaan")
    require(all(value is True for value in checks.values()), "QA HTML statis memuat pemeriksaan gagal")
    inventory = receipt.get("output_inventory")
    require(isinstance(inventory, list) and len(inventory) >= 15, "inventaris HTML tidak memuat 15 halaman")
    for record in inventory:
        require(isinstance(record, dict), "rekaman inventaris HTML tidak sah")
        relative = str(record.get("path", ""))
        target = (OUTPUT / relative).resolve()
        try:
            target.relative_to(OUTPUT.resolve())
        except ValueError as error:
            raise RuntimeError(f"jalur inventaris HTML keluar dari output: {relative}") from error
        require(target.is_file(), f"halaman inventaris HTML hilang: {relative}")
        require(record.get("bytes") == target.stat().st_size and record.get("sha256") == sha256(target), f"identitas inventaris HTML salah: {relative}")
    counts = receipt.get("counts")
    require(isinstance(counts, dict), "jumlah QA HTML hilang")
    require(int(counts.get("pages", 0)) >= 15, "QA HTML tidak mencakup index dan 14 unit")
    require(int(counts.get("mathml_elements", 0)) > 0, "MathML HTML tidak terbukti")
    return receipt


def validate_epub_receipt(path: Path, epub: Path) -> dict[str, object]:
    receipt = load_json(path, path.name)
    require(receipt.get("schema") == "o002.epub-qa.v1", "skema QA EPUB salah")
    require(receipt.get("successful") is True, "QA EPUB tidak lulus")
    validate_file_record(receipt.get("epub"), epub, "EPUB")
    validate_epub(receipt)
    return receipt


def validate_sage_receipt(path: Path) -> dict[str, object]:
    receipt = load_json(path, path.name)
    require(receipt.get("schema") == "o002.sage-lab-qa.v1", "skema QA lab Sage salah")
    require(receipt.get("successful") is True, "lab Sage tidak lulus")
    for key, target in (
        ("result", OUTPUT / "unit05-sage-results.json"),
        ("source", ROOT / "source/code/unit05_sage_lab.py"),
        ("test_source", ROOT / "tests/test_unit05_sage.py"),
    ):
        validate_file_record(receipt.get(key), target, f"Sage {key}")
    runtime = receipt.get("runtime")
    require(isinstance(runtime, dict) and runtime.get("sage") == "9.5", "runtime Sage bukan 9.5")
    validate_file_record(runtime.get("environment_lock"), ROOT / "environment/sage-ubuntu22.04-dpkg-lock.txt", "lock Sage")
    validate_file_record(runtime.get("environment_receipt"), ROOT / "environment/SAGE_ENVIRONMENT_RECEIPT.json", "receipt lingkungan Sage")
    tests = receipt.get("tests")
    require(isinstance(tests, dict), "hasil tes Sage hilang")
    require(int(tests.get("tests_run", 0)) >= 7 and tests.get("failures") == 0 and tests.get("errors") == 0, "suite Sage tidak membuktikan tujuh tes lulus")
    return receipt


def validate_notebook(path: Path) -> None:
    notebook = load_json(path, "notebook P01")
    require(notebook.get("nbformat") == 4, "format notebook P01 bukan v4")
    metadata = notebook.get("metadata")
    require(isinstance(metadata, dict), "metadata notebook hilang")
    kernelspec = metadata.get("kernelspec")
    require(isinstance(kernelspec, dict) and kernelspec.get("name") == "o002-frozen", "notebook tidak memakai kernel beku")
    cells = notebook.get("cells")
    require(isinstance(cells, list) and cells, "notebook P01 kosong")
    code_cells = [cell for cell in cells if isinstance(cell, dict) and cell.get("cell_type") == "code"]
    require(code_cells, "notebook P01 tidak memuat sel kode")
    require(all(cell.get("execution_count") is None and cell.get("outputs") == [] for cell in code_cells), "notebook P01 membawa keadaan eksekusi tersembunyi")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Candidate or Final O002 reader build.")
    parser.add_argument("--mode", choices=("Candidate", "Final"), default="Candidate")
    args = parser.parse_args(argv)
    mode = args.mode

    require(backend_truth_qa.main() == 0, "QA kebenaran backend gagal")
    schema_path = ROOT / "backend/catalog.schema.json"
    catalog_path = ROOT / "backend/catalog.json"
    schema = load_json(schema_path, "skema backend")
    catalog = load_json(catalog_path, "katalog backend")
    schema_errors = sorted(Draft202012Validator(schema).iter_errors(catalog), key=lambda error: list(error.path))
    require(not schema_errors, "backend tidak cocok dengan skema: " + "; ".join(error.message for error in schema_errors))
    require([unit["id"] for unit in catalog["units"]] == REQUIRED_UNIT_IDS, "urutan 14 unit salah")
    require(len(catalog["exercises"]) == 75, "backend tidak memuat tepat 75 latihan")
    require(catalog["cursor"]["standalone_edition_complete"] is True, "status edisi historis hilang")
    if mode == "Final":
        require(catalog["cursor"]["b80_curriculum_complete"] is True, "build Final memerlukan B80 lengkap")
        require(catalog["architecture"]["status"] == "complete", "build Final memerlukan arsitektur lengkap")
        require(catalog["planned_release"]["status"] in {"b80_complete", "published"}, "build Final memerlukan status rilis B80 lengkap")

    output_catalog = OUTPUT / "backend/catalog.json"
    require(output_catalog.is_file() and output_catalog.read_bytes() == catalog_path.read_bytes(), "katalog backend keluaran tidak identik")
    index = OUTPUT / "index.html"
    require(index.is_file(), "output/index.html tidak ditemukan")
    index_html = index.read_text(encoding="utf-8")
    require(re.search(r'<html[^>]+lang="id"', index_html) is not None, "bahasa index HTML bukan id")
    require("CC BY-SA 4.0" in index_html and "MIT" in index_html, "pemberitahuan lisensi hilang dari index")

    external_runtime_pattern = re.compile(r'<(?:script|link|img|source|video|audio)\b[^>]*(?:src|href)="https?://', re.IGNORECASE)
    mathml_count = 0
    for unit in catalog["units"]:
        source_path = Path(str(unit["reader_path"]))
        require(source_path.parts[:2] == ("source", "units"), f"jalur pembaca tidak aman: {source_path}")
        html_path = OUTPUT / source_path.with_suffix(".html")
        require(html_path.is_file(), f"halaman unit hilang: {unit['id']}")
        html = html_path.read_text(encoding="utf-8")
        require(re.search(r'<html[^>]+lang="id"', html) is not None, f"bahasa HTML salah: {unit['id']}")
        require(not external_runtime_pattern.search(html), f"sumber daya runtime eksternal: {unit['id']}")
        require("mathjax" not in html.casefold(), f"MathJax masih dirujuk: {unit['id']}")
        html_ids = re.findall(r'(?:^|[\s<])id="([^"]+)"', html)
        require(len(html_ids) == len(set(html_ids)), f"ID HTML duplikat: {unit['id']}")
        for anchor in [*unit["sections"], *unit["exercises"]]:
            require(f'id="{anchor}"' in html, f"ID backend tidak dirender: {anchor}")
        mathml_count += len(re.findall(r"<math(?:\s|>)", html))
    require(mathml_count > 0, "MathML tidak ditemukan pada 14 halaman unit")

    pdf = OUTPUT / PDF_NAME
    epub = OUTPUT / EPUB_NAME
    require(pdf.is_file() and pdf.read_bytes()[:5] == b"%PDF-", "PDF pembaca tidak sah")
    require(epub.is_file() and epub.read_bytes()[:4] == b"PK\x03\x04", "EPUB pembaca tidak sah")
    require(len(list(OUTPUT.glob("*.pdf"))) == 1, "keluaran harus memuat tepat satu PDF")
    require(len(list(OUTPUT.glob("*.epub"))) == 1, "keluaran harus memuat tepat satu EPUB")

    for license_name in REQUIRED_LICENSES:
        require((OUTPUT / license_name).is_file(), f"berkas lisensi pembaca hilang: {license_name}")
    require("LICENSE-RUNTIME-APACHE-2.0.txt" in (OUTPUT / "RUNTIME-LICENSES.md").read_text(encoding="utf-8"), "inventaris runtime tidak menautkan salinan Apache-2.0")
    for relative in PACKAGED_IDENTITIES:
        source = ROOT / relative
        packaged = OUTPUT / relative
        require(source.is_file() and packaged.is_file(), f"rekaman paket hilang: {relative}")
        require(source.read_bytes() == packaged.read_bytes(), f"rekaman paket tidak identik: {relative}")
    validate_notebook(ROOT / "source/notebooks/o002-p01-clean-kernel.ipynb")

    result_paths = [
        OUTPUT / "p01-results.json",
        OUTPUT / "primer02-demo/manifest.json",
        *[OUTPUT / f"unit{number:02d}-results.json" for number in (1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12)],
        OUTPUT / "unit04/unit04-manifest.json",
        OUTPUT / "unit05-sage-results.json",
    ]
    results = {path.relative_to(OUTPUT).as_posix(): load_json(path, path.name) for path in result_paths}
    require(all(isinstance(payload.get("schema"), str) for payload in results.values()), "artefak hasil tanpa skema")
    for relative in (
        "primer02-demo/values.txt",
        "primer02-demo/measurements.csv",
        "primer02-demo/summary.json",
        "unit04/unit04-data.csv",
        "unit04/unit04-figure.svg",
        "unit04/unit04-alt.txt",
    ):
        require((OUTPUT / relative).is_file(), f"artefak eksperimen hilang: {relative}")
    unit04 = results["unit04/unit04-manifest.json"]
    require(unit04.get("all_model_values_within_uncertainty") is True, "hasil plotting Unit 4 gagal")
    artifacts = unit04.get("artifacts")
    require(isinstance(artifacts, dict), "manifest Unit 4 tidak memuat artefak")
    for name, digest in artifacts.items():
        target = OUTPUT / "unit04" / str(name)
        require(target.is_file() and sha256(target) == digest, f"manifest Unit 4 tidak mengikat {name}")
    require(results["unit12-results.json"].get("verified") is True, "verifikasi paket Unit 12 gagal")

    python_environment = validate_environment_receipt(
        OUTPUT / "PYTHON_ENVIRONMENT_QA.json",
        schema="o002.python-environment.v1",
        lock_path=ROOT / "environment/python-lock.txt",
        expected_packages=95,
    )
    validate_environment_receipt(
        OUTPUT / "SAGE_ENVIRONMENT_QA.json",
        schema="o002.sage-environment.v1",
        lock_path=ROOT / "environment/sage-ubuntu22.04-dpkg-lock.txt",
        expected_packages=1064,
    )
    packages = python_environment.get("packages")
    require(isinstance(packages, list), "inventaris paket Python hilang")
    versions = {str(record["name"]): str(record["version"]) for record in packages if isinstance(record, dict)}
    require(versions.get("scipy") == "1.15.2", "versi SciPy beku berubah")
    unit06 = results["unit06-results.json"]
    unit11 = results["unit11-results.json"]
    require(unit06.get("runtime", {}).get("scipy") == versions["scipy"], "hasil Unit 6 tidak mengikat SciPy beku")
    require(unit11.get("bisection_scipy_comparison", {}).get("scipy_version") == versions["scipy"], "hasil Unit 11 tidak mengikat SciPy beku")

    source_receipt = load_json(OUTPUT / "SOURCE_QA.json", "SOURCE_QA.json")
    require(source_receipt.get("schema") == "o002.source-qa.v2" and source_receipt.get("successful") is True, "QA sumber tidak lulus")
    require(source_receipt.get("unit_triplets") == 14 and source_receipt.get("errors") == 0, "QA sumber tidak mencakup 14 triplet")
    test_receipt = load_json(OUTPUT / "TEST_QA.json", "TEST_QA.json")
    require(test_receipt.get("schema") == "o002.test-qa.v1" and test_receipt.get("successful") is True, "suite tes tidak lulus")
    require(int(test_receipt.get("tests_run", 0)) >= 150 and test_receipt.get("failures") == 0 and test_receipt.get("errors") == 0, "suite tes tidak mencakup batas 14-unit")
    require(test_receipt.get("command") == "python -B scripts/run_tests.py --receipt tmp/build-receipts/TEST_QA.json", "invokasi suite tes tidak tepat")
    toolchain = load_json(OUTPUT / "TOOLCHAIN_QA.json", "TOOLCHAIN_QA.json")
    require(toolchain.get("schema") == "o002.toolchain-qa.v1" and toolchain.get("matches_expected") is True, "toolchain beku tidak cocok")
    require(isinstance(toolchain.get("quarto_pandoc"), str) and toolchain.get("quarto_pandoc"), "versi Pandoc bawaan Quarto tidak direkam")
    sage_receipt = validate_sage_receipt(OUTPUT / "SAGE_LAB_QA.json")
    html_static = validate_html_static_receipt(OUTPUT / "HTML_STATIC_QA.json")
    epub_receipt = validate_epub_receipt(OUTPUT / "EPUB_QA.json", epub)

    final_evidence: dict[str, object] = {"required": mode == "Final"}
    if mode == "Final":
        browser_path = CONTROL / "HTML_BROWSER_QA.json"
        browser = load_json(browser_path, "HTML_BROWSER_QA.json")
        require(browser.get("schema") == "o002.html-browser-qa.v1", "skema receipt browser salah")
        validate_html(browser)
        pdf_receipt_path = CONTROL / "PDF_VISUAL_QA.json"
        pdf_receipt = load_json(pdf_receipt_path, "PDF_VISUAL_QA.json")
        require(pdf_receipt.get("schema") == "o002.pdf-visual-qa.v1", "skema receipt visual PDF salah")
        verify_pdf_receipt(pdf_receipt_path, pdf)
        output_pdf_receipt = OUTPUT / "PDF_VISUAL_QA.json"
        require(output_pdf_receipt.is_file() and output_pdf_receipt.read_bytes() == pdf_receipt_path.read_bytes(), "receipt visual PDF keluaran tidak identik")
        durable_epub_path = CONTROL / "EPUB_QA.json"
        durable_epub = validate_epub_receipt(durable_epub_path, epub)
        require(durable_epub_path.read_bytes() == (OUTPUT / "EPUB_QA.json").read_bytes(), "receipt EPUB durable dan keluaran berbeda")
        final_evidence.update({"html_browser": browser, "pdf_visual": pdf_receipt, "epub": durable_epub})

    public_files = sorted(
        (path for path in OUTPUT.rglob("*") if path.is_file() and path.name != "BUILD_QA.json"),
        key=lambda item: item.relative_to(ROOT).as_posix().casefold(),
    )
    for path in public_files:
        data = path.read_bytes()
        require(b"C:\\Users\\" not in data and b"C:/Users/" not in data and b"file:///C:/Users/" not in data, f"jalur profil lokal bocor: {path.relative_to(OUTPUT)}")

    checks = {
        "ordered_14_unit_reader": True,
        "exact_75_exercises": True,
        "backend_schema_truth_and_references": True,
        "html_static_offline_mathml_links_ids": True,
        "pdf_signature": True,
        "epub_structure_accessibility": True,
        "notebook_clean_kernel": True,
        "python_and_sage_locks": True,
        "sage_local_execution": True,
        "scipy_version_bound": True,
        "experiment_artifact_closure": True,
        "licenses_and_provenance_packaged": True,
        "local_profile_paths_absent": True,
        "determinism_may_follow_first_final_build": True,
    }
    if mode == "Final":
        checks["final_visual_browser_receipts"] = True

    receipt = {
        "schema": "o002.build-qa.v2",
        "mode": mode,
        "successful": True,
        "source_qa": source_receipt,
        "tests": test_receipt,
        "toolchain": toolchain,
        "python_environment": python_environment,
        "sage_lab": sage_receipt,
        "html_static": html_static,
        "epub": epub_receipt,
        "final_evidence": final_evidence,
        "backend": {
            "path": "backend/catalog.json",
            "bytes": catalog_path.stat().st_size,
            "sha256": sha256(catalog_path),
            "b80_curriculum_complete": catalog["cursor"]["b80_curriculum_complete"],
        },
        "checks": checks,
        "mode_gates": {
            "final_visual_browser_receipts": "pass" if mode == "Final" else "not_required",
            "build_determinism_receipt": "may_follow_first_final_build",
            "publication_receipt": "external_to_build",
        },
        "files": [
            {
                "path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
            for path in public_files
        ],
    }
    (OUTPUT / "BUILD_QA.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"{mode} build QA passed: 14 units, 75 exercises, {len(public_files)} public files")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"build QA failed: {error}", file=sys.stderr)
        raise SystemExit(1)
