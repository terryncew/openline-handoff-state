# UNRESOLVED DESIGN QUESTIONS FOR CODEX (before implementation)

The archaeology is read-only. These are the questions the schema v0.1
does not answer, ordered by what blocks Stage 1.

## Blocking Stage 1 (JSONL append/validate/render)

1. **Where does the JSONL file live?** The assignment says "the existing
   coordination repo" — which one? Options observed: the goal workspace
   (`goals/<slug>/`), `openline-wallet` (receipts live there), or a new
   home. This is the user's decision; the schema does not care, but the
   implementation must.
2. **Genesis transition.** `prior_state_hash` of the first record is
   `"0"*64` (matches the audit-log GENESIS convention already in the
   codebase). Confirm this is acceptable vs. a named genesis record.
3. **Renderer determinism.** `rendered_prose` is generated from
   canonical fields via templates. Who authors the templates, and are
   they versioned with the schema (yes, proposed — schema version bump
   on template change)?
4. **Validator placement and invocation.** Stage 1 builds the
   deterministic validator; who runs it, and when — the coordinator
   before appending, the worker before proposing, or both? The
   AGENT HANDOFF prompt's check list is the validator's spec.
5. **Schema versioning rule.** The conformance profile's rule is
   proposed to apply to the schema itself (no field added/removed/
   reworded/reinterpreted without a version bump). Confirm before
   freezing v0.1.
6. **Canonical-terms file location and admission workflow.** Terms are
   proposed in deltas and admitted by the owner (observed practice).
   Where does the accepted-terms file live, and how does an owner
   admission get recorded — as a transition like any other (proposed)?

## Needed before Stage 2 (ten real handoffs)

7. **Migration.** Do existing artifacts get backfilled into the schema,
   or does the schema start fresh from the next handoff? The
   RECONSTRUCTED-HANDOFFS.md five are the natural backfill candidates —
   but backfilling reconstructions risks presenting reconstructions as
   primary records (see LOST-IN-PROSE.md item 12). Proposed: backfill
   only where the primary evidence still exists.
8. **Delta references to not-yet-existing evidence.** A proposed
   transition (e.g. "Codex builds the hook") cannot carry evidence that
   does not exist yet. Proposed: deltas carry `expected_evidence`
   (paths/digests to be filled at admission); the validator checks the
   admission record completes them. Confirm.
9. **`quarantine` routing.** The receipt gate's QUARANTINE disposition
   is the observed model. Stage 1 validator outputs it; Stage 4 gives
   the LLM-quarantine path. Confirm the schema should carry the
   disposition now so Stage 4 needs no schema change.

## Deferred to Stage 3 (receipts on transitions)

10. **Signatures.** The wallet/receipt machinery signs artifacts, but
    workflow state in the corpus was secured by hash-chaining only.
    Stage 3 question: reuse the existing receipt-signing path for
    transition admission, or keep hash-chain + sidecar? Do not decide
    in Stage 1; do not let the absence of signatures block the JSONL.
