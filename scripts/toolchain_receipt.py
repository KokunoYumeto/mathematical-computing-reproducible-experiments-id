from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import re
import subprocess
import sys


def first_output_line(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    if not output:
        raise RuntimeError(f"perintah tidak menghasilkan versi: {command[0]}")
    return output.splitlines()[0].strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    quarto_version = first_output_line(["quarto", "--version"])
    lualatex_banner = first_output_line(["lualatex", "--version"])
    match = re.search(r"LuaHBTeX, Version ([0-9.]+) \(MiKTeX ([0-9.]+)\)", lualatex_banner)
    if match is None:
        raise RuntimeError(f"banner LuaLaTeX tidak dikenali: {lualatex_banner}")

    receipt = {
        "schema": "o002.toolchain-qa.v1",
        "python": platform.python_version(),
        "quarto": quarto_version,
        "luahbtex": match.group(1),
        "miktex": match.group(2),
        "expected": {
            "python": "3.13.1",
            "quarto": "1.9.37",
            "luahbtex": "1.25.7",
            "miktex": "26.5",
        },
    }
    receipt["matches_expected"] = all(
        receipt[key] == value for key, value in receipt["expected"].items()
    )
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if receipt["matches_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
