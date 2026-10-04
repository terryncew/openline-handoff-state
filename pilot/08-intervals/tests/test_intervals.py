"""Frozen behavior checks. No source, admission, plan, or timestamp assertions."""
import copy
import importlib.util
import os
from pathlib import Path
import unittest

DEFAULT = Path(__file__).resolve().parents[1] / "intervals.py"
TARGET = Path(os.environ.get("INTERVALS_MODULE", str(DEFAULT)))
SPEC = importlib.util.spec_from_file_location("intervals_under_test", TARGET)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
merge_intervals = MODULE.merge_intervals


class IntervalTests(unittest.TestCase):
    def test_empty_and_zero_length(self):
        self.assertEqual(merge_intervals([]), [])
        self.assertEqual(merge_intervals([[2, 2], [-1, -1]]), [])

    def test_unordered_disjoint(self):
        self.assertEqual(merge_intervals([[9, 12], [1, 3], [5, 7]]),
                         [[1, 3], [5, 7], [9, 12]])

    def test_overlapping_chain(self):
        self.assertEqual(merge_intervals([[4, 9], [1, 5], [8, 12]]), [[1, 12]])

    def test_touching_chain(self):
        self.assertEqual(merge_intervals([[3, 6], [1, 3], [6, 10]]), [[1, 10]])

    def test_nesting_and_duplicates(self):
        self.assertEqual(merge_intervals([[1, 10], [2, 3], [1, 10], [4, 7]]),
                         [[1, 10]])

    def test_negative_and_large_endpoints(self):
        big = 10 ** 80
        self.assertEqual(merge_intervals([[big, big + 5], [-9, -2]]),
                         [[-9, -2], [big, big + 5]])

    def test_invalid_input(self):
        for value in (None, {}, (), [1], [[1]], [[1, 2, 3]], [(1, 2)],
                      [["1", 2]], [[1.0, 2]], [[True, 2]], [[1, False]],
                      [[3, 1]]):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "^BAD_INPUT$"):
                    merge_intervals(value)

    def test_input_not_mutated(self):
        data = [[9, 12], [1, 3], [5, 7], [4, 4]]
        before = copy.deepcopy(data)
        merge_intervals(data)
        self.assertEqual(data, before)


if __name__ == "__main__":
    unittest.main()
