# HANDOFF STATE SCHEMA v0.1

**Status:** DRAFT 2026-10-03. Archaeology synthesis; not yet implemented.
**Controlling assignment:** HANDOFF-STATE-ARCHAEOLOGY-001 (read-only).
**Rule:** every field below is grounded in observed practice across the
inspected artifact families. Fields are included because they already exist
in the corpus, not because they sound useful. Rejected fields are listed
separately with reasons.

## The model

```
raw history = evidence
accepted state = operational truth
delta = proposed change
receipt = proof of admission
```

The next agent never receives a rewritten summary. It receives the last
accepted state plus a small delta. State transitions are append-only.

Two record types, both JSON:

1. **State object** (`openline.handoff-state.v0.1`) — the accepted
   operational truth for one task at one point in time.
2. **Transition record** (`openline.handoff-transition.v0.1`) — one
   proposed → validated → admitted change, appended to the JSONL log.

## 1. State object

| Field | Type | Grounded in |
|---|---|---|
| `schema` | string, `"openline.handoff-state.v0.1"` | conformance `schema` version strings; handoff.json `schema` fields |
| `task_id` | string, stable, unique | Goal ID / slug (probe GOALs); `handoff` strings (airlock); `experiment` (continuity bundle) |
| `goal` | string | `## Description`; prereg `## Claim under test`; airlock `question` |
| `authority_owner` | string (who can admit transitions) | "Frozen by: Muse… under the user's Phase 2 order" (FREEZE-v0.1); "Nothing consequential merges without his approval" (GOAL.md Standing) |
| `current_state` | string (single controlled status) | `## Phase state`; airlock `status` enums; `verified_stage` |
| `frozen_invariants` | string[] | `frozen_envelope`; FROZEN section labels; `## Translation forbidden`; "No check may be added, removed, reworded, or reinterpreted without a version bump" |
| `verified_facts` | {fact, evidence}[] | `observed` / `validation`; CLAIM.md D1–D7 table; findings-doc `[V]` citations |
| `claims` | {claim, basis, ceiling}[] | `claim_boundary`; prereg `## Claim ceiling`; CLAIM.md §1 + §7 |
| `open_questions` | {question, owner}[] | CLAIM.md G1–G8; airlock `question`/`parked`; selection-doc `UNRESOLVED` items |
| `failed_or_superseded_paths` | {path, classification, evidence}[] | `failed-runs/`; `superseded_by`; `preserve_failed_run`; INCONCLUSIVE archive; audit corrections |
| `canonical_terms` | {TERM: definition} | conformance normative vocabulary ("These terms are defined here and used with exactly these meanings") |
| `proposed_state_changes` | object[] (deltas, not prose) | the systematic gap — MISSING everywhere as structured data; the schema's reason to exist |
| `next_permitted_actions` | string[] | `next_after_merge`; ticket `## Deliverables`; prereg S1…S11 sequence |
| `stop_conditions` | string[] | `do_not_merge_before_result`; ticket `## Stop conditions`; `forbidden`; silence rule |
| `identifiers` | {shas, paths, versions, dates, receipts} | `.sha256` sidecars; `base_sha`/`preregistration_sha256`; GH run numbers; freeze dates |
| `roles` | {author, proposer, verifier, admitter, executor} | the five roles, separated — the least-recorded dimension in the corpus; the schema forces them explicit |

### Field rules

- `verified_facts[].evidence` is REQUIRED. A fact without an evidence
  reference is not a fact in this schema; it is demoted to `claims[]` or
  `open_questions[]`. (Grounded in the `[V]` legend discipline.)
- `claims[].ceiling` is REQUIRED. Every claim carries its non-claim
  boundary. (Grounded in prereg §9 non-claims and CLAIM.md §7.)
- `open_questions[].owner` is REQUIRED. An open question without an owner
  is how items silently die. (Grounded in the archaeology finding that
  open items with no owner decay.)
- `roles.admitter` is REQUIRED on every transition (see §2). The
  archaeology's single most consistent finding: the admitter is the
  least-recorded role everywhere, recoverable only from "his order" prose.
- `canonical_terms` values are definitions, not descriptions. New terms
  enter only through the term lifecycle (TERM-LIFECYCLE.md).

## 2. Transition record (append-only JSONL)

```json
{
  "schema": "openline.handoff-transition.v0.1",
  "task_id": "…",
  "seq": 13,
  "prior_state_hash": "sha256:…",
  "proposed_delta": { "current_state": { "from": "…", "to": "…" }, … },
  "validation": {
    "result": "accept | reject | quarantine",
    "checks": [ { "check": "…", "pass": true } ]
  },
  "admission": {
    "decision": "…",
    "by": "…",
    "at": "…",
    "evidence": "…"
  },
  "resulting_state_hash": "sha256:…",
  "rendered_prose": "…"
}
```

- `prior_state_hash` of the first transition is `"0"*64` (genesis;
  matches the audit-log GENESIS convention already in the codebase).
- `proposed_delta` is a field-level diff, not prose. A delta that cannot
  be expressed as field changes is not ready for admission.
- `validation.checks` is the deterministic validator's output (Stage 1:
  Codex builds this). Semantic conflicts route to `quarantine`, never
  silent resolution. (`quarantine` disposition is observed practice from
  the receipt gate.)
- `rendered_prose` is GENERATED from the canonical state, never
  hand-written, and MUST NOT introduce information absent from the
  canonical fields. It follows the AGENT HANDOFF rendering discipline
  (`workspace/briefs/agent-handoff-controlled-clarity.md`) and ends with
  the fixed sections: CURRENT STATE / AUTHORITY / OWNER / FROZEN
  INVARIANTS / VERIFIED EVIDENCE / OPEN QUESTIONS / FAILED / SUPERSEDED
  PATHS / NEXT PERMITTED ACTION / STOP CONDITIONS.
- `resulting_state_hash` = sha256 of the canonical JSON of the new
  accepted state (see Hash rule).

## Hash rule

`sha256` over canonical JSON: `sort_keys=True`,
`separators=(",", ":")`, `ensure_ascii=False`, UTF-8. The hashed object
excludes its own hash field. (Grounded in the Phase 3 canonical
serialization and the `.sha256` sidecar convention.)

## Schema versioning

The conformance profile's rule applies to the schema itself: no field may
be added, removed, reworded, or reinterpreted without a version bump.
v0.1 is frozen at Stage 1 implementation.

## What this schema does NOT do

- It does not replace evidence artifacts (preregs, bundles, logs). It
  points at them via `identifiers` and `verified_facts[].evidence`.
- It does not assign authority. It records who holds it
  (`authority_owner`, `roles.admitter`).
- It does not resolve semantic conflicts. It quarantines them.
- It does not store conversational history. Raw history is evidence,
  referenced, not embedded.
