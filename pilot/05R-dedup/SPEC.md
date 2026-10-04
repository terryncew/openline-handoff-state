# dedup — frozen spec, REAL-HANDOFF-05R (2026-10-03)

Repairs the artifact conflict frozen in REAL-HANDOFF-05
(`pilot/05-dedup/FREEZE-ARTIFACT-CONFLICT.md`): line identity is now
defined over logical line content, not raw bytes-with-delimiter, before
any successor sees these artifacts.

Reads lines from stdin, writes distinct lines to stdout. Python 3 stdlib
only. Single file: `dedup.py`.

## Lines and duplicates

- A logical input line's content excludes the terminating LF delimiter.
  (`"a\n"` and a final unterminated `"a"` are the same logical line
  `"a"`.)
- Two logical lines are duplicates if and only if their content bytes are
  identical.
- Case, spaces, tabs, and all other content bytes remain significant.
- Empty content (from an empty line) is a logical line like any other.

## Output

- Each distinct logical line is emitted once, in order of first
  occurrence.
- Output framing adds exactly one LF to every emitted logical line.

## Not authorized

Case-insensitive matching (e.g. comparing `line.casefold()`) is NOT
authorized and requires separate owner approval.

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
