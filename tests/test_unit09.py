from __future__ import annotations

from decimal import Decimal, Inexact, localcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit09_provenance.py"
QMD_PATH = ROOT / "source" / "units" / "09-data-konfigurasi-provenans.qmd"
SPEC = importlib.util.spec_from_file_location("unit09_provenance", MODULE_PATH)
assert SPEC and SPEC.loader
unit09 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit09)


class Unit09ProvenanceTests(unittest.TestCase):
    def test_schema_units_and_derivation_are_explicit(self) -> None:
        unit09.validate_raw_records(unit09.RAW_RECORDS)
        derived = unit09.derive_records(unit09.RAW_RECORDS, 3)
        self.assertEqual(
            [record["mass_per_length_g_per_cm"] for record in derived],
            ["2.000", "2.050", "1.975", "2.050", "1.982"],
        )
        fields = {field["name"]: field["unit"] for field in unit09.RAW_SCHEMA["fields"]}
        self.assertEqual(fields, {"sample_id": None, "length_cm": "cm", "mass_g": "g"})

    def test_schema_rejects_private_fields_and_duplicate_ids(self) -> None:
        private = [dict(unit09.RAW_RECORDS[0], email="person@example.invalid")]
        with self.assertRaisesRegex(ValueError, "privat"):
            unit09.validate_raw_records(private)

        duplicate = [dict(unit09.RAW_RECORDS[0]), dict(unit09.RAW_RECORDS[0])]
        with self.assertRaisesRegex(ValueError, "unik"):
            unit09.validate_raw_records(duplicate)

    def test_schema_rejects_non_string_decimal_values(self) -> None:
        for impostor in (10, 10.0, Decimal("10.0")):
            records = [
                {
                    "sample_id": "S01",
                    "length_cm": impostor,
                    "mass_g": "20.0",
                }
            ]
            with self.subTest(value=repr(impostor)):
                with self.assertRaisesRegex(ValueError, "teks desimal"):
                    unit09.validate_raw_records(records)

    def test_every_serialized_schema_field_has_a_meaning(self) -> None:
        for schema in (unit09.RAW_SCHEMA, unit09.DERIVED_SCHEMA):
            for field in schema["fields"]:
                with self.subTest(schema=schema["schema"], field=field["name"]):
                    self.assertIsInstance(field.get("meaning"), str)
                    self.assertTrue(field["meaning"].strip())

    def test_paths_are_relative_canonical_and_cannot_escape(self) -> None:
        self.assertEqual(
            unit09.safe_relative_path("data/raw/unit09_measurements.csv"),
            "data/raw/unit09_measurements.csv",
        )
        for unsafe in (
            "../secret.csv",
            "/absolute/data.csv",
            "data/../secret.csv",
            "C:/secret.csv",
            "data\\raw\\file.csv",
            "data//raw/file.csv",
        ):
            with self.subTest(path=unsafe):
                with self.assertRaises(ValueError):
                    unit09.safe_relative_path(unsafe)

    def test_artifact_paths_are_unique_under_portable_case_folding(self) -> None:
        same_path = dict(unit09.DEFAULT_CONFIG)
        same_path["derived_path"] = same_path["raw_path"]
        with self.assertRaisesRegex(ValueError, "unik secara portabel"):
            unit09.build_manifest(same_path)

        case_alias = dict(unit09.DEFAULT_CONFIG)
        case_alias["derived_path"] = case_alias["raw_path"].upper()
        with self.assertRaisesRegex(ValueError, "unik secara portabel"):
            unit09.build_manifest(case_alias)

        fixed_role_alias = dict(unit09.DEFAULT_CONFIG)
        fixed_role_alias["raw_path"] = "SOURCE/CODE/UNIT09_PROVENANCE.PY"
        with self.assertRaisesRegex(ValueError, "unik secara portabel"):
            unit09.build_manifest(fixed_role_alias)

    def test_decimal_context_is_explicit_recorded_and_ambient_independent(self) -> None:
        records = (
            {
                "sample_id": "S01",
                "length_cm": "10000000",
                "mass_g": "4445001",
            },
        )
        with localcontext() as ambient:
            ambient.prec = 4
            ambient.traps[Inexact] = True
            constrained = unit09.build_manifest(raw_records=records)
        with localcontext() as ambient:
            ambient.prec = 50
            ambient.traps[Inexact] = False
            generous = unit09.build_manifest(raw_records=records)

        self.assertEqual(constrained, generous)
        self.assertEqual(
            constrained["datasets"]["derived"]["records"][0][
                "mass_per_length_g_per_cm"
            ],
            "0.445",
        )
        identity = constrained["environment_identity"]["decimal_context"]
        self.assertEqual(identity["precision"], 28)
        self.assertEqual(identity["rounding"], "ROUND_HALF_EVEN")
        self.assertEqual(
            identity["traps"],
            ["DivisionByZero", "InvalidOperation", "Overflow"],
        )

    def test_artifact_hashes_sizes_rights_and_lineage_match_bytes(self) -> None:
        manifest = unit09.build_manifest()
        config = manifest["configuration"]
        derived = unit09.derive_records(unit09.RAW_RECORDS, config["ratio_decimal_places"])
        expected_payloads = {
            "raw_data": unit09.canonical_csv_bytes(unit09.RAW_RECORDS, unit09.RAW_FIELDS),
            "derived_data": unit09.canonical_csv_bytes(derived, unit09.DERIVED_FIELDS),
            "configuration": unit09.canonical_json_bytes(config),
            "environment_lock": unit09.canonical_json_bytes(
                manifest["environment_identity"]
            ),
            "code": MODULE_PATH.read_bytes(),
        }
        for role, payload in expected_payloads.items():
            binding = manifest["artifacts"][role]
            self.assertEqual(binding["bytes"], len(payload))
            self.assertEqual(binding["sha256"], hashlib.sha256(payload).hexdigest())
        self.assertEqual(
            manifest["lineage"]["output"],
            manifest["artifacts"]["derived_data"]["sha256"],
        )
        self.assertEqual(manifest["artifacts"]["code"]["rights"]["license"], "MIT")
        self.assertFalse(
            manifest["artifacts"]["raw_data"]["rights"]["third_party_material"]
        )

    def test_configuration_changes_derivation_without_changing_raw_bytes(self) -> None:
        default_manifest = unit09.build_manifest()
        changed_config = dict(unit09.DEFAULT_CONFIG)
        changed_config["ratio_decimal_places"] = 2
        changed_manifest = unit09.build_manifest(changed_config)
        self.assertEqual(
            default_manifest["artifacts"]["raw_data"]["sha256"],
            changed_manifest["artifacts"]["raw_data"]["sha256"],
        )
        self.assertNotEqual(
            default_manifest["artifacts"]["configuration"]["sha256"],
            changed_manifest["artifacts"]["configuration"]["sha256"],
        )
        self.assertNotEqual(
            default_manifest["artifacts"]["derived_data"]["sha256"],
            changed_manifest["artifacts"]["derived_data"]["sha256"],
        )

    def test_canonical_manifest_is_repeatable_and_core_hash_is_valid(self) -> None:
        manifest = unit09.build_manifest()
        core = dict(manifest)
        recorded_hash = core.pop("core_sha256")
        self.assertEqual(
            recorded_hash,
            hashlib.sha256(unit09.canonical_json_bytes(core)).hexdigest(),
        )
        self.assertTrue(manifest["environment_identity"]["stdlib_only"])
        self.assertEqual(manifest["environment_identity"]["external_dependencies"], [])
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            unit09.write_manifest(manifest, first)
            unit09.write_manifest(manifest, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            parsed = json.loads(first.read_text(encoding="utf-8"))
        self.assertEqual(parsed["schema"], unit09.SCHEMA)
        self.assertIn("semantic_reproducibility", parsed["reproducibility"])

    def test_reader_command_is_portable_and_uses_natural_terminology(self) -> None:
        source = QMD_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "python source/code/unit09_provenance.py --output "
            "output/unit09-manifest.json",
            source,
        )
        self.assertNotRegex(source, r"(?m)^python .*\\$")
        self.assertNotRegex(source, r"(?i)\bpipa\b")


if __name__ == "__main__":
    unittest.main()
