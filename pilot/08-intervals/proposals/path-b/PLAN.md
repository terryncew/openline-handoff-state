# Endpoint-event consolidation proposal

Proposer: Codex proposal author.
Base: admitted A_PARTIAL, sequence 2.
Exact proposal time: `candidate-state.json -> identifiers.dates.path_b_proposed_at`.
Admission request: pending owner decision; `proposal.json.admission` is empty.

The current validation-and-sort checkpoint leaves three merge cases open.
A grouped endpoint-event sweep can handle overlap, duplicate/nested ranges,
and touching endpoints in one coverage transition rule. At each endpoint,
aggregate starts and ends before changing the coverage count; a net-zero
change preserves the open component, which joins touching intervals.

The accompanying complete candidate preserves the interface, strict integer
validation, empty-range filtering, and caller-data preservation. It sorts at
most twice the number of input endpoints: O(n log n) time and O(n) space,
the same asymptotic bound as the accepted sort-and-accumulate route. Its
attraction is a complete implementation and a natural basis for later
coverage-depth reporting if separately requested. No coverage-depth feature
is included or authorized here.

Requested operational changes are concrete in `proposal.json`:
- Change A_PARTIAL to B_READY_FOR_EXECUTION.
- Record the proposed retirement of the interval-accumulator continuation.
- Replace next actions with adoption of this event-sweep implementation.
- Add the candidate's test result, source digest, and proposal timestamp.
- Keep existing owner, goal, invariant, stop, claim, identifier, and evidence
  fields; request owner admission rather than changing the authority owner.

Proposed work plan: copy the candidate into the active module, run the frozen
behavior checks, review grouped-event handling, then report completion to the
owner. This saves the remaining accumulator implementation work and provides
a coherent complete plan. The behavior run is recorded in `candidate-tests.txt`.

This document and the candidate state are a request. The v0.1 receipt records
the admission result. Repository publication does not answer that request.
