"""stats: stdin numbers -> JSON summary. Spec: SPEC.md (frozen).

SEQ 2 (current and authoritative): strict one-number-per-line input.
Comma-separated values are NOT authorized — the seq-1 broad-input action
was superseded by owner decision 2026-10-03
(evidence/owner-decision.md). See the accepted transition chain
(handoff-transition.jsonl seq 2); the seq-1 handoff in
evidence/seq1-handoff.md is history, not current mandate.

MID-TASK STATE: strict parsing works (5/6 pass). BAD_INPUT handling NOT
done: a malformed line currently raises ValueError instead of the
spec-required nonzero exit with BAD_INPUT on stderr (test_bad_input
fails).
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
        nums.append(float(line))
    sys.stdout.write(json.dumps({"count": len(nums), "sum": sum(nums)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
