# HANDOFF-STATE-001

Agent-to-agent state transfer. The next agent receives the last accepted
state plus a small delta. Never a rewritten summary.

**Frozen schema:** `HANDOFF_STATE_SCHEMA_v0.1.md`
(sha256 `246d2332a9fd2ee88ca52867b70e525205a3627f9bb5aa2f369913ab64968d95` —
see `HANDOFF_STATE_SCHEMA_v0.1.sha256`). Frozen 2026-10-03 by the user's
build order. No field may be added, removed, reworded, or reinterpreted
without a version bump.

**Research record:** `~/workspace/handoff-state-archaeology-001/`
(10 deliverables: field mapping, admission-authority table, term
lifecycle, five reconstructed handoffs, lost-in-prose list,
provider-replacement minimum, rejected fields, open questions).

## Layout

- `HANDOFF_STATE_SCHEMA_v0.1.md` — the frozen schema (do not edit)
- `schema-example-illustrative.json` — readable illustration of the
  schema shape (NOT validator input; labeled as such)
- `test-fixture-valid.json` — the valid fixture: real hashes, generated
  prose, consistent delta (validator input; see DECISIONS.md)
- `OPEN-QUESTIONS-FOR-CODEX.md` — unresolved design questions
- `DECISIONS.md` — seed decisions (illustration vs fixture; exact
  identity matching for v0.1)
- `STAGE-1-TICKET.md` — the Codex work order for Stage 1
- `handoff/` — Stage 1 implementation (JSONL append / validate / render)

## Stages

1. JSON schema + renderer + validator. JSONL append-only, no service.
2. Ten real handoffs, including one small live Muse→Codex provider
   replacement. Both agents consume and emit the format.
3. Receipts on transitions.
4. Validator-driven retry / quarantine.
5. Harder provider replacement. The real test.

Stage 1 only is authorized. Nothing else starts until it closes.
