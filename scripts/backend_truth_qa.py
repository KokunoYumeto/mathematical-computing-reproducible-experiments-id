from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from typing import Iterable

from jsonschema import Draft202012Validator

from update_backend import (
    EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS,
    RELEASE_ARTIFACT_PATHS,
    RELEASE_DOI,
    RELEASE_RECORD_ID,
    evidence_state,
)


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_UNIT_IDS = [
    "o002.p01",
    "o002.p02",
    *[f"o002.u{number:02d}" for number in range(1, 13)],
]
HISTORICAL_EXERCISE_IDS = {
    f"ex-o002-u{unit:02d}-{exercise:02d}"
    for unit in range(1, 13)
    for exercise in range(1, 6)
}
CURRENT_MASTERY_IDS = {
    "ex-o002-u04-m01",
    "ex-o002-u05-sage-01",
    "ex-o002-u05-sage-02",
    "ex-o002-u06-scipy-01",
    "ex-o002-u11-s01",
}
REQUIRED_EXECUTABLE_IDS = {
    *[f"ex-o002-p01-{number:02d}" for number in range(1, 6)],
    *[f"ex-o002-p02-{number:02d}" for number in range(1, 6)],
    *CURRENT_MASTERY_IDS,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique_ids(records: Iterable[dict[str, object]], label: str) -> set[str]:
    identifiers = [str(record["id"]) for record in records]
    require(len(identifiers) == len(set(identifiers)), f"duplicate {label} ID")
    return set(identifiers)


def safe_file(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as error:
        raise RuntimeError(f"path escapes lane: {relative}") from error
    return path


def validate_environment(record: dict[str, object]) -> None:
    lock = record["lock"]
    receipt_record = record["receipt"]
    require(isinstance(lock, dict), f"invalid lock record: {record['id']}")
    require(isinstance(receipt_record, dict), f"invalid receipt record: {record['id']}")
    lock_path = safe_file(str(lock["path"]))
    receipt_path = safe_file(str(receipt_record["path"]))
    require(lock_path.is_file(), f"environment lock missing: {lock_path}")
    require(receipt_path.is_file(), f"environment receipt missing: {receipt_path}")
    require(lock_path.stat().st_size == lock["bytes"], f"environment lock size mismatch: {record['id']}")
    require(sha256(lock_path) == lock["sha256"], f"environment lock hash mismatch: {record['id']}")
    require(receipt_path.stat().st_size == receipt_record["bytes"], f"environment receipt size mismatch: {record['id']}")
    require(sha256(receipt_path) == receipt_record["sha256"], f"environment receipt hash mismatch: {record['id']}")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(receipt.get("schema") == receipt_record["schema"], f"environment receipt schema mismatch: {record['id']}")
    require(receipt.get("matches_runtime") is True, f"environment receipt did not match runtime: {record['id']}")
    receipt_lock = receipt.get("lock")
    require(isinstance(receipt_lock, dict), f"receipt lock absent: {record['id']}")
    require(receipt_lock.get("path") == lock["path"], f"receipt lock path mismatch: {record['id']}")
    require(receipt_lock.get("bytes") == lock["bytes"], f"receipt lock bytes mismatch: {record['id']}")
    require(receipt_lock.get("sha256") == lock["sha256"], f"receipt lock hash mismatch: {record['id']}")
    package_count = receipt.get("package_count", receipt_lock.get("installed_package_count"))
    require(package_count == record["package_count"], f"environment package count mismatch: {record['id']}")
    require(record["status"] == "current", f"verified environment not current: {record['id']}")


def validate_receipt_record(record: dict[str, object]) -> None:
    path = safe_file(str(record["path"]))
    require(path.is_file(), f"registered receipt missing: {record['id']}")
    document = json.loads(path.read_text(encoding="utf-8"))
    require(document.get("schema") == record["schema"], f"receipt schema mismatch: {record['id']}")
    if record["binding"] == "bound":
        require(path.stat().st_size == record["bytes"], f"receipt byte mismatch: {record['id']}")
        require(sha256(path) == record["sha256"], f"receipt hash mismatch: {record['id']}")
    else:
        require(record["binding"] == "external", f"unknown receipt binding: {record['id']}")
        require("bytes" not in record and "sha256" not in record, f"external receipt creates an identity cycle: {record['id']}")


def main() -> int:
    schema = json.loads((ROOT / "backend/catalog.schema.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "backend/catalog.json").read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(catalog),
        key=lambda error: list(error.path),
    )
    require(
        not errors,
        "backend schema failure: "
        + "; ".join(f"{error.json_path}: {error.message}" for error in errors),
    )

    require(catalog["schema_version"] == "o002.backend.v2", "backend must use v2 truth schema")
    require(catalog["language"] == "id-ID", "backend language changed")
    require(catalog["course"]["selected_unit_count"] == 14, "selected count must be 14")

    sources = catalog["sources"]
    components = catalog["components"]
    units = catalog["units"]
    exercises = catalog["exercises"]
    artifacts = catalog["artifacts"]
    labs = catalog["labs"]
    environments = catalog["environments"]
    routes = catalog["prerequisite_routes"]
    relations = catalog["relations"]
    receipts = catalog["receipts"]
    qa = catalog["qa"]

    source_ids = unique_ids(sources, "source")
    component_ids = unique_ids(components, "component")
    unit_ids = unique_ids(units, "unit")
    exercise_ids = unique_ids(exercises, "exercise")
    artifact_ids = unique_ids(artifacts, "artifact")
    lab_ids = unique_ids(labs, "lab")
    environment_ids = unique_ids(environments, "environment")
    route_ids = unique_ids(routes, "route")
    receipt_ids = unique_ids(receipts, "receipt")
    unique_ids(qa, "QA")

    original_sources = [source for source in sources if source["role"] == "original"]
    require(len(original_sources) == 1 and original_sources[0]["id"] == "src-o002-original", "original source identity is wrong")
    for source in sources:
        if source["id"] != "src-o002-original":
            require(source["role"] == "comparison_only", f"external source is not comparison-only: {source['id']}")
            require(source["used_in_current_units"] is False, f"external source incorrectly marked used: {source['id']}")

    architecture = catalog["architecture"]
    require(architecture["required_unit_ids"] == REQUIRED_UNIT_IDS, "selected unit order is wrong")
    require(architecture["admitted_unit_ids"] == REQUIRED_UNIT_IDS, "all 14 units must be admitted in selected order")
    require([unit["id"] for unit in units] == REQUIRED_UNIT_IDS, "unit records are not in selected order")
    require(unit_ids == set(REQUIRED_UNIT_IDS), "unit topology is not exactly P01/P02/U01-U12")

    evidence = evidence_state()
    present = evidence["present"]
    expected_receipt_ids = {str(record["id"]) for record in evidence["receipts"]}
    require(receipt_ids == expected_receipt_ids, "catalog receipt set differs from validated durable evidence")
    for receipt in receipts:
        validate_receipt_record(receipt)

    sage_complete = present.get("sage") is True
    repair_ids = {unit["id"] for unit in units if unit["curriculum_status"] == "repair_required"}
    require(repair_ids == (set() if sage_complete else {"o002.u05"}), f"current repair set is wrong: {sorted(repair_ids)}")
    for unit in units:
        expected_standalone = "not_applicable" if unit["id"].startswith("o002.p") else "complete"
        require(unit["standalone_status"] == expected_standalone, f"standalone status wrong: {unit['id']}")
        if unit["id"] != "o002.u05" or sage_complete:
            require(unit["curriculum_status"] == "complete", f"completed current unit regressed: {unit['id']}")

    unit_by_id = {unit["id"]: unit for unit in units}
    artifact_by_id = {artifact["id"]: artifact for artifact in artifacts}
    lab_by_id = {lab["id"]: lab for lab in labs}
    environment_by_id = {environment["id"]: environment for environment in environments}
    route_by_id = {route["id"]: route for route in routes}

    for component in components:
        require(component["source"] in source_ids, f"unknown component source: {component['id']}")
        require(safe_file(component["path"]).is_file(), f"component path missing: {component['path']}")
    for unit in units:
        require(set(unit["components"]).issubset(component_ids), f"unknown unit component: {unit['id']}")
        require(set(unit["exercises"]).issubset(exercise_ids), f"unknown unit exercise: {unit['id']}")
        require(
            [exercise["id"] for exercise in exercises if exercise["unit"] == unit["id"]] == unit["exercises"],
            f"exercise record order differs from unit: {unit['id']}",
        )
        require(len(unit["components"]) >= 3, f"unit triplet incomplete: {unit['id']}")

    require(len(exercises) == 75, f"current boundary must contain 75 exercises; found {len(exercises)}")
    require(HISTORICAL_EXERCISE_IDS.issubset(exercise_ids), "historical 60 exercises were not preserved")
    require(CURRENT_MASTERY_IDS.issubset(exercise_ids), "current mastery exercises are incomplete")
    primer_ids = {identifier for identifier in exercise_ids if identifier.startswith(("ex-o002-p01-", "ex-o002-p02-"))}
    require(len(primer_ids) == 10, "primers must contain exactly ten exercises")
    for exercise in exercises:
        require(exercise["unit"] in unit_ids, f"exercise has unknown unit: {exercise['id']}")
        require(exercise["source_path"] == unit_by_id[exercise["unit"]]["reader_path"], f"exercise source mismatch: {exercise['id']}")
        source_text = safe_file(exercise["source_path"]).read_text(encoding="utf-8")
        require(f"{{#{exercise['id']}}}" in source_text, f"exercise anchor absent from source: {exercise['id']}")
        require(exercise["hint"]["status"] == "complete", f"hint incomplete: {exercise['id']}")
        require(exercise["solution"]["status"] == "complete", f"solution incomplete: {exercise['id']}")
        if exercise["id"] in REQUIRED_EXECUTABLE_IDS:
            require(exercise["check"]["status"] == "executable", f"required executable check absent: {exercise['id']}")
    deferred = {exercise["id"] for exercise in exercises if exercise["curriculum_status"] == "prerequisite_deferred"}
    require(deferred == {"ex-o002-u11-03", "ex-o002-u11-04", "ex-o002-u11-05"}, f"deferred exercise set is wrong: {sorted(deferred)}")

    require(set(environment_by_id) == {"env-o002-python", "env-o002-sage"}, "environment set is wrong")
    for environment in environments:
        validate_environment(environment)
    require(environment_by_id["env-o002-python"]["package_count"] == 95, "Python closure count changed")
    require(environment_by_id["env-o002-sage"]["package_count"] == 1064, "Sage closure count changed")

    expected_lab_status = {
        "lab-o002-u04-plotting-m01": "complete",
        "lab-o002-u05-sage": "complete" if sage_complete else "pending",
        "lab-o002-u06-scipy": "complete",
        "lab-o002-u11-scipy": "complete",
    }
    require({lab["id"]: lab["status"] for lab in labs} == expected_lab_status, "lab status map is wrong")
    for lab in labs:
        require(lab["unit"] in unit_ids, f"lab unit unknown: {lab['id']}")
        require(lab["environment"] in environment_ids, f"lab environment unknown: {lab['id']}")
        require(set(lab["exercise_ids"]).issubset(exercise_ids), f"lab exercise unknown: {lab['id']}")
        require(set(lab["artifact_ids"]).issubset(artifact_ids), f"lab artifact unknown: {lab['id']}")
        for source_path in lab["source_paths"]:
            require(safe_file(source_path).is_file(), f"lab source missing: {lab['id']} -> {source_path}")
    require(lab_by_id["lab-o002-u05-sage"]["exercise_ids"] == ["ex-o002-u05-sage-01", "ex-o002-u05-sage-02"], "Sage mastery exercises are not registered")

    artifact_paths = [artifact["path"].casefold() for artifact in artifacts]
    require(len(artifact_paths) == len(set(artifact_paths)), "artifact paths are not unique")
    known_producers = component_ids | lab_ids | {"pipeline-o002-build"}
    for artifact in artifacts:
        require(artifact["producer"] in known_producers, f"artifact producer unknown: {artifact['id']}")
        if artifact["state"] in {"current", "historical_release"}:
            path = safe_file(artifact["path"])
            require(path.is_file(), f"current/historical artifact missing: {artifact['id']}")
            if artifact["id"] in EXTERNALLY_BOUND_ARCHIVE_ARTIFACT_IDS:
                require(present.get("bundle") is True, f"archive lacks valid external bundle receipt: {artifact['id']}")
                require(artifact.get("receipt_ids") == ["receipt-o002-bundle"], f"archive receipt binding is wrong: {artifact['id']}")
                require("bytes" not in artifact and "sha256" not in artifact, f"archive self-identity must remain external: {artifact['id']}")
            else:
                require(path.stat().st_size == artifact["bytes"] and sha256(path) == artifact["sha256"], f"artifact identity mismatch: {artifact['id']}")
        require(set(artifact.get("members", [])).issubset(artifact_ids), f"artifact member unknown: {artifact['id']}")
        if artifact.get("accessibility_description") is not None:
            require(artifact["accessibility_description"] in artifact_ids, f"accessibility description unknown: {artifact['id']}")
        require(set(artifact.get("receipt_ids", [])).issubset(receipt_ids), f"artifact receipt unknown: {artifact['id']}")
    require(artifact_by_id["art-o002-p01-notebook"]["state"] == "current", "notebook supplement is not current")
    release_state_requirements = {
        "art-o002-reader-html": present.get("bundle") is True or present.get("html") is True,
        "art-o002-reader-pdf": present.get("bundle") is True or present.get("pdf") is True,
        "art-o002-reader-epub": present.get("bundle") is True or present.get("epub") is True,
        "art-o002-source-archive": present.get("bundle") is True,
        "art-o002-offline-bundle": present.get("bundle") is True,
    }
    for artifact_id, should_be_current in release_state_requirements.items():
        expected = "current" if should_be_current else "declared"
        require(artifact_by_id[artifact_id]["state"] == expected, f"release artifact truth wrong: {artifact_id}")

    expected_route_map = {
        "route-o002-u11-a30": ("A30", "core", True, None),
        "route-o002-u11-b30": ("B30", "deferred", False, "gate-o002-u11-b30"),
        "route-o002-u11-b40": ("B40", "deferred", False, "gate-o002-u11-b40"),
        "route-o002-u11-b70": ("B70", "deferred", False, "gate-o002-u11-b70"),
    }
    require(set(route_ids) == set(expected_route_map), "Unit 11 route set is wrong")
    require(
        "sec-o002-u11-scipy-bisection"
        in route_by_id["route-o002-u11-a30"]["sections"],
        "A30 route omits compulsory SciPy bisection section",
    )
    unit11_text = safe_file(unit_by_id["o002.u11"]["reader_path"]).read_text(encoding="utf-8")
    for route in routes:
        expected = expected_route_map[route["id"]]
        actual = (route["prerequisite"], route["status"], route["required_for_b80"], route["gate_id"])
        require(actual == expected, f"route truth wrong: {route['id']}")
        require(set(route["sections"]).issubset(set(unit_by_id["o002.u11"]["sections"])), f"route section unknown: {route['id']}")
        require(set(route["exercises"]).issubset(set(unit_by_id["o002.u11"]["exercises"])), f"route exercise unknown: {route['id']}")
        if route["gate_id"] is not None:
            require(f"{{#{route['gate_id']}" in unit11_text, f"route gate anchor missing: {route['gate_id']}")

    known_nodes = source_ids | component_ids | unit_ids | exercise_ids | artifact_ids | lab_ids | environment_ids | route_ids | {"A30", "B30", "B40", "B70", "pipeline-o002-build"}
    relation_triples = {(relation["type"], relation["from"], relation["to"]) for relation in relations}
    require(len(relation_triples) == len(relations), "duplicate relation")
    for relation in relations:
        require(relation["from"] in known_nodes and relation["to"] in known_nodes, f"relation endpoint unknown: {relation}")
    expected_precedes = {("precedes", first, second) for first, second in zip(REQUIRED_UNIT_IDS, REQUIRED_UNIT_IDS[1:])}
    require({triple for triple in relation_triples if triple[0] == "precedes"} == expected_precedes, "pedagogical precedence topology is wrong")
    for unit in units:
        for component_id in unit["components"]:
            require(("uses_component", unit["id"], component_id) in relation_triples, f"unit/component relation missing: {unit['id']} -> {component_id}")
    for exercise_id in REQUIRED_EXECUTABLE_IDS:
        require(any(kind == "validated_by" and source == exercise_id for kind, source, _ in relation_triples), f"executable exercise lacks validator relation: {exercise_id}")
    for artifact in artifacts:
        require(("produces", artifact["producer"], artifact["id"]) in relation_triples, f"artifact production relation missing: {artifact['id']}")
    for route in routes:
        require(("implements", "o002.u11", route["id"]) in relation_triples, f"route implementation relation missing: {route['id']}")
        require(("requires_prerequisite", route["id"], route["prerequisite"]) in relation_triples, f"route prerequisite relation missing: {route['id']}")

    for record in qa:
        require(set(record["receipt_ids"]).issubset(receipt_ids), f"QA receipt unknown: {record['id']}")
    qa_by_id = {record["id"]: record for record in qa}
    formats_complete = present.get("bundle") is True
    deterministic = present.get("determinism") is True
    accessible = all(present.get(key) is True for key in ("html", "pdf", "epub"))
    published = present.get("publication") is True
    expected_gate_status = {
        "qa-o002-u05-sage-lab": "pass" if sage_complete else "pending",
        "qa-o002-reader-formats-and-bundle": "pass" if formats_complete else "pending",
        "qa-o002-two-clean-builds": "pass" if deterministic else "pending",
        "qa-o002-final-accessibility": "pass" if accessible else "pending",
        "qa-o002-final-publication": "pass" if published else "pending",
    }
    for gate_id, status in expected_gate_status.items():
        require(qa_by_id[gate_id]["status"] == status, f"evidence-driven gate status wrong: {gate_id}")
    require(qa_by_id["qa-o002-final-publication"]["required_for_b80"] is False, "publication gate must not be self-referential B80 evidence")
    require(qa_by_id["qa-o002-final-publication"]["scope"] == "external_preservation", "publication gate scope is wrong")
    required_pending = {record["id"] for record in qa if record["required_for_b80"] and record["status"] == "pending"}
    expected_required_pending = {
        gate_id for gate_id, status in expected_gate_status.items()
        if gate_id != "qa-o002-final-publication" and status == "pending"
    }
    require(required_pending == expected_required_pending, f"pending B80 QA set is wrong: {sorted(required_pending)}")

    b80_complete = not required_pending
    cursor = catalog["cursor"]
    require(cursor["standalone_edition_complete"] is True, "historical standalone truth lost")
    require(cursor["b80_curriculum_complete"] is b80_complete, "B80 completion does not match required evidence")
    require(cursor["admitted_unit_count"] == 14 and cursor["next_unit"] is None, "14-unit cursor topology is wrong")
    expected_next = next((record["id"] for record in qa if record["required_for_b80"] and record["status"] == "pending"), None)
    require(cursor["next_work_item"] == expected_next, "cursor next work item is not the first pending B80 gate")
    require(architecture["status"] == ("complete" if b80_complete else "in_progress"), "architecture status disagrees with gates")
    require(len(architecture["open_requirements"]) == len(required_pending), "open requirement/QA gate count differs")
    if b80_complete:
        require(all(unit["curriculum_status"] == "complete" for unit in units), "B80 complete with unit repairs")
        require(all(lab["status"] == "complete" for lab in labs), "B80 complete with pending labs")

    planned = catalog["planned_release"]
    require(planned["version"] == "2026.08.22.1" and planned["tag"] == "v2026.08.22.1", "planned release identity changed")
    require(planned["record_id"] == RELEASE_RECORD_ID and planned["doi"] == RELEASE_DOI, "planned Zenodo identity changed")
    expected_release_status = "published" if published else "b80_complete" if b80_complete else "in_progress"
    require(planned["status"] == expected_release_status, "planned release status disagrees with evidence")
    require(planned["artifact_ids"] == list(RELEASE_ARTIFACT_PATHS), "planned release artifact set changed")

    print(
        f"backend truth QA passed: 14 ordered units; 75 exercises; "
        f"Sage={'pass' if sage_complete else 'pending'}; "
        f"B80={'complete' if b80_complete else 'in_progress'}; "
        f"publication={'pass' if published else 'pending'}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError) as error:
        print(f"backend truth QA failed: {error}", file=sys.stderr)
        raise SystemExit(1)
