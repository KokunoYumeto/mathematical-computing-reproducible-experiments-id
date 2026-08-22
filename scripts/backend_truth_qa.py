from __future__ import annotations

import json
from pathlib import Path
import sys

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> int:
    schema = json.loads((ROOT / "backend" / "catalog.schema.json").read_text(encoding="utf-8"))
    catalog = json.loads((ROOT / "backend" / "catalog.json").read_text(encoding="utf-8"))
    cursor = json.loads((ROOT / "00_control" / "CURRENT_CURSOR.json").read_text(encoding="utf-8"))

    errors = sorted(
        Draft202012Validator(schema).iter_errors(catalog),
        key=lambda error: list(error.path),
    )
    require(
        not errors,
        "backend schema failure: "
        + "; ".join(f"{list(error.path)}: {error.message}" for error in errors),
    )

    required = ["o002.p01", "o002.p02", *[f"o002.u{number:02d}" for number in range(1, 13)]]
    admitted = [f"o002.u{number:02d}" for number in range(1, 13)]
    repair_ids = {
        unit["id"]
        for unit in catalog["units"]
        if unit["curriculum_status"] == "repair_required"
    }

    require(catalog["schema_version"] == "o002.backend.v2", "backend must use v2 truth schema")
    require(catalog["architecture"]["required_unit_ids"] == required, "selected unit order is wrong")
    require(catalog["architecture"]["admitted_unit_ids"] == admitted, "admitted boundary is wrong")
    require(catalog["architecture"]["status"] == "in_progress", "architecture must remain in progress")
    require(len(catalog["architecture"]["open_requirements"]) > 0, "open requirements missing")
    require(len(catalog["units"]) == 12, "truth checkpoint must retain exactly 12 admitted units")
    require(sum(len(unit["exercises"]) for unit in catalog["units"]) == 60, "historical exercises changed")
    require(repair_ids == {"o002.u04", "o002.u05", "o002.u06", "o002.u11"}, "repair set is wrong")

    backend_cursor = catalog["cursor"]
    require(backend_cursor["standalone_edition_complete"] is True, "standalone release truth lost")
    require(backend_cursor["b80_curriculum_complete"] is False, "premature B80 completion claim")
    require(backend_cursor["next_unit"] == "o002.p01", "next unit must be P01")
    require(backend_cursor["admitted_unit_count"] == 12, "backend admitted count is wrong")
    require(cursor["historical_release"]["standalone_edition_complete"] is True, "control release truth lost")
    require(cursor["b80_curriculum_complete"] is False, "control prematurely claims B80 complete")
    require(cursor["active_block"] == ["o002.p01"], "control active block must be P01")

    print(
        "backend truth QA passed: v2; standalone complete; B80 incomplete; "
        "12/14 admitted; P01 next; Units 4/5/6/11 require repair"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(f"backend truth QA failed: {error}", file=sys.stderr)
        raise SystemExit(1)
