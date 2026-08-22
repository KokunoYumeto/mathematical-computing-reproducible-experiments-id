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


def valid_qmd(unit: int) -> str:
    token = f"{unit:02d}"
    lines = [
        "---",
        f'title: "Unit {unit}"',
        f"identifier: o002.u{token}",
        "---",
        "",
        f"::: {{#sec-o002-u{token}}}",
        ":::",
        "",
        f"## Isi unit {{#sec-o002-u{token}-content}}",
        "",
        "```{python}",
        f"value = {unit}",
        "```",
        "",
        "$$",
        f"x = {unit}",
        "$$",
        "",
    ]
    for exercise in range(1, 6):
        lines.extend(
            [
                f"### Latihan {exercise} {{#ex-o002-u{token}-{exercise:02d}}}",
                "",
                "Pertanyaan.",
                "",
                '::: {.callout-note collapse="true" title="Petunjuk"}',
                "Petunjuk ringkas.",
                ":::",
                "",
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
    for unit in range(1, 13):
        token = f"{unit:02d}"
        (units / f"{token}-unit.qmd").write_text(
            valid_qmd(unit), encoding="utf-8", newline="\n"
        )
        (code / f"unit{token}_example.py").write_text(
            f"VALUE = {unit}\n", encoding="utf-8", newline="\n"
        )
        (tests / f"test_unit{token}.py").write_text(
            "# fixture companion\n", encoding="utf-8", newline="\n"
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

    def test_complete_twelve_unit_fixture_passes(self) -> None:
        self.assertEqual(self.errors(), [])

    def test_every_unit_qmd_is_required(self) -> None:
        (self.root / "source" / "units" / "09-unit.qmd").unlink()
        self.assert_error_contains("unit 09 requires exactly one")
        self.assert_error_contains("exactly 12 QMD files; found 11")

    def test_one_code_and_exact_test_companion_are_required(self) -> None:
        (self.root / "source" / "code" / "unit03_second.py").write_text(
            "VALUE = 3\n", encoding="utf-8", newline="\n"
        )
        (self.root / "tests" / "test_unit04_extra.py").write_text(
            "# duplicate fixture\n", encoding="utf-8", newline="\n"
        )
        self.assert_error_contains("unit 03 requires exactly one source/code/unit03_*.py")
        self.assert_error_contains("unit 04 requires only tests/test_unit04.py")

    def test_yaml_identifier_and_exact_exercise_set(self) -> None:
        path = self.root / "source" / "units" / "02-unit.qmd"
        text = path.read_text(encoding="utf-8")
        text = text.replace("identifier: o002.u02", "identifier: o002.u99")
        text = text.replace("#ex-o002-u02-05", "#ex-o002-u02-06")
        path.write_text(text, encoding="utf-8", newline="\n")
        self.assert_error_contains("must be 'o002.u02'")
        self.assert_error_contains("exercise IDs in source/units/02-unit.qmd must be exactly")

    def test_section_and_exercise_ids_are_globally_unique(self) -> None:
        path = self.root / "source" / "units" / "02-unit.qmd"
        text = path.read_text(encoding="utf-8").replace(
            "#sec-o002-u02-content", "#sec-o002-u01-content"
        )
        path.write_text(text, encoding="utf-8", newline="\n")
        self.assert_error_contains("duplicate global ID 'sec-o002-u01-content'")

    def test_five_hints_and_full_solutions_are_required(self) -> None:
        path = self.root / "source" / "units" / "05-unit.qmd"
        text = path.read_text(encoding="utf-8")
        text = text.replace('title="Petunjuk"', 'title="Catatan"', 1)
        text = text.replace('title="Jawaban dan solusi"', 'title="Jawaban"', 1)
        path.write_text(text, encoding="utf-8", newline="\n")
        self.assert_error_contains("has 4 hint callout(s); expected 5")
        self.assert_error_contains("has 4 full-solution callout(s); expected 5")

    def test_windows_profile_paths_are_rejected_in_authored_files(self) -> None:
        code = self.root / "source" / "code" / "unit06_example.py"
        code.write_text(
            'A = r"C:\\Users\\Example\\data"\nB = "C:/Users/Example/data"\n',
            encoding="utf-8",
            newline="\n",
        )
        self.assert_error_contains("local Windows profile path in source/code/unit06_example.py")

    def test_three_non_ascii_dash_code_points_are_rejected(self) -> None:
        path = self.root / "source" / "units" / "07-unit.qmd"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("non-breaking‑hyphen en–dash em—dash\n")
        errors = self.errors()
        for code_point in ("U+2011", "U+2013", "U+2014"):
            self.assertTrue(any(code_point in error for error in errors), errors)

    def test_unbalanced_fenced_code_block_is_rejected(self) -> None:
        path = self.root / "source" / "units" / "08-unit.qmd"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("```text\nunclosed\n")
        self.assert_error_contains("unbalanced fenced code block")

    def test_unbalanced_display_math_is_rejected(self) -> None:
        path = self.root / "source" / "units" / "10-unit.qmd"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("$$\nx + 1\n")
        self.assert_error_contains("unbalanced display-math delimiter")

    def test_tex_inline_math_delimiters_are_rejected_outside_code(self) -> None:
        path = self.root / "source" / "units" / "10-unit.qmd"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(r"Nilai \(x+1\) tidak portabel." + "\n")
        self.assert_error_contains("unsupported TeX inline-math delimiter")

    def test_english_solution_heading_is_rejected(self) -> None:
        path = self.root / "source" / "units" / "11-unit.qmd"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write("## Solutions\n")
        self.assert_error_contains("obvious English Hint/Answer/Solution heading")

    def test_heading_like_code_is_not_reader_prose(self) -> None:
        path = self.root / "source" / "units" / "11-unit.qmd"
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
