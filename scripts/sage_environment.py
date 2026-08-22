from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
WSL_DISTRIBUTION = "Ubuntu-22.04"
SAGE_EXECUTABLE = "/usr/bin/sage"
LOCK_LINE_RE = re.compile(r"^([^\s=]+)==([^\s]+)$")


def run_wsl(arguments: Sequence[str]) -> str:
    completed = subprocess.run(
        ["wsl.exe", "-d", WSL_DISTRIBUTION, "--", *arguments],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
    )
    return completed.stdout.strip()


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def installed_dpkg_packages() -> dict[str, str]:
    output = run_wsl(["/usr/bin/dpkg-query", "-W"])
    packages: dict[str, str] = {}
    for line_number, line in enumerate(output.splitlines(), start=1):
        fields = line.split("\t")
        if len(fields) != 2:
            raise RuntimeError(f"baris dpkg {line_number} tidak dapat diurai")
        name, version = fields
        if not name or not version:
            raise RuntimeError(f"identitas paket dpkg kosong pada baris {line_number}")
        if name in packages and packages[name] != version:
            raise RuntimeError(f"dua versi paket dpkg terpasang untuk {name}")
        packages[name] = version
    for required in ("sagemath", "python3-sage"):
        if required not in packages:
            raise RuntimeError(f"paket wajib Sage tidak terpasang: {required}")
    return dict(sorted(packages.items()))


def os_release() -> dict[str, str]:
    result: dict[str, str] = {}
    for line in run_wsl(["/usr/bin/cat", "/etc/os-release"]).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key] = value.strip().strip('"')
    return result


def render_lock(packages: dict[str, str]) -> bytes:
    lines = [
        "# O002/B80 exact WSL Sage environment lock",
        f"# Distribution: {WSL_DISTRIBUTION}",
        *[f"{name}=={version}" for name, version in packages.items()],
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def parse_lock(data: bytes) -> dict[str, str]:
    packages: dict[str, str] = {}
    for line_number, raw_line in enumerate(data.decode("utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = LOCK_LINE_RE.fullmatch(line)
        if match is None:
            raise RuntimeError(f"baris lock Sage {line_number} tidak kanonis")
        name, version = match.groups()
        if name in packages:
            raise RuntimeError(f"paket duplikat dalam lock Sage: {name}")
        packages[name] = version
    return dict(sorted(packages.items()))


def build_receipt(
    lock_path: Path,
    lock_data: bytes,
    packages: dict[str, str],
) -> dict[str, object]:
    release = os_release()
    sage_banner = run_wsl([SAGE_EXECUTABLE, "--version"])
    sage_match = re.search(r"SageMath version ([0-9.]+)", sage_banner)
    if sage_match is None:
        raise RuntimeError(f"banner Sage tidak dikenali: {sage_banner}")
    sage_python = run_wsl(
        [SAGE_EXECUTABLE, "-python", "-c", "import platform; print(platform.python_version())"]
    )
    return {
        "schema": "o002.sage-environment.v1",
        "wsl_distribution": WSL_DISTRIBUTION,
        "operating_system": {
            "id": release.get("ID"),
            "version_id": release.get("VERSION_ID"),
            "architecture": run_wsl(["/usr/bin/uname", "-m"]),
        },
        "sage": {
            "version": sage_match.group(1),
            "python": sage_python,
            "apt_packages": {
                "sagemath": packages["sagemath"],
                "python3-sage": packages["python3-sage"],
            },
        },
        "lock": {
            "path": relative_path(lock_path),
            "bytes": len(lock_data),
            "sha256": sha256_bytes(lock_data),
            "installed_package_count": len(packages),
        },
        "matches_runtime": True,
    }


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Freeze or verify the local WSL SageMath environment."
    )
    parser.add_argument("mode", choices=("freeze", "verify"))
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    lock_path = args.lock.resolve()
    receipt_path = args.receipt.resolve()
    relative_path(lock_path)
    relative_path(receipt_path)

    packages = installed_dpkg_packages()
    expected_data = render_lock(packages)
    if args.mode == "freeze":
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_bytes(expected_data)
    else:
        if not lock_path.is_file():
            raise RuntimeError(f"lock Sage tidak ditemukan: {relative_path(lock_path)}")
        actual_data = lock_path.read_bytes()
        if parse_lock(actual_data) != packages:
            raise RuntimeError("lock Sage tidak cocok dengan inventaris dpkg terpasang")
        if actual_data != expected_data:
            raise RuntimeError("byte lock Sage tidak memakai serialisasi kanonis")

    lock_data = lock_path.read_bytes()
    receipt = build_receipt(lock_path, lock_data, packages)
    write_json(receipt_path, receipt)
    print(
        f"Sage environment verified: Sage {receipt['sage']['version']}; "
        f"{len(packages)} dpkg packages; lock SHA-256 {receipt['lock']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
