# STAGE-1 TICKET — JSONL append / validate / render

**Controlling document:** `HANDOFF_STATE_SCHEMA_v0.1.md`
(sha256 `246d2332a9fd2ee88ca52867b70e525205a3627f9bb5aa2f369913ab64968d95`).
Do not alter the schema. If it appears to conflict with the task, stop
and report — do not reinterpret it.

## Scope

Build ONLY the Stage 1 tooling, in `handoff/`:

1. **Canonical JSON + hashing.** `sort_keys=True`,
   `separators=(",", ":")`, `ensure_ascii=False`, UTF-8. `sha256` over
   the canonical bytes, excluding the hash field itself. Genesis
   `prior_state_hash` is `"0"*64`.
2. **Append.** Append one transition record to the JSONL log. Compute
   `resulting_state_hash` from the new accepted state. Never rewrite
   history.
3. **Deterministic validator.** Implement the check list from
   `workspace/briefs/agent-handoff-controlled-clarity.md`: OPEN→FACT
   without evidence, FROZEN invariant modified, SHA/path/status changed,
   renamed canonical concept, claim exceeds cited experiment, omitted
   negative result, action outside mandate, state change without
   evidence. Output per-check pass/fail. Semantic conflicts route to
   `quarantine`, never silent resolution.
4. **Renderer.** Generate the fixed-section prose from canonical fields
   only (CURRENT STATE / AUTHORITY / OWNER / FROZEN INVARIANTS /
   VERIFIED EVIDENCE / OPEN QUESTIONS / FAILED / SUPERSEDED PATHS /
   NEXT PERMITTED ACTION / STOP CONDITIONS). It MUST NOT introduce
   information absent from the canonical fields.

Python standard library only. No service, no UI, no network.

## Tests

- `schema-example.json`: the example transition validates ACCEPT; the
  rendered prose contains only canonical information.
- One crafted failing delta per validator check above: each must be
  caught, with the right check named.
- Append two transitions to a scratch JSONL: hashes chain
  (`prior_state_hash` of the second equals `resulting_state_hash` of
  the first).

## Do NOT

- Add, remove, reword, or reinterpret any schema field.
- Design signatures or crypto. Hash-chaining only (Stage 3 question,
  explicitly deferred).
- Simulate handoffs or a provider replacement. Stage 1 is tooling;
  the ten-handoff pilot is a separate stage with real agents.
- Start Stage 2.

## Stop conditions

Stop after the tooling plus tests pass. Do not build the pilot. Do not
generalize. Report the test results plainly.
