# wordfreq — frozen spec (2026-10-03)

Reads UTF-8 text from stdin, writes JSON to stdout. Python 3 stdlib
only. Single file: `wordfreq.py`.

## Tokenization

- Lowercase the entire input first.
- A word is a maximal run of `[a-z0-9]`. Every other character is a
  separator (punctuation, whitespace, symbols — all split words).
- Empty input, or input containing no words, → `{}`.

## Output

A single JSON object mapping word → count.

- Key order: count descending, then word ascending.
- Counts are exact integers.

## Example

Input: `Hello, hello world!`
Output: `{"hello": 2, "world": 1}`
