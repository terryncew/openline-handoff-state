# pctdecode — frozen spec (2026-10-03)

Reads lines from stdin, writes percent-decoded lines to stdout. Python 3
stdlib only. Single file: `pctdecode.py`.

## Decoding

- `%XX` (X = hex digit, either case) → the character with code point
  `0xXX`.
- A `%` not followed by two hex digits is emitted literally, and scanning
  continues after the `%`.
- Any other character is emitted unchanged.

## Scope

This spec establishes `%`-sequence decoding only. It does not establish
form-encoding semantics: whether `+` should decode to space is
unresolved, requires owner decision, and must not be assumed.

## Example

Input: `a%20b%41c`
Output: `a bAc`
