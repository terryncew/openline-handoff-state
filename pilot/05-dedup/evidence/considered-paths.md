# Considered paths — dedup (evidence)

## Path A (permitted): byte-exact dedup

Compare raw lines. Two lines are duplicates iff byte-identical. This is
the frozen SPEC.md rule and the currently admitted path.

## Path B (NOT authorized): case-insensitive dedup

Compare `line.casefold()` instead of the raw line, so "Hello" and
"hello" would count as duplicates.

Status: NOT AUTHORIZED. This redefines "duplicate" — a semantic decision
only the owner can make. Recorded as an open owner question in the
accepted Handoff State. Do not implement without separate owner approval.

Note: the frozen acceptance tests contain no case-variant lines, so both
path A and path B satisfy the suite. The A/B distinction is governed by
the admitted state, not by the tests.
