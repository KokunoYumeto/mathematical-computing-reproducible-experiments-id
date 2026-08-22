from __future__ import annotations

import argparse
import json
from pathlib import Path
import platform
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the complete O002 test suite and write a deterministic receipt."
    )
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()

    receipt_path = args.receipt.resolve()
    try:
        receipt_relative = receipt_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("jalur receipt tes harus berada di dalam lane O002") from exc

    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    receipt = {
        "schema": "o002.test-qa.v1",
        "command": f"python -B scripts/run_tests.py --receipt {receipt_relative}",
        "python": platform.python_version(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expected_failures": len(result.expectedFailures),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "successful": result.wasSuccessful(),
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
