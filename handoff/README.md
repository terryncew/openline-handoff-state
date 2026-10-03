# Stage 1: local JSONL handoff tooling

Python standard library only, Python 3.11+, POSIX (fcntl file locking).
No service, network client, scheduler, retry loop, or external contact.
The frozen Markdown schema and seed files are unchanged.

Run the tests from the repository root:

    python -m unittest discover -s handoff/tests -v

The GitHub Actions workflow executes this same command; it is the execution
environment for this build, not part of the handoff runtime.

## Commands

    python -m handoff validate proposal.json
    python -m handoff append proposal.json --log handoff/task.jsonl
    python -m handoff replay --log handoff/task.jsonl
    python -m handoff render accepted-state.json
    python -m handoff parse-rendered receipt.txt
    python -m handoff verify stored-record-with-prior.json

A proposal file is an input envelope (not a new schema record) containing
exactly prior_state, proposed_delta, admission. The first prior_state is null.
No log path, identity, timestamp, or admission authority is inferred.
Commands emit canonical JSON. Exit codes: 0 accept/success, 2 reject,
3 quarantine. Failed check names are in transition.validation.checks.

A returned receipt contains both state and transition. Its rendered prose is
transition.rendered_prose. The JSONL stores only the frozen transition record,
not a new wrapper record type. Replay reconstructs canonical accepted state
from the genesis delta and verifies every subsequent record, hash and template.

## Delta grammar

Genesis establishes all 16 state fields using { "to": value } for each field.
It requires a complete, explicit admission matching the declared initial owner.
This records the owner's declaration; it does not assign or authenticate authority.

Later field operations are exactly one of:

- { "from": old_value, "to": new_value }: compare and replace.
- { "replace": value }: replace, subject to invariant checks.
- { "add": array_or_object }: append list entries or add new dictionary keys.

Paths may address existing dictionary members, such as identifiers.dates.
Parent/child operations cannot overlap. Object additions cannot overwrite a key.
No removal, inferred rename, text normalization, or automatic question resolution.

authority_owner, goal, frozen_invariants, stop_conditions and task_id cannot
change in this minimal implementation. Existing identifiers and term definitions
remain exact. Facts, open questions, and failed/superseded paths remain an
unchanged prefix; additions are explicit. Terminal statuses UNRESOLVED, FAILED,
NEGATIVE, FROZEN, SUPERSEDED and INCONCLUSIVE cannot be promoted. Other status
changes require explicit deltas and admission. OPEN to FACT additionally requires
new evidence-bearing facts.

A new term is admitted only by an explicit term-addition delta with complete
owner admission. Existing terms cannot be removed, renamed or redefined.
No separate terms file is needed: canonical_terms in accepted state is canonical.

## Admission and disposition

For every accepted transition, admission.by, resulting roles.admitter and
the prior authority_owner must match exactly. A delta cannot appoint its own
authority. The historical prior roles.admitter is preserved as historical state;
it is not silently substituted for the authority owner.

Missing admission rejects acceptance; its proposal is retained in the transition.
Rejected and quarantined attempts advance the attempt sequence, never accepted
state. Their resulting_state_hash stays the accepted head. A rejected genesis
returns a receipt with state null and is not appended to an accepted-state log.

For new tooling inputs, admission.decision must be exactly "admit" or "accept".
The existing fixture's exact "outreach authorized and executed" decision is
recognized for compatibility. Other prose fails the explicit-admission-decision
check, including conditional admissions. Put the authorizing rationale in
admission.evidence. This is a narrow invocation contract, not a schema-field
change or an attempt to interpret arbitrary decision prose.
The supplied text is retained verbatim.

The caller supplies the authorizing evidence reference and an aware timestamp.
The tooling records this declaration. It does not authenticate a user or verify
that an evidence artifact proves the asserted fact; signatures are deferred.

All claim/basis/ceiling changes quarantine. Literal opposing facts using
"NOT: <exact fact>" or "NOT <exact fact>" quarantine. A reported semantic
conflict may force quarantine through --semantic-conflict or the Python API;
it cannot override any failed structural or authority check.

These are mechanical checks, not general natural-language reasoning. Owner
admission plus preserved constraints is the mandate check. A newly added fact
or action may contain an unreported semantic conflict that literal checks cannot
detect. Claim scope, experiment adequacy and prose mandate interpretation need
verifier scrutiny; do not claim this tooling proves them. This is a recorded
limitation for the real pilot, not permission to reconcile contradictory state.

## Rendering and integrity

Version-locked controlled templates quote canonical JSON values. Prefix sections
carry schema, task, goal, claims/ceilings, terms, proposed deltas, identifiers.
The required ending sections preserve current state, authority, roles, frozen
invariants, evidence, questions, failed/superseded paths, actions and stops.
OWNER prints existing roles; no missing task-owner field is invented.
parse-rendered round-trips all fields and rejects template changes. No SHA,
path, status, uncertainty or negative outcome is shortened.

test-fixture-valid.json is used as a prior/delta/admission acceptance fixture.
The tool independently reproduces its resulting state and hashes and generates
the required fixed-section prose. Its supplied prose/checks are not trusted or
copied. Strict verify diagnoses supplied prose/template or check differences.
The illustrative seed is never admitted or migrated into primary history.

File locks serialize cooperating writers. A stale prior, corrupt chain, blank
line, non-JSON value, duplicate JSON key or incomplete tail fails closed.
There is no repair or retry. Hash chaining detects consistency errors; without
signatures it is not protection against someone rewriting the entire log.

## Stage boundary

Stage 1 ends with tooling and tests. No Muse/Codex handoff is simulated.
The ten real handoffs, evidence-channel access, and measurement of extra
successor context remain Stage 2 work. Tests here do not establish pilot success.
