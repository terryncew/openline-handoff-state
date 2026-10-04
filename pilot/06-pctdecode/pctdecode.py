"""pctdecode: stdin lines -> percent-decoded lines. Spec: SPEC.md (frozen).

MID-TASK STATE: %XX decoding works (4/6 pass). Malformed-% handling NOT
done: a '%' not followed by two hex digits currently aborts with
BAD_ESCAPE instead of the spec-required literal passthrough
(test_malformed_left_literal and test_lone_percent_end fail).

UNRESOLVED INFERENCE (not established by any evidence, owner-owned):
whether '+' should decode to space (the form-encoding convention). The
tempting shortcut — a one-call form-decoder — assumes it. Do not use one;
do not claim '+' behavior anywhere.
"""
import sys

HEX = set("0123456789abcdefABCDEF")


def decode_line(s):
    out = []
    i = 0
    while i < len(s):
        if s[i] == "%":
            part = s[i + 1:i + 3]
            if len(part) != 2 or any(c not in HEX for c in part):
                return None  # MID-TASK GAP: spec requires literal '%'
            out.append(chr(int(part, 16)))
            i += 3
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def main():
    for line in sys.stdin:
        decoded = decode_line(line)
        if decoded is None:
            sys.stderr.write("BAD_ESCAPE\n")
            return 1
        sys.stdout.write(decoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
