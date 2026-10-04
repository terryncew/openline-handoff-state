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

File permissions come only from the supplied Allowlist. Structural state,
history, and rendering checks cannot be bypassed by listing those paths.
"""
from dataclasses import dataclass, field

from handoff.canonical import canonical_json, loads, state_hash
from handoff.core import verify_record
from handoff.render import render
from handoff.store import _replay_text


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
    file_checks: str = "not_run"


def _fail(failures, check, detail):
    failures.append(CloseoutFailure(check=check, detail=detail))


def _repo_path(path):
    return (isinstance(path, str) and bool(path)
            and "\\" not in path
            and all(part not in {"", ".", ".."} for part in path.split("/")))


def _verify_files(failures, *, frozen_files, candidate_files, allowlist,
                  task_dir, frozen_log_text, candidate_log_text,
                  frozen_head_state, final_state):
    """Check supplied snapshots; the diff never supplies permissions."""
    before = len(failures)
    if not isinstance(frozen_files, dict) or not isinstance(candidate_files, dict):
        _fail(failures, "protected-files", "both file snapshots are required")
        return False
    if not isinstance(allowlist, Allowlist):
        _fail(failures, "allowlist", "an explicit Allowlist is required")
        return False
    if not _repo_path(task_dir):
        _fail(failures, "allowlist", "task_dir must be a repository-relative path")
        return False
    for label, files in (("frozen", frozen_files), ("candidate", candidate_files)):
        if any(not _repo_path(path) or not isinstance(data, bytes)
               for path, data in files.items()):
            _fail(failures, "protected-files",
                  label + " snapshot must map repository-relative paths to bytes")
            return False

    state_path = task_dir + "/handoff-state.json"
    log_path = task_dir + "/handoff-transition.jsonl"
    prose_path = task_dir + "/HANDOFF.md"
    structural = {state_path, log_path, prose_path}
    implementation = allowlist.implementation_changed
    evidence = allowlist.evidence_added
    for paths in (implementation, evidence):
        if not isinstance(paths, list) or any(not _repo_path(path) for path in paths):
            _fail(failures, "allowlist", "allowlist entries must be explicit file paths")
            return False
    implementation, evidence = set(implementation), set(evidence)
    if (implementation & evidence) or ((implementation | evidence) & structural):
        _fail(failures, "allowlist", "allowlist categories must be disjoint from structural files")
    for path in sorted(implementation):
        if path not in frozen_files or path not in candidate_files:
            _fail(failures, "allowlist",
                  "implementation_changed requires an existing, retained file: " + path)
    for path in sorted(evidence):
        if path in frozen_files:
            _fail(failures, "allowlist", "evidence_added cannot rewrite an existing file: " + path)

    for path, data in frozen_files.items():
        if path not in candidate_files:
            _fail(failures, "protected-files", "frozen file deleted: " + path)
        elif path not in structural | implementation and candidate_files[path] != data:
            _fail(failures, "protected-files", "protected bytes changed: " + path)
    for path in sorted(candidate_files.keys() - frozen_files.keys()):
        if path not in evidence:
            _fail(failures, "allowlist", "unlisted new file: " + path)

    for label, files, log_text, expected_state in (
            ("frozen", frozen_files, frozen_log_text, frozen_head_state),
            ("candidate", candidate_files, candidate_log_text, final_state)):
        missing = structural - files.keys()
        if missing:
            _fail(failures, "allowlist",
                  label + " structural files missing: " + ", ".join(sorted(missing)))
            continue
        try:
            if files[log_path] != log_text.encode("utf-8"):
                _fail(failures, "allowlist", label + " log file differs from supplied history")
            document = loads(files[state_path].decode("utf-8"))
            if expected_state is None or canonical_json(document) != canonical_json(expected_state):
                _fail(failures, "allowlist", label + " state file differs from replayed state")
            if expected_state is not None and files[prose_path] != render(expected_state).encode("utf-8"):
                _fail(failures, "allowlist", label + " HANDOFF.md differs from canonical rendering")
        except (ValueError, UnicodeError) as exc:
            _fail(failures, "allowlist", label + " structural files invalid: " + str(exc))

    if log_path in frozen_files and log_path in candidate_files:
        if not candidate_files[log_path].startswith(frozen_files[log_path]):
            _fail(failures, "protected-files", "frozen log byte prefix changed")
    try:
        frozen_receipt = _replay_text(frozen_log_text)
        if (frozen_receipt is None
                or canonical_json(frozen_receipt["state"]) != canonical_json(frozen_head_state)):
            _fail(failures, "protected-files", "frozen head differs from canonical replay")
    except (ValueError, TypeError, KeyError) as exc:
        _fail(failures, "protected-files", "frozen history cannot replay: " + str(exc))
    return len(failures) == before


def verify_closeout(*, frozen_log_text, candidate_log_text,
                    frozen_head_state, candidate_state,
                    frozen_files=None, candidate_files=None,
                    allowlist=None, authority_owner,
                    task_dir="pilot/08-intervals"):
    """Verify a candidate closeout continues a frozen accepted state.

    frozen_log_text / candidate_log_text: raw handoff-transition.jsonl text.
    frozen_head_state: parsed accepted state at the frozen head.
    candidate_state: parsed candidate handoff-state.json.
    frozen_files / candidate_files: complete snapshots, repo-relative path -> bytes.
    allowlist: required explicit Allowlist; implementation changes and new evidence.
        Existing files cannot be deleted; evidence_added cannot rewrite history.
    authority_owner: exact expected admission owner.
    """
    failures = []
    checks_run = []

    frozen_lines = [l for l in frozen_log_text.split("\n") if l.strip()]
    candidate_lines = [l for l in candidate_log_text.split("\n") if l.strip()]

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

    try:
        frozen_records = [loads(l) for l in frozen_lines]
        candidate_records = [loads(l) for l in candidate_lines]
        if any(not isinstance(rec, dict) for rec in frozen_records + candidate_records):
            raise ValueError("transition records must be JSON objects")
    except ValueError as exc:
        _fail(failures, "chain-replay", "invalid history: " + str(exc))
        return CloseoutVerification(False, failures, checks_run, "failed")
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
        if not isinstance(admission, dict) or admission.get("by") != authority_owner:
            _fail(failures, "first-new-record",
                  f"admission does not identify {authority_owner!r} exactly: "
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
    try:
        receipt = _replay_text(candidate_log_text)
        state = receipt["state"] if receipt is not None else None
        if any(rec["validation"]["result"] != "accept" for rec in candidate_records):
            _fail(failures, "chain-replay", "accepted history contains a non-accepted record")
    except (ValueError, TypeError, KeyError) as exc:
        _fail(failures, "chain-replay", "canonical v0.1 replay failed: " + str(exc))
        replay_ok = False

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

    # Checks 6-7: byte identity and permissions supplied independently of the diff.
    checks_run.append("protected-files")
    checks_run.append("allowlist")
    files_ok = _verify_files(
        failures, frozen_files=frozen_files, candidate_files=candidate_files,
        allowlist=allowlist, task_dir=task_dir,
        frozen_log_text=frozen_log_text, candidate_log_text=candidate_log_text,
        frozen_head_state=frozen_head_state, final_state=state if replay_ok else None,
    )

    return CloseoutVerification(
        passed=not failures,
        failures=failures,
        checks_run=checks_run,
        file_checks="passed" if files_ok else "failed",
    )
