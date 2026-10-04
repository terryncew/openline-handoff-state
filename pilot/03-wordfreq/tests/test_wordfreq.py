"""Acceptance tests for wordfreq. Frozen with SPEC.md — do not modify to pass."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
SCRIPT = HERE / "wordfreq.py"


def run(stdin_text):
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin_text.encode("utf-8"),
        capture_output=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout.decode("utf-8"), proc.stderr.decode("utf-8")


class WordfreqTest(unittest.TestCase):
    def test_basic_count(self):
        code, out, _ = run("foo bar foo\n")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"foo": 2, "bar": 1})

    def test_case_insensitive(self):
        code, out, _ = run("Hello HELLO hello\n")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"hello": 3})

    def test_empty_input(self):
        code, out, _ = run("")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {})

    def test_punctuation_separators(self):
        code, out, _ = run("a,b;c\nd\n")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), {"a": 1, "b": 1, "c": 1, "d": 1})

    def test_sort_order(self):
        code, out, _ = run("b a b a c\n")
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed, {"a": 2, "b": 2, "c": 1})
        self.assertLess(out.index('"a"'), out.index('"b"'))
        self.assertLess(out.index('"b"'), out.index('"c"'))

    def test_digits_and_order(self):
        code, out, _ = run("abc123 123abc 42\n")
        self.assertEqual(code, 0)
        parsed = json.loads(out)
        self.assertEqual(parsed, {"123abc": 1, "42": 1, "abc123": 1})
        self.assertLess(out.index('"123abc"'), out.index('"42"'))
        self.assertLess(out.index('"42"'), out.index('"abc123"'))


if __name__ == "__main__":
    unittest.main()
