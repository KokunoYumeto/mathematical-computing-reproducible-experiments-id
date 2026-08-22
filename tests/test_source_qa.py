from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
from io import StringIO
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "source_qa.py"
SPEC = importlib.util.spec_from_file_location("source_qa", MODULE_PATH)
assert SPEC and SPEC.loader
source_qa = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source_qa)


def spec_for(token: str) -> dict[str, object]:
    return next(spec for spec in source_qa.UNIT_SPECS if spec["token"] == token)


def valid_qmd(spec: dict[str, object]) -> str:
    token = str(spec["token"])
    identifier = str(spec["identifier"])
    exercise_count = int(spec["exercise_count"])
    check_count = int(spec["check_count"])
    lines = [
        "---",
        f'title: "Unit {token}"',
        f"identifier: {identifier}",
        "---",
        "",
        f"::: {{#sec-o002-{token}}}",
        ":::",
        "",
        f"## Isi unit {{#sec-o002-{token}-content}}",
        "",
        "```{python}",
        "value = 1",
        "```",
        "",
        "$$",
        "x = 1",
        "$$",
        "",
    ]
    exercise_ids = [
        f"ex-o002-{token}-{exercise:02d}"
        for exercise in range(1, exercise_count + 1)
    ]
    exercise_ids.extend(str(item) for item in spec.get("extra_exercises", ()))
    for exercise, exercise_id in enumerate(exercise_ids, start=1):
        lines.extend(
            [
                f"### Latihan {exercise} {{#{exercise_id}}}",
                "",
                "Pertanyaan.",
                "",
                '::: {.callout-note collapse="true" title="Petunjuk"}',
                "Petunjuk ringkas.",
                ":::",
                "",
            ]
        )
        if exercise <= check_count:
            lines.extend(
                [
                    '::: {.callout-important title="Pemeriksaan mandiri"}',
                    "Pemeriksaan dapat dijalankan.",
                    ":::",
                    "",
                ]
            )
        lines.extend(
            [
                '::: {.callout-tip collapse="true" title="Jawaban dan solusi"}',
                "Jawaban lengkap.",
                ":::",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def create_valid_lane(root: Path) -> None:
    units = root / "source" / "units"
    code = root / "source" / "code"
    tests = root / "tests"
    units.mkdir(parents=True)
    code.mkdir(parents=True)
    tests.mkdir(parents=True)
    for index, spec in enumerate(source_qa.UNIT_SPECS, start=1):
        (units / str(spec["qmd"])).write_text(
            valid_qmd(spec), encoding="utf-8", newline="\n"
        )
        (code / str(spec["code"])).write_text(
            f"VALUE = {index}\n", encoding="utf-8", newline="\n"
        )
        (tests / str(spec["test"])).write_text(
            "# fixture companion\n", encoding="utf-8", newline="\n"
        )
    (tests / "test_source_qa.py").write_text(
        "# infrastructure fixture\n", encoding="utf-8", newline="\n"
    )
    (code / "unit05_sage_lab.py").write_text(
        "VALUE = 5\n", encoding="utf-8", newline="\n"
    )
    for test_name in (
        "test_notebook_supplement.py",
        "test_release_tooling.py",
        "test_unit05_sage.py",
    ):
        (tests / test_name).write_text(
            "# additional fixture companion\n", encoding="utf-8", newline="\n"
        )


class SourceQATests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        create_valid_lane(self.root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def errors(self) -> list[str]:
        return source_qa.inspect_lane(self.root)

    def assert_error_contains(self, fragment: str) -> None:
        errors = self.errors()
        self.assertTrue(
            any(fragment in error for error in errors),
            msg=f"expected fragment {fragment!r} in errors: {errors}",
        )

    def test_complete_fourteen_unit_fixture_passes(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_every_unit_qmd_is_required(self) -> None:
        (self.root / "source" / "units" / str(spec_for("u09")["qmd"])).unlink()
        self.assert_error_contains("source/units closure mismatch")
        self.assert_error_contains(str(spec_for("u09")["qmd"]))

    def test_one_code_and_exact_test_companion_are_required(self) -> None:
        (self.root / "source" / "code" / "unit03_second.py").write_text(
            "VALUE = 3\n", encoding="utf-8", newline="\n"
        )
        (self.root / "tests" / "test_unit04_extra.py").write_text(
            "# duplicate fixture\n", encoding="utf-8", newline="\n"
        )
        self.assert_error_contains("source/code closure mismatch")
        self.assert_error_contains("unit03_second.py")
        self.assert_error_contains("tests closure mismatch")
        self.assert_error_contains("test_unit04_extra.py")

    def test_yaml_identifier_and_exact_exercise_set(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u02")["qmd"])
        text = path.read_text(encoding="utf-8")
        text = text.replace("identifier: o002.u02", "identifier: o002.u99")
        text = text.replace("#ex-o002-u02-05", "#ex-o002-u02-06")
        path.write_text(text, encoding="utf-8", newline="\n")
        self.assert_error_contains("must be 'o002.u02'")
        self.assert_error_contains(
            f"exercise IDs in source/units/{spec_for('u02')['qmd']} must be exactly"
        )

    def test_section_and_exercise_ids_are_globally_unique(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u02")["qmd"])
        text = path.read_text(encoding="utf-8").replace(
            "#sec-o002-u02-content", "#sec-o002-u01-content"
        )
        path.write_text(text, encoding="utf-8", newline="\n")
        self.assert_error_contains("duplicate global ID 'sec-o002-u01-content'")

    def test_five_hints_and_full_solutions_are_required(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u03")["qmd"])
        text = path.read_text(encoding="utf-8")
        text = text.replace('title="Petunjuk"', 'title="Catatan"', 1)
        text = text.replace('title="Jawaban dan solusi"', 'title="Jawaban"', 1)
        path.write_text(text, encoding="utf-8", newline="\n")
        self.assert_error_contains("has 4 hint callout(s); expected 5")
        self.assert_error_contains("has 4 full-solution callout(s); expected 5")

    def test_windows_profile_paths_are_rejected_in_authored_files(self) -> None:
        code = self.root / "source" / "code" / str(spec_for("u06")["code"])
        code.write_text(
            'A = r"C:\\Users\\Example\\data"\nB = "C:/Users/Example/data"\n',
            encoding="utf-8",
            newline="\n",
        )
        self.assert_error_contains(
            f"local Windows profile path in source/code/{spec_for('u06')['code']}"
        )

    def test_three_non_ascii_dash_code_points_are_rejected(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u07")["qmd"])
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("non-breaking‑hyphen en–dash em—dash\n")
        errors = self.errors()
        for code_point in ("U+2011", "U+2013", "U+2014"):
            self.assertTrue(any(code_point in error for error in errors), errors)

    def test_unbalanced_fenced_code_block_is_rejected(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u08")["qmd"])
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("```text\nunclosed\n")
        self.assert_error_contains("unbalanced fenced code block")

    def test_unbalanced_display_math_is_rejected(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u10")["qmd"])
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("$$\nx + 1\n")
        self.assert_error_contains("unbalanced display-math delimiter")

    def test_tex_inline_math_delimiters_are_rejected_outside_code(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u10")["qmd"])
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(r"Nilai \(x+1\) tidak portabel." + "\n")
        self.assert_error_contains("unsupported TeX inline-math delimiter")

    def test_english_solution_heading_is_rejected(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u11")["qmd"])
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("## Solutions\n")
        self.assert_error_contains("obvious English Hint/Answer/Solution heading")

    def test_heading_like_code_is_not_reader_prose(self) -> None:
        path = self.root / "source" / "units" / str(spec_for("u11")["qmd"])
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(
                "```text\n"
                "## Solution\n"
                '::: {.callout-note title="Hint"}\n'
                "{#sec-o002-u01-content}\n"
                "solutions\n"
                "```\n"
            )
        self.assertEqual(self.errors(), [])

    def test_cli_exit_status_tracks_validation(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(source_qa.main(["--root", str(self.root)]), 0)
        self.assertIn("source QA passed", stdout.getvalue())

        (self.root / "tests" / "test_unit12.py").unlink()
        stdout = StringIO()
        stderr = StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            self.assertEqual(source_qa.main(["--root", str(self.root)]), 1)
        self.assertIn("source QA failed", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
