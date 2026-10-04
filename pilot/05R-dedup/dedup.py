"""dedup: stdin lines -> distinct lines in first-occurrence order. Spec: SPEC.md (frozen, 05R repaired).

PATH A (permitted): byte-exact comparison over logical line content
(excluding the LF delimiter). Path B (case-insensitive) is NOT
authorized — see evidence/considered-paths.md.

MID-TASK STATE: byte-exact dedup works (4/6 pass). Logical-line parsing
and output framing NOT done: a final input line without a trailing
newline is emitted without one (test_no_trailing_newline and
test_single_line_no_newline fail).
"""
import sys


def main():
    seen = set()
    out = []
    for line in sys.stdin:
        if line not in seen:
            seen.add(line)
            out.append(line)
    sys.stdout.write("".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
