# dedup — frozen spec (2026-10-03)

Reads lines from stdin, writes distinct lines to stdout. Python 3 stdlib
only. Single file: `dedup.py`.

## Duplicates

Two lines are duplicates if and only if they are byte-identical,
including case and whitespace. Empty lines are lines.

## Output

Each distinct line is emitted once, in order of first occurrence.
Every emitted line ends with exactly one newline character.

## Example

Input:
```
a
b
a
```
Output:
```
a
b
```
