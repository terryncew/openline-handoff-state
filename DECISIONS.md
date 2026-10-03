# SEED DECISIONS — 2026-10-03

Codex's Stage-1 pre-build review found four defects in the seed example
(placeholder hashes, hand-written prose, unbound principal strings,
delta/resulting-state inconsistency on the added question's owner).
Codex paused per the ticket's stop-and-report rule. Correct call.
Resolutions, decided by Muse under the user's HANDOFF-STATE-001 build
order:

## 1. Illustration vs valid fixture

Both. `schema-example-illustrative.json` is preserved as a readable
illustration of the schema shape, explicitly labeled NOT validator
input (placeholders, hand-written prose, inconsistent strings).
`test-fixture-valid.json` is the separately labeled valid fixture:
real computed hashes, prose generated from canonical fields only,
delta and resulting state byte-consistent, principal strings canonical.

## 2. Identity bindings vs exact matching

**v0.1: exact matching only.** No schema change. The same principal
must appear as the identical string in `authority_owner`,
`roles.admitter`, and `admission.by`. Descriptive context moves to
`frozen_invariants` (standing rules) or `admission.evidence` (the
authorizing record) — never into the identity string itself. The
validator enforces byte equality; a mismatch is a failed check, not a
judgment call.

**Explicit identity bindings** (`{id, label}` on authority fields) are
deferred as a v0.2 candidate. Rationale: the freeze rule — no field
added, removed, reworded, or reinterpreted without a version bump —
and Stage 1's mandate is tiny. If exact matching proves brittle in the
ten-handoff pilot, v0.2 carries the binding.

## What changed in the seed

- `test-fixture-valid.json` added: prior state + transition (seq 5) +
  resulting state for OPEN-MHS-RECEIVER-001, with
  `prior_state_hash sha256:a918b726…` and
  `resulting_state_hash sha256:fd95b800…` computed per the hash rule.
- The added open question's owner is identical in delta and resulting
  state ("Open-MHS maintainer"), keeping the full silence-clock text
  in the question string.
- `admission.by` = `roles.admitter` = `authority_owner` =
  "Terrynce White" (exact).
- README updated to point at both files.
