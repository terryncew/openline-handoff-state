"""Phase-aware closeout verifier for Handoff State v0.1.

The frozen-start guard answers "is this repository still byte-identical
to the frozen starting state?" This module answers a different question:

    "Is this candidate state a valid admitted continuation of the frozen
    starting state?"

It uses only the canonical Python v0.1 evaluation/replay logic
(handoff.core / handoff.canonical / handoff.schema). Admission semantics
are not duplicated in another language.

Checks (SPEC.md, pilot/09-closeout-verifier):
 1. every preexisting accepted record preserved byte-for-byte, same order
 2. candidate history strictly extends the frozen history
 3. first new record: next seq, frozen head hash as prior_state_hash,
    admitted by the configured authority owner (exact), accepted under
    canonical v0.1 tooling
 4. full candidate chain replays clean
 5. replayed final hash == recorded head/resulting hash == candidate
    state document hash
 6. protected artifacts not explicitly allowed to change: byte-identical
 7. explicit allowlist for legitimate closeout changes (state files
    structurally; new evidence and implementation files by explicit path)
 8. reject: rewritten/deleted history, wrong prior hash, skipped seq,
    missing/incorrect admission, unadmitted proposal treated as accepted,
    unexpected protected-file changes, final state/hash mismatch

PARTIAL IMPLEMENTATION (2026-10-04): checks 1-5 and the rejection paths
of 8 are implemented. Checks 6-7 (protected-file byte-identity and the
explicit allowlist) are scaffolded in the signature but NOT yet enforced:
frozen_files, candidate_files and allowlist are accepted and recorded,
not evaluated. See the frozen acceptance tests for the remaining work.
"""
from dataclasses import dataclass, field

from handoff.canonical import canonical_json, loads, state_hash
from handoff.core import apply_delta, verify_record
from handoff.render import render


@dataclass
class Allowlist:
    """Explicit, mechanically checked closeout changes. Nothing is inferred."""
    implementation_changed: list = field(default_factory=list)
    evidence_added: list = field(default_factory=list)


@dataclass
class CloseoutFailure:
    check: str
    detail: str


@dataclass
class CloseoutVerification:
    passed: bool
    failures: list = field(default_factory=list)
    checks_run: list = field(default_factory=list)
    # accepted for forward-compatibility; not yet enforced (see module docstring)
    file_checks: str = "not_implemented"


def _fail(failures, check, detail):
    failures.append(CloseoutFailure(check=check, detail=detail))


def verify_closeout(*, frozen_log_text, candidate_log_text,
                    frozen_head_state, candidate_state,
                    frozen_files=None, candidate_files=None,
                    allowlist=None, authority_owner,
                    task_dir="pilot/08-intervals"):
    """Verify a candidate closeout continues a frozen accepted state.

    frozen_log_text / candidate_log_text: raw handoff-transition.jsonl text.
    frozen_head_state: parsed accepted state at the frozen head.
    candidate_state: parsed candidate handoff-state.json.
    frozen_files / candidate_files: repo-relative path -> bytes (checks 6-7;
        accepted but not yet enforced).
    allowlist: explicit Allowlist (checks 6-7; accepted but not yet enforced).
    authority_owner: exact expected admission owner.
    """
    failures = []
    checks_run = []

    frozen_lines = [l for l in frozen_log_text.splitlines() if l.strip()]
    candidate_lines = [l for l in candidate_log_text.splitlines() if l.strip()]

    # Check 1: frozen history preserved byte-for-byte, same order.
    checks_run.append("history-preserved")
    if len(candidate_lines) < len(frozen_lines):
        _fail(failures, "history-preserved",
              f"candidate log shorter than frozen log "
              f"({len(candidate_lines)} < {len(frozen_lines)}): deleted history")
    else:
        for i, frozen_line in enumerate(frozen_lines):
            if candidate_lines[i] != frozen_line:
                _fail(failures, "history-preserved",
                      f"frozen record {i} differs in candidate history: rewritten history")
                break

    # Check 2: strict extension.
    checks_run.append("history-extends")
    if len(candidate_lines) <= len(frozen_lines):
        _fail(failures, "history-extends",
              "candidate history does not extend the frozen history")

    frozen_records = [loads(l) for l in frozen_lines]
    candidate_records = [loads(l) for l in candidate_lines]
    n = len(frozen_records)
    frozen_head_hash = state_hash(frozen_head_state)

    # Check 3: first new record.
    checks_run.append("first-new-record")
    if len(candidate_records) > n:
        rec = candidate_records[n]
        expected_seq = frozen_records[-1]["seq"] + 1 if frozen_records else 1
        if rec.get("seq") != expected_seq:
            _fail(failures, "first-new-record",
                  f"expected seq {expected_seq}, found {rec.get('seq')}: skipped sequence")
        if rec.get("prior_state_hash") != frozen_head_hash:
            _fail(failures, "first-new-record",
                  "prior_state_hash is not the frozen head hash: wrong prior hash")
        admission = rec.get("admission") or {}
        if admission.get("by") != authority_owner:
            _fail(failures, "first-new-record",
                  f"admission owner {admission.get('by')!r} != {authority_owner!r}: "
                  "missing/incorrect owner admission")
        record_errors = verify_record(frozen_head_state, rec)
        if record_errors:
            _fail(failures, "first-new-record",
                  "canonical v0.1 re-evaluation failed: " + "; ".join(record_errors))
        elif rec.get("validation", {}).get("result") != "accept":
            _fail(failures, "first-new-record",
                  "record does not validate as accepted: unadmitted proposal treated as accepted")

    # Check 4: full candidate chain replays clean.
    checks_run.append("chain-replay")
    state = None
    replay_ok = True
    for rec in candidate_records:
        errors = verify_record(state, rec)
        if errors:
            _fail(failures, "chain-replay",
                  f"seq {rec.get('seq')}: " + "; ".join(errors))
            replay_ok = False
            break
        try:
            state = apply_delta(state, rec["proposed_delta"])
        except (ValueError, TypeError, KeyError) as exc:
            _fail(failures, "chain-replay", f"seq {rec.get('seq')}: cannot apply delta: {exc}")
            replay_ok = False
            break

    # Check 5: final hash agreement.
    checks_run.append("final-hash")
    if replay_ok and state is not None:
        final_hash = state_hash(state)
        recorded = candidate_records[-1].get("resulting_state_hash")
        document = state_hash(candidate_state)
        if final_hash != recorded:
            _fail(failures, "final-hash",
                  "replayed final hash != recorded resulting hash: final state/hash mismatch")
        if final_hash != document:
            _fail(failures, "final-hash",
                  "replayed final hash != candidate state document hash: final state/hash mismatch")

    # Checks 6-7: protected files and explicit allowlist — NOT YET ENFORCED.
    checks_run.append("protected-files")
    checks_run.append("allowlist")

    return CloseoutVerification(
        passed=not failures,
        failures=failures,
        checks_run=checks_run,
        file_checks="not_implemented",
    )
