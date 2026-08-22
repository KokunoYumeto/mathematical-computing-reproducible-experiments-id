from pathlib import Path
import tempfile
import unittest


class DemoPackageTests(unittest.TestCase):
    def test_frozen_input_is_42(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual((root / "inputs" / "value.txt").read_text().strip(), "42")


if __name__ == "__main__":
    unittest.main()
