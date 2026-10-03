# csv2json — frozen spec (2026-10-03)

Reads CSV from stdin, writes JSON to stdout. Python 3 stdlib only.
Single file: `csv2json.py`.

## Input

- Fully empty input (no bytes, or only whitespace) → `{"rows": [], "errors": []}`.
- Otherwise the first line must be exactly `name,age,city`. Any other
  first line → exit nonzero, `bad header` on stderr, no JSON on stdout.
- Data rows: `name` (string), `age` (integer or empty), `city` (string).
- Blank lines are skipped.

## Output

A single JSON object: `{"rows": [...], "errors": [...]}`.

- Valid row → `{"name": ..., "age": <int|null>, "city": ...}`.
  An empty age field → `null`, not an error.
- Malformed row → appended to `errors`, never silently dropped and
  never placed in `rows`:
  `{"row": N, "raw": "<original line>", "reason": "<reason>"}`.
  `N` is the 1-based data-row number (the header is not counted).
  Reasons, exactly: `wrong column count`, `bad age`.
  (`bad age` = age field non-empty and not an integer.)
- All object keys sorted at every level.

## Example

Input:
```
name,age,city
Ada,36,London
Bob,,Paris
Cara,xx,Rome
```
Output:
```json
{"errors": [{"raw": "Cara,xx,Rome", "reason": "bad age", "row": 3}], "rows": [{"age": 36, "city": "London", "name": "Ada"}, {"age": null, "city": "Paris", "name": "Bob"}]}
```
