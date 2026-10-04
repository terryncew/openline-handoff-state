"""Acceptance tests for toposort. Frozen with SPEC.md — do not modify to pass.

TOPOSORT_SCRIPT env var may point at an alternate implementation for
evidence runs; the deliverable under test is toposort.py.
"""
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCRIPT = Path(os.environ.get("TOPOSORT_SCRIPT", HERE / "toposort.py"))


def run(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=120,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


def lines(pairs):
    return "".join(json.dumps({"node": n, "deps": d}) + "\n" for n, d in pairs)


def large_chain(n=100000):
    ids = [f"n{i:06d}" for i in range(n)]
    return "".join(
        json.dumps({"node": ids[i], "deps": [ids[i - 1]] if i else []}) + "\n"
        for i in range(n)
    ), ids


class ToposortTest(unittest.TestCase):
    def test_empty_input(self):
        code, out, _ = run("")
        self.assertEqual(code, 0)
        self.assertEqual(out, "")

    def test_linear_chain(self):
        code, out, _ = run(lines([("c", ["b"]), ("b", ["a"]), ("a", [])]))
        self.assertEqual(code, 0)
        self.assertEqual(out, "a\nb\nc\n")

    def test_diamond_tiebreak(self):
        code, out, _ = run(lines([("c", []), ("a", []), ("b", ["a"])]))
        self.assertEqual(code, 0)
        self.assertEqual(out, "a\nb\nc\n")

    def test_cycle(self):
        code, out, err = run(lines([("a", ["b"]), ("b", ["a"])]))
        self.assertNotEqual(code, 0)
        self.assertIn("CYCLE", err)

    def test_large_chain(self):
        stdin_text, ids = large_chain()
        code, out, _ = run(stdin_text)
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines(), ids)


if __name__ == "__main__":
    unittest.main()
