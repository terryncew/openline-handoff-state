# Owner decision — REAL-HANDOFF-07 staged history

**Staged:** 2026-10-03, per the REAL-HANDOFF-07 START work order, which
explicitly orders a real two-state history with an owner narrowing
decision.

**Decision:** Input to `stats.py` is strictly one decimal number per
line. Comma-separated values per line are NOT authorized. A non-empty
line that is not a single decimal number → nonzero exit with `BAD_INPUT`
on stderr (per the frozen SPEC.md Errors section).

**Reason (staged):** downstream consumer contract requires the strict
reading; the lenient comma-splitting authorized under seq 1 is revoked.

**Effect:** seq-1 action A (comma-separated acceptance) is superseded. It
remains valid history; it is not current.
