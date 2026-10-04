"""dedup: stdin lines -> distinct lines in first-occurrence order. Spec: SPEC.md (frozen, 05R repaired).

PATH A (permitted): byte-exact comparison over logical line content
(excluding the LF delimiter). Path B (case-insensitive) is NOT
authorized — see evidence/considered-paths.md.

Logical lines are read as bytes so duplicate identity preserves every
content byte. A terminating LF is removed before comparison, then one
LF is restored for every emitted first occurrence.
"""
import sys


def main():
    seen = set()
    out = []
    lines = sys.stdin.buffer.read().split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    for line in lines:
        if line not in seen:
            seen.add(line)
            out.append(line + b"\n")
    sys.stdout.buffer.write(b"".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
