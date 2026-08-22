from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BUNDLE_TOOL_SCRIPT = Path(__file__).resolve().with_name("make_release_bundles.py")
_BUNDLE_TOOL_SPEC = importlib.util.spec_from_file_location(
    "o002_bundle_validation_tools", BUNDLE_TOOL_SCRIPT
)
if _BUNDLE_TOOL_SPEC is None or _BUNDLE_TOOL_SPEC.loader is None:
    raise RuntimeError("bundle tooling could not be loaded for freshness validation")
BUNDLE_TOOLS = importlib.util.module_from_spec(_BUNDLE_TOOL_SPEC)
_BUNDLE_TOOL_SPEC.loader.exec_module(BUNDLE_TOOLS)
RELEASE_VERSION = "2026.08.22.1"
RELEASE_TAG = "v2026.08.22.1"
RELEASE_RECORD_ID = 22053905
RELEASE_DOI = "10.5281/zenodo.22053905"
RELEASE_ARTIFACT_PATHS = {
    "art-o002-reader-html": "output/index.html",
    "art-o002-reader-pdf": "output/Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf",
    "art-o002-reader-epub": "output/Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.epub",
    "art-o002-source-archive": "release/O002_B80_ID_EDITABLE_SOURCE_2026-08-22-1.zip",
    "art-o002-offline-bundle": "release/O002_B80_ID_OFFLINE_READER_2026-08-22-1.zip",
}
EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS = frozenset(
    {"art-o002-source-archive", "art-o002-offline-bundle"}
)


@dataclass(frozen=True)
class UnitSpec:
    unit_id: str
    reader: str
    code: str
    test: str
    standalone_status: str
    curriculum_status: str


UNIT_SPECS = [
    UnitSpec(
        "o002.p01",
        "source/units/p01-menjalankan-eksperimen-python.qmd",
        "source/code/primer01_execution.py",
        "tests/test_primer01.py",
        "not_applicable",
        "complete",
    ),
    UnitSpec(
        "o002.p02",
        "source/units/p02-kontrol-koleksi-fungsi-modul-berkas.qmd",
        "source/code/primer02_control_files.py",
        "tests/test_primer02.py",
        "not_applicable",
        "complete",
    ),
    UnitSpec("o002.u01", "source/units/01-komputasi-bukti.qmd", "source/code/unit01_experiment.py", "tests/test_unit01.py", "complete", "complete"),
    UnitSpec("o002.u02", "source/units/02-objek-fungsi.qmd", "source/code/unit02_objects.py", "tests/test_unit02.py", "complete", "complete"),
    UnitSpec("o002.u03", "source/units/03-array-vektorisasi.qmd", "source/code/unit03_arrays.py", "tests/test_unit03.py", "complete", "complete"),
    UnitSpec("o002.u04", "source/units/04-visualisasi-integritas.qmd", "source/code/unit04_visualization.py", "tests/test_unit04.py", "complete", "complete"),
    UnitSpec("o002.u05", "source/units/05-eksak-simbolik-sage.qmd", "source/code/unit05_symbolic.py", "tests/test_unit05.py", "complete", "repair_required"),
    UnitSpec("o002.u06", "source/units/06-titik-mengambang-stabilitas.qmd", "source/code/unit06_floating.py", "tests/test_unit06.py", "complete", "complete"),
    UnitSpec("o002.u07", "source/units/07-rancangan-eksperimen.qmd", "source/code/unit07_experiment_design.py", "tests/test_unit07.py", "complete", "complete"),
    UnitSpec("o002.u08", "source/units/08-pengujian-validasi.qmd", "source/code/unit08_validation.py", "tests/test_unit08.py", "complete", "complete"),
    UnitSpec("o002.u09", "source/units/09-data-konfigurasi-provenans.qmd", "source/code/unit09_provenance.py", "tests/test_unit09.py", "complete", "complete"),
    UnitSpec("o002.u10", "source/units/10-otomasi-pipa.qmd", "source/code/unit10_pipeline.py", "tests/test_unit10.py", "complete", "complete"),
    UnitSpec("o002.u11", "source/units/11-eksperimen-numerik.qmd", "source/code/unit11_numerical.py", "tests/test_unit11.py", "complete", "complete"),
    UnitSpec("o002.u12", "source/units/12-proyek-akhir.qmd", "source/code/unit12_capstone.py", "tests/test_unit12.py", "complete", "complete"),
]

