from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import re
from typing import Sequence

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name


ROOT = Path(__file__).resolve().parents[1]
DIRECT_ROOTS = (
    "ipykernel",
    "ipython",
    "jsonschema",
    "jupyter-client",
    "jupyter-core",
    "jupyterlab",
    "matplotlib",
    "nbclient",
    "nbformat",
    "numpy",
    "notebook",
    "scipy",
    "sympy",
)
LOCK_LINE_RE = re.compile(r"^([a-z0-9][a-z0-9._-]*)==([^\s]+)$")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def relative_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def installed_distributions() -> dict[str, list[metadata.Distribution]]:
    result: dict[str, list[metadata.Distribution]] = {}
    for distribution in metadata.distributions():
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            raise RuntimeError("distribusi Python tanpa medan Name")
        name = canonicalize_name(raw_name)
        result.setdefault(name, []).append(distribution)
    return result


def selected_distribution(
    installed: dict[str, list[metadata.Distribution]],
    name: str,
) -> metadata.Distribution | None:
    candidates = installed.get(name, [])
    if not candidates:
        return None
    versions = {candidate.version for candidate in candidates}
    if len(versions) != 1:
        raise RuntimeError(
            f"closure memerlukan {name}, tetapi beberapa versi terpasang: "
            f"{sorted(versions)}"
        )
    return candidates[0]


def dependency_closure(
    installed: dict[str, list[metadata.Distribution]],
) -> tuple[dict[str, str], list[dict[str, str]]]:
    pending = [canonicalize_name(name) for name in DIRECT_ROOTS]
    selected: dict[str, str] = {}
    edges: list[dict[str, str]] = []
    while pending:
        name = pending.pop()
        if name in selected:
            continue
        distribution = selected_distribution(installed, name)
        if distribution is None:
            raise RuntimeError(f"dependensi langsung atau transitif tidak terpasang: {name}")
        selected[name] = distribution.version
        for raw_requirement in distribution.requires or ():
            requirement = Requirement(raw_requirement)
            if requirement.marker is not None and not requirement.marker.evaluate(
                {"extra": ""}
            ):
                continue
            dependency = canonicalize_name(requirement.name)
            dependency_distribution = selected_distribution(installed, dependency)
            if dependency_distribution is None:
                raise RuntimeError(
                    f"{name} memerlukan {dependency}, tetapi distribusinya tidak terpasang"
                )
            if requirement.specifier and dependency_distribution.version not in requirement.specifier:
                raise RuntimeError(
                    f"{name} memerlukan {dependency}{requirement.specifier}, "
                    f"tetapi versi terpasang {dependency_distribution.version}"
                )
            edges.append({"from": name, "to": dependency})
            pending.append(dependency)
    edges.sort(key=lambda item: (item["from"], item["to"]))
    return dict(sorted(selected.items())), edges


def render_lock(packages: dict[str, str]) -> bytes:
    lines = [
        "# O002/B80 resolved Python environment lock",
        "# Generated from declared roots; names are PEP 503 normalized.",
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
            raise RuntimeError(f"baris lock {line_number} tidak kanonis: {raw_line!r}")
        name = canonicalize_name(match.group(1))
        if name in packages:
            raise RuntimeError(f"paket duplikat dalam lock: {name}")
        packages[name] = match.group(2)
    return dict(sorted(packages.items()))


def build_receipt(
    lock_path: Path,
    lock_data: bytes,
    packages: dict[str, str],
    edges: list[dict[str, str]],
) -> dict[str, object]:
    return {
        "schema": "o002.python-environment.v1",
        "python": {
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "direct_roots": list(DIRECT_ROOTS),
        "lock": {
            "path": relative_path(lock_path),
            "bytes": len(lock_data),
            "sha256": sha256_bytes(lock_data),
        },
        "package_count": len(packages),
        "packages": [
            {"name": name, "version": version}
            for name, version in packages.items()
        ],
        "dependency_edges": edges,
        "closure_complete": True,
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
        description="Freeze or verify the complete O002 Python dependency closure."
    )
    parser.add_argument("mode", choices=("freeze", "verify"))
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    lock_path = args.lock.resolve()
    receipt_path = args.receipt.resolve()
    relative_path(lock_path)
    relative_path(receipt_path)

    packages, edges = dependency_closure(installed_distributions())
    expected_data = render_lock(packages)
    if args.mode == "freeze":
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        lock_path.write_bytes(expected_data)
    else:
        if not lock_path.is_file():
            raise RuntimeError(f"lock tidak ditemukan: {relative_path(lock_path)}")
        actual_data = lock_path.read_bytes()
        locked_packages = parse_lock(actual_data)
        if locked_packages != packages:
            missing = sorted(set(packages) - set(locked_packages))
            extra = sorted(set(locked_packages) - set(packages))
            changed = sorted(
                name
                for name in set(packages) & set(locked_packages)
                if packages[name] != locked_packages[name]
            )
            raise RuntimeError(
                f"lock tidak cocok dengan closure runtime: missing={missing}, "
                f"extra={extra}, changed={changed}"
            )
        if actual_data != expected_data:
            raise RuntimeError("byte lock tidak memakai serialisasi kanonis")

    lock_data = lock_path.read_bytes()
    receipt = build_receipt(lock_path, lock_data, packages, edges)
    write_json(receipt_path, receipt)
    print(
        f"Python environment verified: {len(packages)} packages; "
        f"lock SHA-256 {receipt['lock']['sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
