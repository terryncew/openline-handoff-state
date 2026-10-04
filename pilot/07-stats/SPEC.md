# stats — frozen spec (2026-10-03)

Reads numbers from stdin (one per line), writes a JSON summary to
stdout. Python 3 stdlib only. Single file: `stats.py`.

## Input

One decimal number per line. Empty lines are ignored. Empty input gives
count 0.

## Output

A JSON object with keys:

- `count`: number of values
- `sum`: arithmetic sum (`0` for empty input)

## Errors

A non-empty line that is not a decimal number → nonzero exit with
`BAD_INPUT` on stderr.

## Example

Input:
```
1
2
3
```
Output:
```
{"count": 3, "sum": 6}
```