REQUIRED_UNIT_IDS = [spec.unit_id for spec in UNIT_SPECS]
EXERCISE_HEADING_RE = re.compile(
    r"^#{2,6}\s+(.+?)\s+\{#(ex-o002-(?:p|u)\d{2}-"
    r"(?:\d{2}|[a-z][a-z0-9-]*\d{2}))\}\s*$",
    re.MULTILINE,
)
CHECK_CALLOUT_RE = re.compile(
    r'title="(?:Pemeriksaan mandiri|Cek yang dapat dijalankan)"'
)
CHECK_LABEL_RE = re.compile(r"#\|\s*label:\s*(chk-o002-[a-z0-9-]+)")
SOLUTION_LABEL_RE = re.compile(r"#\|\s*label:\s*(sol-o002-[a-z0-9-]+)")
REQUIRED_EXECUTABLE_EXERCISES = {
    *[f"ex-o002-p01-{number:02d}" for number in range(1, 6)],
    *[f"ex-o002-p02-{number:02d}" for number in range(1, 6)],
    "ex-o002-u04-m01",
    "ex-o002-u05-sage-01",
    "ex-o002-u05-sage-02",
    "ex-o002-u06-scipy-01",
    "ex-o002-u11-s01",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def receipt_record(
    receipt_id: str,
    kind: str,
    relative: str,
    document: dict[str, object],
    *,
    binding: str = "bound",
) -> dict[str, object]:
    path = ROOT / relative
    record: dict[str, object] = {
        "id": receipt_id,
        "kind": kind,
        "path": relative,
        "schema": str(document["schema"]),
        "status": "pass",
        "binding": binding,
    }
    if binding == "bound":
        record.update({"bytes": path.stat().st_size, "sha256": sha256(path)})
    elif binding != "external":
        raise ValueError(f"unknown receipt binding: {binding}")
    return record


def nested_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from nested_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from nested_dicts(child)


def nested_leaves(value: object, prefix: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield from nested_leaves(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from nested_leaves(child, f"{prefix}[{index}]")
    else:
        yield prefix.casefold(), value


def bound_record(document: dict[str, object], relative: str) -> dict[str, object] | None:
    aliases = {relative, Path(relative).name}
    for record in nested_dicts(document):
        candidate = record.get("path", record.get("local_path", record.get("filename")))
        if candidate in aliases:
            return record
    return None


def validate_local_binding(document: dict[str, object], relative: str) -> dict[str, object]:
    record = bound_record(document, relative)
    if record is None:
        raise RuntimeError(f"receipt does not bind required path: {relative}")
    path = ROOT / relative
    if not path.is_file():
        raise RuntimeError(f"receipt-bound artifact is absent: {relative}")
    if record.get("bytes") != path.stat().st_size or record.get("sha256") != sha256(path):
        raise RuntimeError(f"receipt-bound artifact identity mismatch: {relative}")
    return record


def require_success(document: dict[str, object], relative: str) -> None:
    if document.get("successful") is not True:
        raise RuntimeError(f"receipt is not explicitly successful: {relative}")


def validate_named_check(
    document: dict[str, object],
    label: str,
    aliases: tuple[tuple[str, ...], ...],
) -> None:
    leaves = list(nested_leaves(document))
    for alias in aliases:
        for path, value in leaves:
            normalized = re.sub(r"[^a-z0-9]+", "", path)
            if all(token in normalized for token in alias):
                if value is True or str(value).casefold() in {"pass", "passed", "success", "successful"}:
                    return
                if value == 0 and any(token in normalized for token in ("error", "failure", "violation")):
                    return
    raise RuntimeError(f"receipt lacks passing {label} check")


def validate_output_binding(document: dict[str, object]) -> None:
    for record in nested_dicts(document):
        relative = record.get("path", record.get("local_path"))
        if not isinstance(relative, str) or not relative.startswith("output/"):
            continue
        path = ROOT / relative
        if (
            path.is_file()
            and record.get("bytes") == path.stat().st_size
            and record.get("sha256") == sha256(path)
        ):
            return
    raise RuntimeError("HTML browser receipt lacks a valid output manifest/page binding")


def read_optional_receipt(
    *,
    receipt_id: str,
    kind: str,
    relative: str,
    expected_schema: str,
    validator,
    binding: str = "bound",
) -> tuple[dict[str, object], dict[str, object]] | None:
    path = ROOT / relative
    if not path.is_file():
        return None
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != expected_schema:
        raise RuntimeError(
            f"receipt schema mismatch: {relative}; expected {expected_schema}, "
            f"found {document.get('schema')}"
        )
    validator(document)
    return document, receipt_record(
        receipt_id, kind, relative, document, binding=binding
    )


def validate_sage_evidence() -> tuple[list[dict[str, object]], dict[str, object]]:
    result_relative = "00_control/SAGE_LAB_RESULT.json"
    qa_relative = "00_control/SAGE_LAB_QA.json"
    result_path = ROOT / result_relative
    qa_path = ROOT / qa_relative
    if not result_path.is_file() or not qa_path.is_file():
        raise FileNotFoundError("completed Sage lab receipts are missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    if result.get("schema") != "o002.unit05.sage-lab.v1":
        raise RuntimeError("Sage result schema mismatch")
    if qa.get("schema") != "o002.sage-lab-qa.v1" or qa.get("successful") is not True:
        raise RuntimeError("Sage QA receipt is not successful")
    validate_local_binding(qa, result_relative)
    for relative in (
        "environment/sage-ubuntu22.04-dpkg-lock.txt",
        "environment/SAGE_ENVIRONMENT_RECEIPT.json",
        "source/code/unit05_sage_lab.py",
        "tests/test_unit05_sage.py",
    ):
        validate_local_binding(qa, relative)
    tests = qa.get("tests")
    runtime = qa.get("runtime")
    if not isinstance(tests, dict) or (
        tests.get("tests_run"), tests.get("failures"), tests.get("errors")
    ) != (7, 0, 0):
        raise RuntimeError("Sage QA does not prove seven passing tests")
    if not isinstance(runtime, dict) or runtime.get("sage") != "9.5":
        raise RuntimeError("Sage QA runtime is not Sage 9.5")
    result_runtime = result.get("runtime")
    if not isinstance(result_runtime, dict) or result_runtime.get("sage") != "9.5":
        raise RuntimeError("Sage result runtime is not Sage 9.5")
    return [
        receipt_record("receipt-o002-sage-lab-result", "lab_result", result_relative, result),
        receipt_record("receipt-o002-sage-lab-qa", "lab_qa", qa_relative, qa),
    ], result


def validate_bundle(document: dict[str, object]) -> None:
    require_success(document, "00_control/BUNDLE_QA.json")
    if document.get("version") != RELEASE_VERSION or document.get("tag") != RELEASE_TAG:
        raise RuntimeError("bundle receipt is not bound to the planned version and tag")
    reader_artifacts = document.get("reader_artifacts")
    archives = document.get("archives")
    if not isinstance(reader_artifacts, list) or len(reader_artifacts) != 3:
        raise RuntimeError("bundle receipt must bind exactly three reader artifacts")
    if not isinstance(archives, list) or len(archives) != 2:
        raise RuntimeError("bundle receipt must bind exactly two archives")
    for relative in RELEASE_ARTIFACT_PATHS.values():
        validate_local_binding(document, relative)
    if {record.get("bundle_kind") for record in archives if isinstance(record, dict)} != {
        "editable_source",
        "offline_reader",
    }:
        raise RuntimeError("bundle receipt archive roles are incomplete")
    for record in archives:
        if not isinstance(record, dict):
            raise RuntimeError("bundle archive record is invalid")
        checks = record.get("verified_readback")
        if not isinstance(checks, dict) or set(checks) != {
            "inventory",
            "bytes",
            "sha256",
            "crc",
            "embedded_manifest",
        } or any(value is not True for value in checks.values()):
            raise RuntimeError("bundle archive readback checks are incomplete")
        entries = record.get("entries")
        if (
            not isinstance(entries, list)
            or record.get("entry_count") != len(entries)
            or record.get("content_entry_count") != len(entries) - 1
        ):
            raise RuntimeError("bundle archive inventory counts are inconsistent")
    def live_inventory(paths, base: Path) -> list[dict[str, object]]:
        records = []
        for path in paths:
            relative = path.resolve().relative_to(base.resolve()).as_posix()
            records.append(
                {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
        return sorted(records, key=lambda item: str(item["path"]).casefold())

    by_kind = {
        str(record["bundle_kind"]): record
        for record in archives
        if isinstance(record, dict)
    }
    expected_by_kind = {
        "editable_source": live_inventory(BUNDLE_TOOLS.source_files(ROOT), ROOT),
        "offline_reader": live_inventory(
            BUNDLE_TOOLS.offline_files(ROOT / "output"), ROOT / "output"
        ),
    }
    for kind, expected in expected_by_kind.items():
        record = by_kind[kind]
        entries = record["entries"]
        content = [
            entry
            for entry in entries
            if isinstance(entry, dict)
            and entry.get("path") != BUNDLE_TOOLS.RESERVED_ARCHIVE_MEMBER
        ]
        if content != expected:
            raise RuntimeError(
                f"bundle {kind} is stale or differs from the complete live inventory"
            )
        if record.get("content_bytes") != sum(int(item["bytes"]) for item in expected):
            raise RuntimeError(f"bundle {kind} content byte total is stale")
    policy = document.get("self_reference_policy")
    if not isinstance(policy, dict) or not policy or any(
        value is not True for value in policy.values()
    ):
        raise RuntimeError("bundle self-reference policy is absent or incomplete")


def validate_determinism(document: dict[str, object]) -> None:
    require_success(document, "00_control/BUILD_DETERMINISM_QA.json")
    if document.get("clean_build_count") != 2:
        raise RuntimeError("determinism receipt must prove exactly two clean builds")
    comparisons = document.get("comparisons")
    if not isinstance(comparisons, list) or {
        record.get("kind") for record in comparisons if isinstance(record, dict)
    } != {"source", "output"}:
        raise RuntimeError("determinism receipt must compare source and output manifests")
    witness_paths: set[str] = set()
    for comparison in comparisons:
        if not isinstance(comparison, dict) or any(
            comparison.get(key) is not True
            for key in ("byte_identical", "row_count_identical", "total_bytes_identical")
        ):
            raise RuntimeError("determinism comparison contains a non-passing invariant")
        first = comparison.get("first")
        second = comparison.get("second")
        if not isinstance(first, dict) or not isinstance(second, dict):
            raise RuntimeError("determinism comparison lacks witness records")
        for record in (first, second):
            relative = record.get("path")
            if not isinstance(relative, str):
                raise RuntimeError("determinism witness path is invalid")
            validate_local_binding(document, relative)
            witness_paths.add(relative)
            if not isinstance(record.get("row_count"), int) or record["row_count"] < 1:
                raise RuntimeError("determinism witness row count is invalid")
        if first["row_count"] != second["row_count"] or first["total_bytes"] != second["total_bytes"]:
            raise RuntimeError("determinism witness summaries disagree")
    if len(witness_paths) != 4:
        raise RuntimeError("determinism receipt must bind four distinct witness paths")
    checks = document.get("checks")
    if not isinstance(checks, dict) or not checks or any(value is not True for value in checks.values()):
        raise RuntimeError("determinism receipt checks are incomplete")


def validate_html(document: dict[str, object]) -> None:
    require_success(document, "00_control/HTML_BROWSER_QA.json")
    validate_output_binding(document)
    viewports = document.get("viewports")
    if not isinstance(viewports, dict):
        raise RuntimeError("HTML browser receipt lacks viewport records")
    for name in ("desktop", "narrow"):
        record = viewports.get(name)
        if not isinstance(record, dict) or not any(
            value is True or str(value).casefold() in {"pass", "passed", "success", "successful"}
            for _, value in nested_leaves(record)
        ):
            raise RuntimeError(f"HTML browser receipt lacks passing {name} viewport")
    checks = document.get("checks")
    required_checks = {
        "centered_reflow",
        "keyboard_navigation",
        "focus_visibility",
        "contrast",
        "console_clean",
        "local_resources",
        "responsive_tables_code_math",
    }
    if (
        not isinstance(checks, dict)
        or not required_checks.issubset(checks)
        or any(checks[key] is not True for key in required_checks)
    ):
        raise RuntimeError("HTML browser receipt checks are incomplete")


def validate_pdf(document: dict[str, object]) -> None:
    review = document.get("review")
    if not isinstance(review, dict) or review.get("result") != "pass":
        raise RuntimeError("PDF visual receipt is not a pass")
    validate_local_binding(document, RELEASE_ARTIFACT_PATHS["art-o002-reader-pdf"])


def validate_epub(document: dict[str, object]) -> None:
    require_success(document, "00_control/EPUB_QA.json")
    validate_local_binding(document, RELEASE_ARTIFACT_PATHS["art-o002-reader-epub"])
    checks = document.get("checks")
    if not isinstance(checks, dict) or not checks:
        raise RuntimeError("EPUB receipt lacks checks")
    leaf_checks = [value for _, value in nested_leaves(checks)]
    if not leaf_checks or any(value is not True for value in leaf_checks):
        raise RuntimeError("EPUB receipt contains a non-passing check")


def validate_publication(document: dict[str, object]) -> None:
    require_success(document, "00_control/PUBLICATION_RECEIPT_FINAL.json")
    for key, value in nested_leaves(document):
        if any(secret in key for secret in ("token", "password", "authorization", "credential", "secret")):
            raise RuntimeError("publication receipt contains a credential-shaped field")
        if isinstance(value, str) and re.search(r"(?:Bearer\s+|access_token=)", value, flags=re.IGNORECASE):
            raise RuntimeError("publication receipt contains credential material")
    for relative in RELEASE_ARTIFACT_PATHS.values():
        record = bound_record(document, relative)
        if record is None:
            raise RuntimeError(f"publication receipt lacks anonymous readback: {relative}")
        path = ROOT / relative
        url = record.get("public_url", record.get("url"))
        if not isinstance(url, str) or not url.startswith("https://"):
            raise RuntimeError(f"publication readback lacks public URL: {relative}")
        if not path.is_file() or record.get("bytes") != path.stat().st_size or record.get("sha256") != sha256(path):
            raise RuntimeError(f"publication readback identity mismatch: {relative}")


def evidence_state() -> dict[str, object]:
    receipts: list[dict[str, object]] = []
    present: dict[str, bool] = {}
    receipt_ids: dict[str, str] = {}
    errors: dict[str, str] = {}
    try:
        sage_receipts, _ = validate_sage_evidence()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        present["sage"] = False
        errors["sage"] = str(error)
    else:
        present["sage"] = True
        receipts.extend(sage_receipts)
        receipt_ids["sage_result"] = "receipt-o002-sage-lab-result"
        receipt_ids["sage_qa"] = "receipt-o002-sage-lab-qa"
    specs = [
        ("bundle", "receipt-o002-bundle", "bundle_qa", "00_control/BUNDLE_QA.json", "o002.bundle-receipt.v1", validate_bundle, "external"),
        ("determinism", "receipt-o002-build-determinism", "build_determinism_qa", "00_control/BUILD_DETERMINISM_QA.json", "o002.build-determinism.v1", validate_determinism, "external"),
        ("html", "receipt-o002-html-browser", "html_browser_qa", "00_control/HTML_BROWSER_QA.json", "o002.html-browser-qa.v1", validate_html, "bound"),
        ("pdf", "receipt-o002-pdf-visual", "pdf_visual_qa", "00_control/PDF_VISUAL_QA.json", "o002.pdf-visual-qa.v1", validate_pdf, "bound"),
        ("epub", "receipt-o002-epub", "epub_qa", "00_control/EPUB_QA.json", "o002.epub-qa.v1", validate_epub, "external"),
        ("publication", "receipt-o002-publication-final", "publication_qa", "00_control/PUBLICATION_RECEIPT_FINAL.json", "o002.publication-final.v1", validate_publication, "external"),
    ]
    for key, receipt_id, kind, relative, schema, validator, binding in specs:
        try:
            loaded = read_optional_receipt(
                receipt_id=receipt_id,
                kind=kind,
                relative=relative,
                expected_schema=schema,
                validator=validator,
                binding=binding,
            )
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
            loaded = None
            errors[key] = str(error)
        present[key] = loaded is not None
        if loaded is not None:
            _, record = loaded
            receipts.append(record)
            receipt_ids[key] = receipt_id
    return {
        "present": present,
        "receipt_ids": receipt_ids,
        "receipts": receipts,
        "errors": errors,
    }


def component_id(unit_id: str, kind: str) -> str:
    return f"cmp-o002-{unit_id.split('.')[1]}-{kind}"


def parse_unit(spec: UnitSpec) -> tuple[dict[str, object], list[dict[str, str]], list[dict[str, object]]]:
    path = ROOT / spec.reader
    code_path = ROOT / spec.code
    test_path = ROOT / spec.test
    for required_path in (path, code_path, test_path):
        if not required_path.is_file():
            raise FileNotFoundError(required_path)

    text = path.read_text(encoding="utf-8")
    title_match = re.search(r'^title:\s*"([^"]+)"\s*$', text, flags=re.MULTILINE)
    identifier_match = re.search(
        r"^identifier:\s*(o002\.(?:p|u)\d{2})\s*$", text, flags=re.MULTILINE
    )
    if not title_match or not identifier_match:
        raise RuntimeError(f"front matter tidak lengkap: {path}")
    if identifier_match.group(1) != spec.unit_id:
        raise RuntimeError(
            f"ID unit tidak cocok: {path}; expected {spec.unit_id}, "
            f"found {identifier_match.group(1)}"
        )

    token = spec.unit_id.split(".")[1]
    sections = re.findall(rf"\{{#(sec-o002-{token}[a-z0-9-]*)\}}", text)
    if not sections or len(sections) != len(set(sections)):
        raise RuntimeError(f"ID seksi hilang atau tidak unik: {path}")

    matches = list(EXERCISE_HEADING_RE.finditer(text))
    exercises: list[dict[str, object]] = []
    for sequence, match in enumerate(matches, start=1):
        exercise_id = match.group(2)
        if not exercise_id.startswith(f"ex-o002-{token}-"):
            raise RuntimeError(f"latihan unit lain ditemukan di {path}: {exercise_id}")
        segment_end = matches[sequence].start() if sequence < len(matches) else len(text)
        segment = text[match.end() : segment_end]
        hint_count = segment.count('title="Petunjuk"')
        solution_count = segment.count('title="Jawaban dan solusi"')
        if hint_count != 1 or solution_count != 1:
            raise RuntimeError(
                f"{exercise_id} requires one hint and one full solution; "
                f"found hint={hint_count}, solution={solution_count}"
            )
        check_labels = CHECK_LABEL_RE.findall(segment)
        solution_labels = SOLUTION_LABEL_RE.findall(segment)
        executable = bool(CHECK_CALLOUT_RE.search(segment) or check_labels)
        if exercise_id in REQUIRED_EXECUTABLE_EXERCISES and not executable:
            raise RuntimeError(f"executable check missing: {exercise_id}")
        suffix = exercise_id.removeprefix(f"ex-o002-{token}-")
        curriculum_status = (
            "prerequisite_deferred"
            if exercise_id in {"ex-o002-u11-03", "ex-o002-u11-04", "ex-o002-u11-05"}
            else "complete"
        )
        exercises.append(
            {
                "id": exercise_id,
                "unit": spec.unit_id,
                "sequence": sequence,
                "kind": "core" if suffix.isdigit() else "mastery",
                "title": match.group(1).strip(),
                "source_path": spec.reader,
                "curriculum_status": curriculum_status,
                "hint": {
                    "status": "complete",
                    "source_anchor": exercise_id,
                    "label": "Petunjuk",
                },
                "check": {
                    "status": "executable" if executable else "not_present",
                    "source_anchor": exercise_id,
                    "label": check_labels[0] if check_labels else (
                        "Cek yang dapat dijalankan" if executable else None
                    ),
                },
                "solution": {
                    "status": "complete",
                    "source_anchor": exercise_id,
                    "label": solution_labels[0] if solution_labels else "Jawaban dan solusi",
                },
            }
        )

    baseline = [f"ex-o002-{token}-{number:02d}" for number in range(1, 6)]
    actual_ids = [exercise["id"] for exercise in exercises]
    numeric_ids = [
        exercise_id
        for exercise_id in actual_ids
        if exercise_id.removeprefix(f"ex-o002-{token}-").isdigit()
    ]
    if numeric_ids != baseline:
        raise RuntimeError(f"lima latihan dasar tidak utuh atau tidak berurutan: {path}")

    components = [
        {
            "id": component_id(spec.unit_id, "text"),
            "kind": "reader_text",
            "source": "src-o002-original",
            "license": "CC BY-SA 4.0",
            "path": spec.reader,
        },
        {
            "id": component_id(spec.unit_id, "code"),
            "kind": "software",
            "source": "src-o002-original",
            "license": "MIT",
            "path": spec.code,
        },
        {
            "id": component_id(spec.unit_id, "test"),
            "kind": "test",
            "source": "src-o002-original",
            "license": "MIT",
            "path": spec.test,
        },
    ]
    unit = {
        "id": spec.unit_id,
        "title": title_match.group(1),
        "standalone_status": spec.standalone_status,
        "curriculum_status": spec.curriculum_status,
        "reader_path": spec.reader,
        "sections": sections,
        "exercises": actual_ids,
        "components": [component["id"] for component in components],
    }
    return unit, components, exercises


def artifact_records(evidence: dict[str, object]) -> list[dict[str, object]]:
    present = evidence["present"]
    receipt_ids = evidence["receipt_ids"]
    assert isinstance(present, dict) and isinstance(receipt_ids, dict)
    bundle_current = present.get("bundle") is True

    def built_state(relative: str) -> str:
        return "current" if (ROOT / relative).is_file() else "declared"
    records: list[dict[str, object]] = [
        {
            "id": "art-o002-p01-results",
            "kind": "result_json",
            "path": "output/p01-results.json",
            "producer": "cmp-o002-p01-code",
            "state": built_state("output/p01-results.json"),
        },
        {
            "id": "art-o002-p01-notebook",
            "kind": "notebook",
            "path": "source/notebooks/o002-p01-clean-kernel.ipynb",
            "producer": "cmp-o002-p01-notebook-generator",
            "state": "current",
        },
        {
            "id": "art-o002-p02-values",
            "kind": "accessibility_text",
            "path": "output/primer02-demo/values.txt",
            "producer": "cmp-o002-p02-code",
            "state": built_state("output/primer02-demo/values.txt"),
        },
        {
            "id": "art-o002-p02-measurements",
            "kind": "data_csv",
            "path": "output/primer02-demo/measurements.csv",
            "producer": "cmp-o002-p02-code",
            "state": built_state("output/primer02-demo/measurements.csv"),
        },
        {
            "id": "art-o002-p02-summary",
            "kind": "result_json",
            "path": "output/primer02-demo/summary.json",
            "producer": "cmp-o002-p02-code",
            "state": built_state("output/primer02-demo/summary.json"),
        },
        {
            "id": "art-o002-p02-manifest",
            "kind": "manifest_json",
            "path": "output/primer02-demo/manifest.json",
            "producer": "cmp-o002-p02-code",
            "state": built_state("output/primer02-demo/manifest.json"),
            "members": [
                "art-o002-p02-values",
                "art-o002-p02-measurements",
                "art-o002-p02-summary",
            ],
        },
    ]

    for number in (1, 2, 3, 5, 7, 8, 9, 10, 12):
        records.append(
            {
                "id": f"art-o002-u{number:02d}-results",
                "kind": "result_json",
                "path": f"output/unit{number:02d}-results.json",
                "producer": f"cmp-o002-u{number:02d}-code",
                "state": built_state(f"output/unit{number:02d}-results.json"),
            }
        )

    records.extend(
        [
            {
                "id": "art-o002-u04-data",
                "kind": "data_csv",
                "path": "output/unit04/unit04-data.csv",
                "producer": "lab-o002-u04-plotting-m01",
                "state": built_state("output/unit04/unit04-data.csv"),
            },
            {
                "id": "art-o002-u04-figure",
                "kind": "figure_svg",
                "path": "output/unit04/unit04-figure.svg",
                "producer": "lab-o002-u04-plotting-m01",
                "state": built_state("output/unit04/unit04-figure.svg"),
                "accessibility_description": "art-o002-u04-alt",
            },
            {
                "id": "art-o002-u04-alt",
                "kind": "accessibility_text",
                "path": "output/unit04/unit04-alt.txt",
                "producer": "lab-o002-u04-plotting-m01",
                "state": built_state("output/unit04/unit04-alt.txt"),
            },
            {
                "id": "art-o002-u04-manifest",
                "kind": "manifest_json",
                "path": "output/unit04/unit04-manifest.json",
                "producer": "lab-o002-u04-plotting-m01",
                "state": built_state("output/unit04/unit04-manifest.json"),
                "members": [
                    "art-o002-u04-data",
                    "art-o002-u04-figure",
                    "art-o002-u04-alt",
                ],
            },
            {
                "id": "art-o002-u05-sage-results",
                "kind": "result_json",
                "path": "00_control/SAGE_LAB_RESULT.json",
                "producer": "lab-o002-u05-sage",
                "state": "current",
                "receipt_ids": [
                    "receipt-o002-sage-lab-result",
                    "receipt-o002-sage-lab-qa",
                ],
            },
            {
                "id": "art-o002-u06-results",
                "kind": "result_json",
                "path": "output/unit06-results.json",
                "producer": "lab-o002-u06-scipy",
                "state": built_state("output/unit06-results.json"),
            },
            {
                "id": "art-o002-u11-results",
                "kind": "result_json",
                "path": "output/unit11-results.json",
                "producer": "lab-o002-u11-scipy",
                "state": built_state("output/unit11-results.json"),
            },
            {
                "id": "art-o002-reader-html",
                "kind": "reader_html",
                "path": RELEASE_ARTIFACT_PATHS["art-o002-reader-html"],
                "producer": "pipeline-o002-build",
                "state": "current" if (
                    bundle_current or present.get("html") is True
                ) and (ROOT / RELEASE_ARTIFACT_PATHS["art-o002-reader-html"]).is_file() else "declared",
            },
            {
                "id": "art-o002-reader-pdf",
                "kind": "reader_pdf",
                "path": RELEASE_ARTIFACT_PATHS["art-o002-reader-pdf"],
                "producer": "pipeline-o002-build",
                "state": "current" if (
                    bundle_current or present.get("pdf") is True
                ) and (ROOT / RELEASE_ARTIFACT_PATHS["art-o002-reader-pdf"]).is_file() else "declared",
            },
            {
                "id": "art-o002-reader-epub",
                "kind": "reader_epub",
                "path": RELEASE_ARTIFACT_PATHS["art-o002-reader-epub"],
                "producer": "pipeline-o002-build",
                "state": "current" if (
                    bundle_current or present.get("epub") is True
                ) and (ROOT / RELEASE_ARTIFACT_PATHS["art-o002-reader-epub"]).is_file() else "declared",
            },
            {
                "id": "art-o002-source-archive",
                "kind": "source_archive",
                "path": RELEASE_ARTIFACT_PATHS["art-o002-source-archive"],
                "producer": "pipeline-o002-build",
                "state": "current" if bundle_current else "declared",
            },
            {
                "id": "art-o002-offline-bundle",
                "kind": "bundle",
                "path": RELEASE_ARTIFACT_PATHS["art-o002-offline-bundle"],
                "producer": "pipeline-o002-build",
                "state": "current" if bundle_current else "declared",
            },
        ]
    )
    release_receipts = {
        "art-o002-reader-html": [key for key in (receipt_ids.get("bundle"), receipt_ids.get("html")) if key],
        "art-o002-reader-pdf": [key for key in (receipt_ids.get("bundle"), receipt_ids.get("pdf")) if key],
        "art-o002-reader-epub": [key for key in (receipt_ids.get("bundle"), receipt_ids.get("epub")) if key],
        "art-o002-source-archive": [key for key in (receipt_ids.get("bundle"),) if key],
        "art-o002-offline-bundle": [key for key in (receipt_ids.get("bundle"),) if key],
    }
    for record in records:
        if record["id"] in release_receipts and release_receipts[record["id"]]:
            record["receipt_ids"] = release_receipts[record["id"]]
        path = ROOT / str(record["path"])
        if (
            record["state"] in {"current", "historical_release"}
            and path.is_file()
            and record["id"] not in EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS
        ):
            record["bytes"] = path.stat().st_size
            record["sha256"] = sha256(path)
    return records


def environment_record(
    *,
    environment_id: str,
    kind: str,
    runtime_version: str,
    platform: str,
    availability: str,
    lock_relative: str,
    receipt_relative: str,
    expected_schema: str,
    required_packages: list[str],
) -> dict[str, object]:
    lock_path = ROOT / lock_relative
    receipt_path = ROOT / receipt_relative
    if not lock_path.is_file() or not receipt_path.is_file():
        raise FileNotFoundError(f"environment evidence missing: {lock_path}, {receipt_path}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("schema") != expected_schema or receipt.get("matches_runtime") is not True:
        raise RuntimeError(f"environment receipt is not verified: {receipt_relative}")
    lock = receipt.get("lock")
    if not isinstance(lock, dict):
        raise RuntimeError(f"environment receipt lacks lock record: {receipt_relative}")
    if (
        lock.get("path") != lock_relative
        or lock.get("bytes") != lock_path.stat().st_size
        or lock.get("sha256") != sha256(lock_path)
    ):
        raise RuntimeError(f"environment lock mismatch: {lock_relative}")
    package_count = receipt.get("package_count", lock.get("installed_package_count"))
    if not isinstance(package_count, int) or package_count < 1:
        raise RuntimeError(f"environment package count missing: {receipt_relative}")
    return {
        "id": environment_id,
        "kind": kind,
        "runtime_version": runtime_version,
        "platform": platform,
        "availability": availability,
        "status": "current",
        "lock": {
            "path": lock_relative,
            "bytes": lock_path.stat().st_size,
            "sha256": sha256(lock_path),
        },
        "receipt": {
            "path": receipt_relative,
            "bytes": receipt_path.stat().st_size,
            "sha256": sha256(receipt_path),
            "schema": expected_schema,
        },
        "package_count": package_count,
        "required_packages": required_packages,
    }


def environment_records() -> list[dict[str, object]]:
    python_receipt = json.loads(
        (ROOT / "environment/PYTHON_ENVIRONMENT_RECEIPT.json").read_text(encoding="utf-8")
    )
    python_roots = [str(item) for item in python_receipt.get("direct_roots", [])]
    return [
        environment_record(
            environment_id="env-o002-python",
            kind="python",
            runtime_version="CPython 3.13.1",
            platform="OS-independent package identities; native Windows execution",
            availability="native",
            lock_relative="environment/python-lock.txt",
            receipt_relative="environment/PYTHON_ENVIRONMENT_RECEIPT.json",
            expected_schema="o002.python-environment.v1",
            required_packages=python_roots,
        ),
        environment_record(
            environment_id="env-o002-sage",
            kind="sagemath",
            runtime_version="SageMath 9.5; apt sagemath 9.5-4",
            platform="WSL Ubuntu 22.04 x86_64",
            availability="local_wsl",
            lock_relative="environment/sage-ubuntu22.04-dpkg-lock.txt",
            receipt_relative="environment/SAGE_ENVIRONMENT_RECEIPT.json",
            expected_schema="o002.sage-environment.v1",
            required_packages=["python3-sage==9.5-4", "sagemath==9.5-4"],
        ),
    ]


def lab_records(evidence: dict[str, object]) -> list[dict[str, object]]:
    present = evidence["present"]
    assert isinstance(present, dict)
    sage_complete = present.get("sage") is True
    return [
        {
            "id": "lab-o002-u04-plotting-m01",
            "unit": "o002.u04",
            "kind": "plotting",
            "status": "complete",
            "environment": "env-o002-python",
            "exercise_ids": ["ex-o002-u04-m01"],
            "artifact_ids": [
                "art-o002-u04-data",
                "art-o002-u04-figure",
                "art-o002-u04-alt",
                "art-o002-u04-manifest",
            ],
            "source_paths": [
                "source/units/04-visualisasi-integritas.qmd",
                "source/code/unit04_visualization.py",
                "tests/test_unit04.py",
            ],
            "requirements": [
                "progressive fig/ax plot scatter errorbar construction",
                "labels units legend and accessible description",
                "deterministic data-to-plot-to-manifest mastery",
            ],
            "evidence": "current executable mastery exercise and four current output artifacts",
        },
        {
            "id": "lab-o002-u05-sage",
            "unit": "o002.u05",
            "kind": "sagemath",
            "status": "complete" if sage_complete else "pending",
            "environment": "env-o002-sage",
            "exercise_ids": ["ex-o002-u05-sage-01", "ex-o002-u05-sage-02"],
            "artifact_ids": ["art-o002-u05-sage-results"],
            "source_paths": [
                "source/units/05-eksak-simbolik-sage.qmd",
                "source/code/unit05_symbolic.py",
                "source/code/unit05_sage_lab.py",
                "tests/test_unit05.py",
                "tests/test_unit05_sage.py",
            ],
            "requirements": [
                "local execution of ZZ QQ RR SR and coercion",
                "polynomial factorization solving and approximation",
                "two executable Sage mastery exercises with full solutions",
            ],
            "evidence": (
                "Sage 9.5 lab result and seven-test local execution receipt are bound"
                if sage_complete
                else "local Sage execution evidence is absent or invalid"
            ),
        },
        {
            "id": "lab-o002-u06-scipy",
            "unit": "o002.u06",
            "kind": "scipy",
            "status": "complete",
            "environment": "env-o002-python",
            "exercise_ids": ["ex-o002-u06-scipy-01"],
            "artifact_ids": ["art-o002-u06-results"],
            "source_paths": [
                "source/units/06-titik-mengambang-stabilitas.qmd",
                "source/code/unit06_floating.py",
                "tests/test_unit06.py",
            ],
            "requirements": [
                "scipy.special.exprel stable-versus-naive comparison",
                "domain conditioning forward/backward error and proof boundary",
                "executable mastery exercise and tests",
            ],
            "evidence": "current SciPy content, mastery exercise, code, and executable tests",
        },
        {
            "id": "lab-o002-u11-scipy",
            "unit": "o002.u11",
            "kind": "scipy",
            "status": "complete",
            "environment": "env-o002-python",
            "exercise_ids": ["ex-o002-u11-s01"],
            "artifact_ids": ["art-o002-u11-results"],
            "source_paths": [
                "source/units/11-eksperimen-numerik.qmd",
                "source/code/unit11_numerical.py",
                "tests/test_unit11.py",
            ],
            "requirements": [
                "original bisection versus scipy.optimize.root_scalar(method=bisect)",
                "version bracketing convergence residual and result validation",
                "executable A30 mastery exercise and tests",
            ],
            "evidence": "current SciPy comparison, mastery exercise, code, and executable tests",
        },
    ]


def prerequisite_routes() -> list[dict[str, object]]:
    return [
        {
            "id": "route-o002-u11-a30",
            "unit": "o002.u11",
            "title": "Jalur inti A30/B80: metode, bagi-dua, SciPy, dan sumber galat",
            "prerequisite": "A30",
            "gate_id": None,
            "status": "core",
            "required_for_b80": True,
            "sections": [
                "sec-o002-u11-method-theorem",
                "sec-o002-u11-bisection",
                "sec-o002-u11-scipy-bisection",
                "sec-o002-u11-error-sources",
                "sec-o002-u11-artifacts",
            ],
            "exercises": [
                "ex-o002-u11-01",
                "ex-o002-u11-02",
                "ex-o002-u11-s01",
            ],
        },
        {
            "id": "route-o002-u11-b30",
            "unit": "o002.u11",
            "title": "Jalur B30: kuadratur",
            "prerequisite": "B30",
            "gate_id": "gate-o002-u11-b30",
            "status": "deferred",
            "required_for_b80": False,
            "sections": ["sec-o002-u11-quadrature"],
            "exercises": ["ex-o002-u11-03"],
        },
        {
            "id": "route-o002-u11-b40",
            "unit": "o002.u11",
            "title": "Jalur B40: sistem linear",
            "prerequisite": "B40",
            "gate_id": "gate-o002-u11-b40",
            "status": "deferred",
            "required_for_b80": False,
            "sections": ["sec-o002-u11-linear"],
            "exercises": ["ex-o002-u11-04"],
        },
        {
            "id": "route-o002-u11-b70",
            "unit": "o002.u11",
            "title": "Jalur B70: langkah Euler",
            "prerequisite": "B70",
            "gate_id": "gate-o002-u11-b70",
            "status": "deferred",
            "required_for_b80": False,
            "sections": ["sec-o002-u11-euler"],
            "exercises": ["ex-o002-u11-05"],
        },
    ]


def build_catalog() -> dict[str, object]:
    evidence = evidence_state()
    present = evidence["present"]
    receipt_ids = evidence["receipt_ids"]
    assert isinstance(present, dict) and isinstance(receipt_ids, dict)
    units: list[dict[str, object]] = []
    components: list[dict[str, str]] = []
    exercises: list[dict[str, object]] = []
    for spec in UNIT_SPECS:
        unit, unit_components, unit_exercises = parse_unit(spec)
        units.append(unit)
        components.extend(unit_components)
        exercises.extend(unit_exercises)

    supplemental_components = [
        {
            "id": "cmp-o002-p01-notebook-generator",
            "kind": "software",
            "source": "src-o002-original",
            "license": "MIT",
            "path": "scripts/make_notebook_supplement.py",
        },
        {
            "id": "cmp-o002-p01-notebook-test",
            "kind": "test",
            "source": "src-o002-original",
            "license": "MIT",
            "path": "tests/test_notebook_supplement.py",
        },
        {
            "id": "cmp-o002-u05-sage-code",
            "kind": "software",
            "source": "src-o002-original",
            "license": "MIT",
            "path": "source/code/unit05_sage_lab.py",
        },
        {
            "id": "cmp-o002-u05-sage-test",
            "kind": "test",
            "source": "src-o002-original",
            "license": "MIT",
            "path": "tests/test_unit05_sage.py",
        },
    ]
    components.extend(supplemental_components)
    p01 = next(unit for unit in units if unit["id"] == "o002.p01")
    p01["components"].extend(
        component["id"]
        for component in supplemental_components
        if component["id"].startswith("cmp-o002-p01-")
    )  # type: ignore[index]
    u05 = next(unit for unit in units if unit["id"] == "o002.u05")
    u05["components"].extend(
        component["id"]
        for component in supplemental_components
        if component["id"].startswith("cmp-o002-u05-sage-")
    )  # type: ignore[index]

    sage_complete = present.get("sage") is True
    for unit in units:
        if unit["id"] == "o002.u05":
            unit["curriculum_status"] = (
                "complete" if sage_complete else "repair_required"
            )

    artifacts = artifact_records(evidence)
    environments = environment_records()
    labs = lab_records(evidence)
    routes = prerequisite_routes()

    relations: list[dict[str, str]] = []
    for first, second in zip(REQUIRED_UNIT_IDS, REQUIRED_UNIT_IDS[1:]):
        relations.append({"type": "precedes", "from": first, "to": second})
    for unit in units:
        for component in unit["components"]:  # type: ignore[index]
            relations.append({"type": "uses_component", "from": unit["id"], "to": component})  # type: ignore[index]
    unit_test_components = {
        unit["id"]: next(component for component in unit["components"] if component.endswith("-test"))  # type: ignore[index]
        for unit in units
    }
    for exercise in exercises:
        if exercise["check"]["status"] == "executable":  # type: ignore[index]
            validator = (
                "cmp-o002-u05-sage-test"
                if str(exercise["id"]).startswith("ex-o002-u05-sage-")
                else unit_test_components[exercise["unit"]]  # type: ignore[index]
            )
            relations.append(
                {
                    "type": "validated_by",
                    "from": exercise["id"],  # type: ignore[index]
                    "to": validator,
                }
            )
    for lab in labs:
        relations.append({"type": "implements", "from": lab["unit"], "to": lab["id"]})  # type: ignore[index]
        relations.append({"type": "uses_environment", "from": lab["id"], "to": lab["environment"]})  # type: ignore[index]
        for artifact_id in lab["artifact_ids"]:  # type: ignore[index]
            relations.append({"type": "produces", "from": lab["id"], "to": artifact_id})  # type: ignore[index]
    for route in routes:
        relations.append({"type": "implements", "from": route["unit"], "to": route["id"]})  # type: ignore[index]
        relations.append(
            {
                "type": "requires_prerequisite",
                "from": route["id"],  # type: ignore[index]
                "to": route["prerequisite"],  # type: ignore[index]
            }
        )
    produced_pairs = {
        (relation["from"], relation["to"])
        for relation in relations
        if relation["type"] == "produces"
    }
    for artifact in artifacts:
        pair = (str(artifact["producer"]), str(artifact["id"]))
        if pair not in produced_pairs:
            relations.append({"type": "produces", "from": pair[0], "to": pair[1]})
    relations.append(
        {
            "type": "validated_by",
            "from": "art-o002-p01-notebook",
            "to": "cmp-o002-p01-notebook-test",
        }
    )

    formats_complete = present.get("bundle") is True
    deterministic = present.get("determinism") is True
    accessible = all(present.get(key) is True for key in ("html", "pdf", "epub"))
    published = present.get("publication") is True

    pending_requirements = [
        (
            "compulsory local Sage lab and two executable Sage mastery exercises",
            sage_complete,
        ),
        (
            "expanded HTML PDF EPUB editable-source and offline-bundle build with notebook packaging",
            formats_complete,
        ),
        (
            "two clean byte-identical final builds and complete manifests",
            deterministic,
        ),
        (
            "full PDF visual and HTML/EPUB accessibility receipts",
            accessible,
        ),
    ]
    open_requirements = [
        description for description, complete in pending_requirements if not complete
    ]
    b80_complete = not open_requirements

    def ids(*keys: str) -> list[str]:
        return [str(receipt_ids[key]) for key in keys if key in receipt_ids]

    qa = [
        {
            "id": "qa-o002-standalone-release",
            "scope": "historical_standalone",
            "required_for_b80": False,
            "status": "pass",
            "evidence": "immutable v2026.08.22 release: 12 units and 60 exercises",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-b80-source-structure",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "ordered 14-unit source with P01/P02 and stable existing unit IDs",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-python-environment",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "verified 95-package Python lock and matching runtime receipt",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-sage-environment",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "verified Ubuntu 22.04 Sage 9.5 lock and matching runtime receipt",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-u04-plotting-mastery",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "progressive plotting lab, executable m01, accessible output, and manifest",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-u05-sage-lab",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass" if sage_complete else "pending",
            "evidence": (
                "local Sage 9.5 result and seven-test execution receipt are verified"
                if sage_complete
                else "local Sage execution evidence is absent or invalid"
            ),
            "receipt_ids": ids("sage_result", "sage_qa"),
        },
        {
            "id": "qa-o002-u06-scipy-lab",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "scipy.special.exprel comparison, mastery exercise, and executable tests",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-u11-scipy-and-routes",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "root_scalar comparison, mastery exercise, and explicit A30/B30/B40/B70 routes",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-p01-notebook-supplement",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "current deterministic clean-kernel notebook supplement and frozen-kernel validation",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-rights-provenance",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "all admitted expression is original CC BY-SA 4.0 text and MIT code",
            "receipt_ids": [],
        },
        {
            "id": "qa-o002-reader-formats-and-bundle",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass" if formats_complete else "pending",
            "evidence": (
                "versioned HTML PDF EPUB source archive and offline bundle identities are verified"
                if formats_complete
                else "versioned reader and bundle receipt is absent or invalid"
            ),
            "receipt_ids": ids("bundle"),
        },
        {
            "id": "qa-o002-two-clean-builds",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass" if deterministic else "pending",
            "evidence": (
                "two clean source/output manifest pairs are byte-identical"
                if deterministic
                else "two-build determinism receipt is absent or invalid"
            ),
            "receipt_ids": ids("determinism"),
        },
        {
            "id": "qa-o002-final-accessibility",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass" if accessible else "pending",
            "evidence": (
                "PDF all-page review plus HTML browser and EPUB accessibility receipts pass"
                if accessible
                else "one or more PDF HTML-browser or EPUB receipts are absent or invalid"
            ),
            "receipt_ids": ids("html", "pdf", "epub"),
        },
        {
            "id": "qa-o002-final-publication",
            "scope": "external_preservation",
            "required_for_b80": False,
            "status": "pass" if published else "pending",
            "evidence": (
                "Zenodo anonymous byte readback is verified; GitHub publication is deferred while the account suspension is under support review"
                if published
                else "external publication receipt is absent or invalid"
            ),
            "receipt_ids": ids("publication"),
        },
        {
            "id": "qa-o002-backend-truth",
            "scope": "current_b80",
            "required_for_b80": True,
            "status": "pass",
            "evidence": "schema-backed topology and closure invariants pass at this boundary",
            "receipt_ids": [],
        },
    ]
    next_work_item = next(
        (
            str(record["id"])
            for record in qa
            if record["required_for_b80"] and record["status"] == "pending"
        ),
        None,
    )
    boundary = (
        "all 14 selected units and every curricular/build/accessibility gate pass"
        if b80_complete
        else f"all 14 selected units admitted; next unresolved gate: {next_work_item}"
    )

    return {
        "schema_version": "o002.backend.v2",
        "language": "id-ID",
        "course": {
            "id": "B80",
            "project_id": "O002",
            "title": "Komputasi Matematis dan Eksperimen yang Dapat Direproduksi",
            "prerequisite": "A30",
            "selected_unit_count": 14,
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
                "role": "comparison_only",
                "license": "CC BY-NC-SA 4.0; separate component rights remain separate",
                "identity": "commit 0687916182ab3ddc9e922d4a6eb603609ba91c36; tree b66a9c79aa7144a75d3f83ba53bba4ff8961f91b",
                "used_in_current_units": False,
            },
            {
                "id": "src-o002-rse",
                "title": "Research Software Engineering with Python",
                "role": "comparison_only",
                "license": "CC BY 4.0 text; MIT code; excluded components remain separate",
                "identity": "commit 62217e6606842ab9752fcf8e73954d1eb4a3cf07; tree f570f30bb8ace202550c474e81eb3414e8976be5",
                "used_in_current_units": False,
            },
            {
                "id": "src-o002-spl",
                "title": "Scientific Python Lectures",
                "role": "comparison_only",
                "license": "CC BY 4.0",
                "identity": "commit 817a97d8d9a26eeb4e735a402420cd34dd7e89fc; tree 4af72a3d18cf9bfd32ccbf0c1ea099dd4ba65689",
                "used_in_current_units": False,
            },
            {
                "id": "src-o002-fangohr",
                "title": "Introduction to Python for Computational Science and Engineering",
                "role": "comparison_only",
                "license": "CC BY-NC 4.0",
                "identity": "official repository fangohr/introduction-to-python-for-computational-science-and-engineering; DOI 10.5281/zenodo.1411868",
                "used_in_current_units": False,
            },
            {
                "id": "src-o002-sage-tutorial",
                "title": "Official Sage Tutorial 10.9",
                "role": "comparison_only",
                "license": "CC BY-SA 3.0",
                "identity": "commit 686dc1a8d420c2e0aabadd4f602d9a0aa4690c50; src/doc/en/tutorial",
                "used_in_current_units": False,
            },
        ],
        "components": components,
        "units": units,
        "exercises": exercises,
        "artifacts": artifacts,
        "labs": labs,
        "environments": environments,
        "prerequisite_routes": routes,
        "relations": relations,
        "receipts": evidence["receipts"],
        "qa": qa,
        "historical_release": {
            "version": "2026.08.22",
            "tag": "v2026.08.22",
            "doi": "10.5281/zenodo.22052053",
            "unit_count": 12,
            "exercise_count": 60,
            "verified": True,
        },
        "planned_release": {
            "version": RELEASE_VERSION,
            "tag": RELEASE_TAG,
            "record_id": RELEASE_RECORD_ID,
            "doi": RELEASE_DOI,
            "status": (
                "published" if published else "b80_complete" if b80_complete else "in_progress"
            ),
            "artifact_ids": list(RELEASE_ARTIFACT_PATHS),
        },
        "architecture": {
            "status": "complete" if b80_complete else "in_progress",
            "required_unit_ids": REQUIRED_UNIT_IDS,
            "admitted_unit_ids": REQUIRED_UNIT_IDS,
            "open_requirements": open_requirements,
        },
        "cursor": {
            "last_admitted_unit": "o002.u12",
            "next_unit": None,
            "next_work_item": next_work_item,
            "boundary": boundary,
            "standalone_edition_complete": True,
            "b80_curriculum_complete": b80_complete,
            "admitted_unit_count": 14,
            "selected_unit_count": 14,
        },
    }


def main() -> int:
    output = ROOT / "backend" / "catalog.json"
    output.write_text(
        json.dumps(build_catalog(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
