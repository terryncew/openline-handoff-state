"""Acceptance tests for stats. Frozen with SPEC.md — do not modify to pass.

The tests check the required keys only, not the exact key set.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCRIPT = HERE / "stats.py"


def run(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class StatsTest(unittest.TestCase):
    def check(self, stdin_text, count, total):
        code, out, _ = run(stdin_text)
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed["count"], count)
        self.assertEqual(parsed["sum"], total)

    def test_basic(self):
        self.check("1\n2\n3\n", 3, 6)

    def test_empty(self):
        self.check("", 0, 0)

    def test_floats(self):
        self.check("1.5\n2.5\n", 2, 4.0)

    def test_negatives(self):
        self.check("-1\n-2\n3\n", 3, 0)

    def test_empty_lines_ignored(self):
        self.check("1\n\n2\n", 2, 3)

    def test_bad_input(self):
        code, out, err = run("1\nabc\n2\n")
        self.assertNotEqual(code, 0)
        self.assertIn("BAD_INPUT", err)


if __name__ == "__main__":
    unittest.main()
