"""Acceptance tests for pctdecode. Frozen with SPEC.md — do not modify to pass."""
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCRIPT = HERE / "pctdecode.py"


def run(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class PctDecodeTest(unittest.TestCase):
    def test_basic(self):
        code, out, _ = run("a%20b%41c\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "a bAc\n")

    def test_lowercase_hex(self):
        code, out, _ = run("x%2fy\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "x/y\n")

    def test_malformed_left_literal(self):
        code, out, _ = run("100% sure %2G ok\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "100% sure %2G ok\n")

    def test_lone_percent_end(self):
        code, out, _ = run("abc%\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "abc%\n")

    def test_empty(self):
        code, out, _ = run("")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_no_escapes(self):
        code, out, _ = run("plain\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "plain\n")


if __name__ == "__main__":
    unittest.main()
