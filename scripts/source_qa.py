from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import sys
from typing import Iterable, Sequence


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_UNITS = tuple(range(1, 13))

ID_RE = re.compile(r"\{#((?:sec|ex)-[-A-Za-z0-9_.:]+)(?=[\s}])")
YAML_IDENTIFIER_RE = re.compile(r"^\s*identifier\s*:\s*(.*?)\s*$")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
CALLOUT_TITLE_RE = re.compile(
    r"^[ \t]*:{3,}[ \t]*\{(?=[^}\n]*\.callout-)[^}\n]*"
    r"\btitle[ \t]*=[ \t]*(?:\"([^\"\n]*)\"|'([^'\n]*)')[^}\n]*\}[ \t]*$",
    re.MULTILINE,
)
PROFILE_PATH_RE = re.compile(r"c:(?:\\+|/+)users(?:\\+|/+)", re.IGNORECASE)
ENGLISH_MARKDOWN_HEADING_RE = re.compile(
    r"^[ \t]{0,3}#{1,6}[ \t]+(?:hints?|answers?|solutions?)\b",
    re.IGNORECASE | re.MULTILINE,
)
ENGLISH_STANDALONE_LABEL_RE = re.compile(
    r"^[ \t]*(?:\*\*|__)?(?:hints?|answers?|solutions?)"
    r"(?:[ \t]+(?:and|&)[ \t]+(?:answers?|solutions?))?"
    r"(?:\*\*|__)?[ \t]*:?[ \t]*(?:\{[^}\n]*\})?[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)
ENGLISH_CALLOUT_TITLE_RE = re.compile(
    r"\btitle[ \t]*=[ \t]*['\"][ \t]*(?:hints?|answers?|solutions?)\b",
    re.IGNORECASE,
)
ENGLISH_SUMMARY_RE = re.compile(
    r"<summary>[ \t]*(?:hints?|answers?|solutions?)\b[^<]*</summary>",
    re.IGNORECASE,
)
FORBIDDEN_DASHES = {
    "\u2011": "U+2011 non-breaking hyphen",
    "\u2013": "U+2013 en dash",
    "\u2014": "U+2014 em dash",
}


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _read_utf8(path: Path, root: Path, errors: list[str]) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        errors.append(f"cannot read UTF-8 source {_relative(path, root)}: {exc}")
        return None


def _yaml_identifier(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    closing = next(
        (index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"),
        None,
    )
    if closing is None:
        return None
    values: list[str] = []
    for line in lines[1:closing]:
        match = YAML_IDENTIFIER_RE.match(line)
        if match:
            values.append(match.group(1).strip().strip("'\""))
    return values[0] if len(values) == 1 else None


def _id_occurrences(text: str) -> Iterable[tuple[str, int]]:
    for match in ID_RE.finditer(text):
        yield match.group(1), text.count("\n", 0, match.start()) + 1


def _unescaped_display_delimiters(line: str) -> Iterable[int]:
    index = 0
    while index + 1 < len(line):
        if line[index : index + 2] != "$$":
            index += 1
            continue
        preceding_backslashes = 0
        cursor = index - 1
        while cursor >= 0 and line[cursor] == "\\":
            preceding_backslashes += 1
            cursor -= 1
        if preceding_backslashes % 2 == 0:
            yield index + 1
        index += 2


def _outside_fenced_code(text: str) -> str:
    """Keep prose and line numbering while blanking fenced blocks."""

    output: list[str] = []
    open_fence: tuple[str, int] | None = None
    for raw_line in text.splitlines(keepends=True):
        line = raw_line.rstrip("\r\n")
        line_ending = raw_line[len(line) :]
        fence = FENCE_RE.match(line)
        if open_fence is not None:
            marker_character, marker_length = open_fence
            if fence:
                marker, trailing = fence.groups()
                if (
                    marker[0] == marker_character
                    and len(marker) >= marker_length
                    and not trailing.strip()
                ):
                    open_fence = None
            output.append(line_ending)
            continue
        if fence:
            marker, _ = fence.groups()
            open_fence = (marker[0], len(marker))
            output.append(line_ending)
            continue
        output.append(raw_line)
    return "".join(output)


def _delimiter_errors(text: str, label: str) -> list[str]:
    errors: list[str] = []
    open_fence: tuple[str, int, int] | None = None
    open_math: tuple[int, int] | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        fence = FENCE_RE.match(line)
        if open_fence is not None:
            marker_character, marker_length, opening_line = open_fence
            if fence:
                marker, trailing = fence.groups()
                if (
                    marker[0] == marker_character
                    and len(marker) >= marker_length
                    and not trailing.strip()
                ):
                    open_fence = None
            continue

        if fence:
            marker, _ = fence.groups()
            open_fence = (marker[0], len(marker), line_number)
            continue

        for column in _unescaped_display_delimiters(line):
            if open_math is None:
                open_math = (line_number, column)
            else:
                open_math = None

    if open_fence is not None:
        errors.append(
            f"unbalanced fenced code block in {label}: opened at line {open_fence[2]}"
        )
    if open_math is not None:
        errors.append(
            f"unbalanced display-math delimiter in {label}: opened at "
            f"line {open_math[0]}, column {open_math[1]}"
        )
    return errors


def _callout_titles(text: str) -> list[str]:
    titles: list[str] = []
    for match in CALLOUT_TITLE_RE.finditer(text):
        titles.append(match.group(1) if match.group(1) is not None else match.group(2))
    return titles


def _check_authored_text(path: Path, text: str, root: Path) -> list[str]:
    errors: list[str] = []
    label = _relative(path, root)
    profile_match = PROFILE_PATH_RE.search(text)
    if profile_match:
        line = text.count("\n", 0, profile_match.start()) + 1
        errors.append(f"local Windows profile path in {label}:{line}")
    for character, description in FORBIDDEN_DASHES.items():
        if character in text:
            first = text.index(character)
            line = text.count("\n", 0, first) + 1
            count = text.count(character)
            errors.append(
                f"forbidden {description} in {label}:{line} ({count} occurrence(s))"
            )
    return errors


def _check_qmd(path: Path, text: str, unit: int, root: Path) -> list[str]:
    errors: list[str] = []
    label = _relative(path, root)
    unit_token = f"{unit:02d}"
    expected_identifier = f"o002.u{unit_token}"
    actual_identifier = _yaml_identifier(text)
    if actual_identifier != expected_identifier:
        errors.append(
            f"YAML identifier in {label} must be {expected_identifier!r}; "
            f"found {actual_identifier!r}"
        )

    structural_text = _outside_fenced_code(text)
    for delimiter in (r"\(", r"\)"):
        if delimiter in structural_text:
            first = structural_text.index(delimiter)
            line = structural_text.count("\n", 0, first) + 1
            errors.append(
                f"unsupported TeX inline-math delimiter {delimiter!r} in {label}:{line}; "
                "use dollar delimiters for portable HTML/PDF rendering"
            )
    actual_exercises = [
        identifier
        for identifier, _ in _id_occurrences(structural_text)
        if identifier.startswith("ex-")
    ]
    expected_exercises = [f"ex-o002-u{unit_token}-{index:02d}" for index in range(1, 6)]
    if Counter(actual_exercises) != Counter(expected_exercises):
        actual_counts = Counter(actual_exercises)
        expected_counts = Counter(expected_exercises)
        missing = sorted((expected_counts - actual_counts).elements())
        unexpected = sorted((actual_counts - expected_counts).elements())
        errors.append(
            f"exercise IDs in {label} must be exactly {', '.join(expected_exercises)}; "
            f"missing={missing}, unexpected={unexpected}"
        )

    titles = _callout_titles(structural_text)
    hint_count = titles.count("Petunjuk")
    solution_count = titles.count("Jawaban dan solusi")
    if hint_count != 5:
        errors.append(f"{label} has {hint_count} hint callout(s); expected 5")
    if solution_count != 5:
        errors.append(f"{label} has {solution_count} full-solution callout(s); expected 5")

    errors.extend(_delimiter_errors(text, label))
    if (
        ENGLISH_MARKDOWN_HEADING_RE.search(structural_text)
        or ENGLISH_STANDALONE_LABEL_RE.search(structural_text)
        or ENGLISH_CALLOUT_TITLE_RE.search(structural_text)
        or ENGLISH_SUMMARY_RE.search(structural_text)
    ):
        errors.append(f"obvious English Hint/Answer/Solution heading in {label}")
    return errors


def inspect_lane(root: Path) -> list[str]:
    root = Path(root).resolve()
    units_directory = root / "source" / "units"
    code_directory = root / "source" / "code"
    tests_directory = root / "tests"
    errors: list[str] = []

    for directory in (units_directory, code_directory, tests_directory):
        if not directory.is_dir():
            errors.append(f"required directory missing: {_relative(directory, root)}")

    qmd_files = sorted(
        (path for path in units_directory.glob("*.qmd") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )
    code_files = sorted(
        (path for path in code_directory.glob("unit[0-9][0-9]_*.py") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )
    test_files = sorted(
        (path for path in tests_directory.glob("test_unit[0-9][0-9]*.py") if path.is_file()),
        key=lambda path: path.name.casefold(),
    )

    if len(qmd_files) != len(EXPECTED_UNITS):
        errors.append(
            f"source/units must contain exactly 12 QMD files; found {len(qmd_files)}"
        )

    qmd_by_unit: dict[int, Path] = {}
    for unit in EXPECTED_UNITS:
        token = f"{unit:02d}"
        qmd_matches = [
            path for path in qmd_files if re.fullmatch(rf"{token}-.+\.qmd", path.name)
        ]
        code_matches = [path for path in code_files if path.name.startswith(f"unit{token}_")]
        expected_test_name = f"test_unit{token}.py"
        test_matches = [
            path for path in test_files if path.name.startswith(f"test_unit{token}")
        ]
        if len(qmd_matches) != 1:
            errors.append(
                f"unit {token} requires exactly one source/units/{token}-*.qmd; "
                f"found {[path.name for path in qmd_matches]}"
            )
        else:
            qmd_by_unit[unit] = qmd_matches[0]
        if len(code_matches) != 1:
            errors.append(
                f"unit {token} requires exactly one source/code/unit{token}_*.py; "
                f"found {[path.name for path in code_matches]}"
            )
        if [path.name for path in test_matches] != [expected_test_name]:
            errors.append(
                f"unit {token} requires only tests/{expected_test_name}; "
                f"found {[path.name for path in test_matches]}"
            )

    authored_files = sorted(
        {*qmd_files, *code_files, *test_files},
        key=lambda path: _relative(path, root).casefold(),
    )
    texts: dict[Path, str] = {}
    for path in authored_files:
        text = _read_utf8(path, root, errors)
        if text is not None:
            texts[path] = text
            errors.extend(_check_authored_text(path, text, root))

    occurrences: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for path in qmd_files:
        text = texts.get(path)
        if text is None:
            continue
        for identifier, line in _id_occurrences(_outside_fenced_code(text)):
            occurrences[identifier].append((path, line))
    for identifier in sorted(occurrences, key=str.casefold):
        locations = occurrences[identifier]
        if len(locations) > 1:
            rendered = ", ".join(
                f"{_relative(path, root)}:{line}" for path, line in locations
            )
            errors.append(f"duplicate global ID {identifier!r}: {rendered}")

    for unit, path in sorted(qmd_by_unit.items()):
        text = texts.get(path)
        if text is not None:
            errors.extend(_check_qmd(path, text, unit, root))

    return sorted(errors, key=str.casefold)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the closed 12-unit O002 authored-source structure."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="lane root (defaults to the project containing this script)",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        help="write a deterministic machine-readable receipt on success",
    )
    args = parser.parse_args(argv)
    errors = inspect_lane(args.root)
    if errors:
        print(f"source QA failed with {len(errors)} error(s):", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if args.receipt is not None:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(
            json.dumps(
                {
                    "schema": "o002.source-qa.v1",
                    "successful": True,
                    "unit_triplets": len(EXPECTED_UNITS),
                    "errors": 0,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print("source QA passed: 12 unit triplets and authored-source invariants are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
