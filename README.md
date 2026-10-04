# HANDOFF-STATE-001 — frozen (Stage 2 complete, 10/10)

Agent-to-agent state transfer. The next agent receives the last accepted
state plus a small delta. Never a rewritten summary.

**Status:** Stage 2 complete and frozen 2026-10-04. Ten real handoffs, all
owner-admitted. No further work is authorized on this record without an
explicit owner order. No Stage 3. No signatures. No autonomous retry.

**Frozen schema:** `HANDOFF_STATE_SCHEMA_v0.1.md`
(sha256 `246d2332a9fd2ee88ca52867b70e525205a3627f9bb5aa2f369913ab64968d95` —
see `HANDOFF_STATE_SCHEMA_v0.1.sha256`). No field may be added, removed,
reworded, or reinterpreted without a version bump. Unchanged through
Stage 2.

**Evaluator:** v0.1.2 (`handoff/core.py`, `EVALUATOR_VERSION`). Two narrow
evaluator-only repairs, schemas untouched:
- v0.1.1 — CLAIM-EVOLUTION-001: explicit owner-admitted claim replacement.
- v0.1.2 — QUESTION-LIFECYCLE-001: explicit owner-admitted open-question
  resolution.

**Evidence index:** `EVIDENCE.md` — the 10/10 scoreboard, accepted head
hashes, and the reusable tooling produced.

**Research record:** `~/workspace/handoff-state-archaeology-001/`
(10 deliverables from the pre-Stage-2 archaeology).

## Layout

- `HANDOFF_STATE_SCHEMA_v0.1.md` — the frozen schema (do not edit)
- `EVIDENCE.md` — 10/10 evidence index (start here)
- `handoff/` — canonical Python implementation (evaluate / append /
  replay / render / verify); `handoff/closeout.py` — phase-aware closeout
  verifier; `python -m handoff verify-closeout` — operational CLI
- `pilot/` — the ten accepted handoff task dirs (`02`–`10`, plus `05R`),
  each with accepted state, transition log, frozen SPEC, and evidence
- `.github/workflows/` — CI: `test` (full suite + replay audit),
  `closeout-cli-smoke` (operational CLI on the real 08 fixture)
- `OPEN-QUESTIONS-FOR-CODEX.md`, `STAGE-1-TICKET.md`, `DECISIONS.md` —
  historical Stage-1 seed apparatus (resolved; do not treat as open)
- `schema-example-illustrative.json` — readable illustration of the
  schema shape (NOT validator input; labeled as such)
- `test-fixture-valid.json` — the valid fixture: real hashes, generated
  prose, consistent delta (validator input; see DECISIONS.md)

## Rule for readers

This repository is a frozen record and a library. The OpenLine World
visualization reads this authoritative state; it never decides it. Do not
rebuild the rules in another engine and do not create a second simulation.
