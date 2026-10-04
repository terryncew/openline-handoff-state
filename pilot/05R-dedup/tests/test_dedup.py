"""Acceptance tests for dedup (REAL-HANDOFF-05R). Frozen with SPEC.md — do not modify to pass."""
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCRIPT = HERE / "dedup.py"


def run(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class DedupTest(unittest.TestCase):
    def test_basic_dedup(self):
        code, out, _ = run("a\nb\na\nc\nb\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "a\nb\nc\n")

    def test_first_occurrence_order(self):
        code, out, _ = run("b\na\nb\na\nc\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "b\na\nc\n")

    def test_empty_input(self):
        code, out, _ = run("")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_empty_lines(self):
        code, out, _ = run("a\n\nb\n\na\n")
        self.assertEqual(code, 0)
        self.assertEqual(out, "a\n\nb\n")

    def test_no_trailing_newline(self):
        code, out, _ = run("a\nb\na")
        self.assertEqual(code, 0)
        self.assertEqual(out, "a\nb\n")

    def test_single_line_no_newline(self):
        code, out, _ = run("hello")
        self.assertEqual(code, 0)
        self.assertEqual(out, "hello\n")


if __name__ == "__main__":
    unittest.main()
