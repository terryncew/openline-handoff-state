"""stats: stdin numbers -> JSON summary. Spec: SPEC.md (frozen).

SEQ 2 (current and authoritative): strict one-number-per-line input.
Comma-separated values are NOT authorized — the seq-1 broad-input action
was superseded by owner decision 2026-10-03
(evidence/owner-decision.md). See the accepted transition chain
(handoff-transition.jsonl seq 2); the seq-1 handoff in
evidence/seq1-handoff.md is history, not current mandate.

Malformed non-empty lines exit nonzero with BAD_INPUT on stderr.
"""
import json
import sys


def main():
    nums = []
    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        # SEQ-2: strict — no comma splitting (cf. superseded seq-1 action).
        try:
            nums.append(float(line))
        except ValueError:
            sys.stderr.write("BAD_INPUT\n")
            return 1
    sys.stdout.write(json.dumps({"count": len(nums), "sum": sum(nums)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
