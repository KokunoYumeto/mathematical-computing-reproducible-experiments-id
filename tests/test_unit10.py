from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "source" / "code" / "unit10_pipeline.py"
SPEC = importlib.util.spec_from_file_location("unit10_pipeline", MODULE_PATH)
assert SPEC and SPEC.loader
unit10 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(unit10)


class Unit10PipelineTests(unittest.TestCase):
    def test_topological_order_respects_dependencies(self) -> None:
        graph = {"data": [], "fit": ["data"], "plot": ["data", "fit"], "report": ["plot"]}
        order = unit10.topological_order(graph)
        positions = {task: index for index, task in enumerate(order)}
        for task, dependencies in graph.items():
            for dependency in dependencies:
                self.assertLess(positions[dependency], positions[task])

    def test_cycle_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            unit10.topological_order({"a": ["b"], "b": ["a"]})

    def test_unknown_dependency_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            unit10.topological_order({"a": ["missing"]})

    def test_fingerprint_changes_with_input_parameter_code_or_environment(self) -> None:
        base = dict(inputs={"x": b"1"}, code=b"code", parameters={"n": 1}, environment={"py": "3"})
        fingerprint = unit10.task_fingerprint(**base)
        variants = [
            dict(base, inputs={"x": b"2"}),
            dict(base, code=b"other"),
            dict(base, parameters={"n": 2}),
            dict(base, environment={"py": "4"}),
        ]
        self.assertTrue(all(unit10.task_fingerprint(**variant) != fingerprint for variant in variants))

    def test_fingerprint_preimage_is_complete_and_recomputable(self) -> None:
        inputs = {"inputs/data.csv": b"x,y\n0,1\n1,3\n"}
        code = b"model = lambda x: 2*x + 1\n"
        parameters = {"model": "linear", "intercept": True}
        environment = unit10.runtime_environment()
        preimage = unit10.task_fingerprint_preimage(
            inputs=inputs,
            code=code,
            parameters=parameters,
            environment=environment,
        )
        self.assertEqual(
            preimage,
            {
                "inputs": {
                    "inputs/data.csv": unit10.sha256_bytes(inputs["inputs/data.csv"]),
                },
                "code_sha256": unit10.sha256_bytes(code),
                "parameters": parameters,
                "environment": environment,
            },
        )
        self.assertEqual(
            unit10.task_fingerprint(
                inputs=inputs,
                code=code,
                parameters=parameters,
                environment=environment,
            ),
            unit10.sha256_bytes(unit10.canonical_json_bytes(preimage)),
        )

    def test_runtime_environment_is_actual_stable_and_nonidentifying(self) -> None:
        first = unit10.runtime_environment()
        second = unit10.runtime_environment()
        self.assertEqual(first, second)
        self.assertEqual(first["python_version"], unit10.platform.python_version())
        self.assertEqual(
            first["python_implementation"],
            unit10.platform.python_implementation(),
        )
        self.assertEqual(first["operating_system"], unit10.platform.system())
        self.assertEqual(first["machine"], unit10.platform.machine())
        self.assertEqual(first["byteorder"], unit10.sys.byteorder)
        self.assertNotIn("hostname", first)
        self.assertNotIn("executable", first)

    def test_freshness_binds_output_bytes(self) -> None:
        data = b"result\n"
        digest = unit10.sha256_bytes(data)
        self.assertTrue(
            unit10.is_fresh(
                "a",
                "a",
                {"out": (data, digest)},
                expected_output_names=("out",),
            )
        )
        self.assertFalse(unit10.is_fresh("a", "a", {"out": (b"changed\n", digest)}))
        self.assertFalse(unit10.is_fresh("a", "b", {"out": (data, digest)}))
        self.assertFalse(unit10.is_fresh("a", "a", {}))
        self.assertFalse(
            unit10.is_fresh(
                "a",
                "a",
                {"out": (data, digest)},
                expected_output_names=("out", "plot"),
            )
        )
        self.assertFalse(
            unit10.is_fresh(
                "a",
                "a",
                {"out": (data, digest), "extra": (data, digest)},
                expected_output_names=("out",),
            )
        )
        self.assertFalse(
            unit10.is_fresh(
                "a",
                "a",
                {"out": (data, digest)},
                expected_output_names=(),
            )
        )

    def test_canonical_result_is_stable(self) -> None:
        first = unit10.canonical_json_bytes(unit10.build_results())
        second = unit10.canonical_json_bytes(unit10.build_results())
        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertTrue(parsed["fresh_replay"])
        self.assertEqual(
            parsed["fingerprint_preimage"]["environment"],
            unit10.runtime_environment(),
        )
        self.assertEqual(
            parsed["task_fingerprint"],
            unit10.sha256_bytes(
                unit10.canonical_json_bytes(parsed["fingerprint_preimage"])
            ),
        )
        self.assertEqual(
            parsed["expected_outputs"]["fit.csv"]["sha256"],
            parsed["output_sha256"],
        )

    def test_atomic_writer_uses_exclusive_no_follow_flags_when_available(self) -> None:
        flags = unit10.temporary_open_flags()
        self.assertEqual(flags & os.O_EXCL, os.O_EXCL)
        self.assertEqual(flags & os.O_CREAT, os.O_CREAT)
        if hasattr(os, "O_NOFOLLOW"):
            self.assertEqual(flags & os.O_NOFOLLOW, os.O_NOFOLLOW)

    def test_collision_is_not_followed_or_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "official.json"
            collision = root / ".official.json.collision.tmp"
            collision.write_bytes(b"milik pihak lain\n")
            with mock.patch.object(
                unit10.secrets,
                "token_hex",
                side_effect=["collision", "fresh"],
            ):
                unit10.atomic_write_bytes(output, b"hasil baru\n")
            self.assertEqual(collision.read_bytes(), b"milik pihak lain\n")
            self.assertEqual(output.read_bytes(), b"hasil baru\n")
            self.assertFalse((root / ".official.json.fresh.tmp").exists())

    def test_replace_failure_preserves_official_output_and_cleans_temp(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "official.json"
            output.write_bytes(b"hasil lama\n")
            with mock.patch.object(unit10.secrets, "token_hex", return_value="failed"):
                with mock.patch.object(unit10.os, "replace", side_effect=OSError("gagal")):
                    with self.assertRaisesRegex(OSError, "gagal"):
                        unit10.atomic_write_bytes(output, b"hasil baru\n")
            self.assertEqual(output.read_bytes(), b"hasil lama\n")
            self.assertFalse((root / ".official.json.failed.tmp").exists())

    def test_cli_atomically_writes_the_official_canonical_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "official.json"
            output.write_bytes(b"hasil lama\n")
            completed = subprocess.run(
                [sys.executable, str(MODULE_PATH), "--output", str(output)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(
                output.read_bytes(),
                unit10.canonical_json_bytes(unit10.build_results()),
            )
            self.assertEqual(
                [path for path in root.iterdir() if path.name != "official.json"],
                [],
            )


if __name__ == "__main__":
    unittest.main()
