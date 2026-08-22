from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from typing import Iterable


def scale_vector(scalar: int | Fraction, vector: Iterable[int | Fraction]) -> tuple[int | Fraction, ...]:
    return tuple(scalar * component for component in vector)


def mean_fraction(values: Iterable[int | Fraction]) -> Fraction:
    frozen = tuple(Fraction(value) for value in values)
    if not frozen:
        raise ValueError("values tidak boleh kosong")
    return sum(frozen, start=Fraction(0)) / len(frozen)


def least_nonnegative_residue(a: int, modulus: int) -> int:
    if not isinstance(a, int) or not isinstance(modulus, int):
        raise TypeError("a dan modulus harus bilangan bulat")
    if modulus <= 0:
        raise ValueError("modulus harus positif")
    return a % modulus


def canonical_json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def build_results() -> dict[str, object]:
    vector = (2, -1, 4)
    scaled = scale_vector(3, vector)
    payload: dict[str, object] = {
        "schema": "o002.unit02-results.v1",
        "mean": str(mean_fraction([Fraction(1, 3), Fraction(1, 2)])),
        "residue": least_nonnegative_residue(-17, 5),
        "scale": {
            "input": list(vector),
            "output": list(scaled),
            "input_unchanged": vector == (2, -1, 4),
            "length_preserved": len(vector) == len(scaled),
        },
    }
    canonical = canonical_json_bytes(payload)
    payload["payload_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_json_bytes(build_results()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
