"""Acceptance tests for csv2json. Frozen with SPEC.md — do not modify to pass."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCRIPT = HERE / "csv2json.py"
FIX = HERE / "fixtures"


def run(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class Csv2JsonTest(unittest.TestCase):
    def test_happy_path(self):
        code, out, _ = run("name,age,city\nAda,36,London\n")
        self.assertEqual(code, 0)
        self.assertEqual(
            json.loads(out),
            {
                "rows": [{"age": 36, "city": "London", "name": "Ada"}],
                "errors": [],
            },
        )

    def test_empty_age_is_null(self):
        code, out, _ = run("name,age,city\nBob,,Paris\n")
        self.assertEqual(code, 0)
        self.assertEqual(
            json.loads(out)["rows"],
            [{"age": None, "city": "Paris", "name": "Bob"}],
        )

    def test_empty_input(self):
        code, out, _ = run("")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"rows": [], "errors": []})

    def test_keys_sorted(self):
        code, out, _ = run("name,age,city\nAda,36,London\n")
        self.assertEqual(code, 0)
        self.assertLess(out.index('"age"'), out.index('"city"'))
        self.assertLess(out.index('"city"'), out.index('"name"'))
        self.assertLess(out.index('"errors"'), out.index('"rows"'))

    def test_bad_header(self):
        code, _, err = run("name,city\nAda,London\n")
        self.assertNotEqual(code, 0)
        self.assertIn("bad header", err)

    def test_malformed_age_goes_to_errors(self):
        code, out, _ = run("name,age,city\nCara,xx,Rome\n")
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["rows"], [])
        self.assertEqual(
            parsed["errors"],
            [{"row": 1, "raw": "Cara,xx,Rome", "reason": "bad age"}],
        )

    def test_wrong_column_count_goes_to_errors(self):
        code, out, _ = run("name,age,city\nDave,41\nEve,29,Berlin,extra\n")
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["rows"], [])
        self.assertEqual(
            parsed["errors"],
            [
                {"row": 1, "raw": "Dave,41", "reason": "wrong column count"},
                {
                    "row": 2,
                    "raw": "Eve,29,Berlin,extra",
                    "reason": "wrong column count",
                },
            ],
        )

    def test_fixture_end_to_end(self):
        stdin_text = (FIX / "input.csv").read_text(encoding="utf-8")
        expected = json.loads((FIX / "expected.json").read_text(encoding="utf-8"))
        code, out, _ = run(stdin_text)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), expected)


if __name__ == "__main__":
    unittest.main()
