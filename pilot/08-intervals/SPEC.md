# Interval union — frozen REAL-HANDOFF-08 task

Implement `merge_intervals(intervals)` in `intervals.py` using Python 3.11+
standard library only. Input is a list of lists, each exactly two integer
endpoints `[start, end]`, with `start <= end`. Booleans are not integers for
this interface. Invalid input raises `ValueError("BAD_INPUT")`.

Intervals are half-open. Discard empty intervals. Return a new list of
sorted, disjoint maximal intervals covering the same points. Merge touching
intervals as well as overlapping ones. Preserve the caller's input.

Examples:
- `[[5, 8], [1, 3], [3, 6]] -> [[1, 8]]`
- `[[2, 2], [-4, -1], [10, 12]] -> [[-4, -1], [10, 12]]`

The eight tests in `tests/test_intervals.py` are frozen behavior checks.
They do not select an implementation plan or confer admission authority.
Implementation actions come from the admitted Handoff State v0.1 chain.
No CLI, dependencies, additional feature, signatures, retries, or Stage 3.
