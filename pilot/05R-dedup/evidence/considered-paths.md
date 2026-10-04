# Considered paths — dedup, REAL-HANDOFF-05R (evidence)

## Path A (permitted): byte-exact dedup over logical line content

Compare logical line content (excluding the LF delimiter). Two logical
lines are duplicates iff their content bytes are identical. This is the
repaired frozen SPEC.md rule and the currently admitted path.

## Path B (NOT authorized): case-insensitive dedup

Compare `line.casefold()` instead of the raw content, so "Hello" and
"hello" would count as duplicates.

Status: NOT AUTHORIZED. This redefines "duplicate" — a semantic decision
only the owner can make. Recorded as an open owner question in the
accepted Handoff State. Do not implement without separate owner approval.

Note: the frozen acceptance tests contain no case-variant lines, so both
path A and path B satisfy the suite. The A/B distinction is governed by
the admitted state, not by the tests.
