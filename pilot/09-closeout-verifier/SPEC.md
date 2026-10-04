# REAL-HANDOFF-09 — phase-aware closeout verifier (frozen spec, 2026-10-04)

## Problem
The frozen-start verifier (`pilot/08-intervals/verify_freeze.py`) correctly
answers "is this repository still byte-identical to the frozen starting
state?" A legitimate owner-admitted closeout necessarily changes the
accepted transition count, the current state, `HANDOFF.md`, and the
accepted-state hash — so the frozen-start guard correctly goes red after
a valid closeout. It must not be weakened.

## Task
Add reusable core tooling that answers a different question:

**"Is this candidate state a valid admitted continuation of the frozen
starting state?"**

Do not modify `pilot/08-intervals/verify_freeze.py`,
`pilot/08-intervals/FREEZE.json`, or any frozen 08 evidence.

## Deliverable
`handoff/closeout.py` — `verify_closeout(...)` using only the canonical
Python Handoff State v0.1 evaluation/replay logic (`handoff/core.py`,
`handoff/canonical.py`, `handoff/schema.py`, `handoff/render.py`,
`handoff/store.py`). No admission semantics in another language.

## Required behavior
Given a frozen accepted starting state/history and a candidate closeout,
mechanically verify:

1. Every preexisting accepted transition record is preserved
   byte-for-byte and in the same order.
2. The candidate accepted history extends the frozen history (strictly
   longer), not rewrites it.
3. The first new accepted transition: has the next sequence number; uses
   the frozen head hash as `prior_state_hash`; is admitted by the
   configured authority owner (exact match); validates as accepted under
   the canonical v0.1 tooling.
4. Replaying the full candidate accepted chain succeeds.
5. The replayed final state hash equals the candidate recorded
   head/resulting hash, and equals the hash of the candidate state
   document.
6. Frozen/protected artifacts not explicitly allowed to change remain
   byte-identical between frozen start and candidate.
7. Legitimate closeout changes are explicitly allowed and mechanically
   checked, never inferred:
   - `handoff-state.json`: must equal the replayed final state.
   - `handoff-transition.jsonl`: frozen prefix byte-identical, then only
     accepted appended records.
   - `HANDOFF.md`: must equal the canonical rendering of the final state.
   - bounded closeout evidence: new files must appear on an explicit
     allowlist.
   - the authorized implementation file(s): paths on an explicit
     allowlist may differ.
8. Reject: rewritten/deleted historical records; wrong prior hash;
   skipped sequence; missing/incorrect owner admission; an unadmitted
   proposed state treated as accepted; unexpected protected-file changes;
   final state/hash mismatch.

## Reference fixture
REAL-HANDOFF-08: frozen start `c45b3c6`, legitimate admitted closeout
`bd58f07`. The verifier must pass that pair and must fail tampered or
unauthorized variants of it.

## Non-goals
No signatures, no Stage 3, no autonomous retry, no schema redesign, no
changes to the 08 freeze guard or frozen 08 evidence.
