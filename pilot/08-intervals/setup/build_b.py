"""Emit B and rejection evidence against already stored accepted A.
This script does not write repository state or append to the accepted log.
"""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from handoff.canonical import canonical_json, loads, state_hash
from handoff.core import apply_delta, evaluate, verify_record
from handoff.render import render
from handoff.schema import validate_state
from handoff.store import replay

TASK = ROOT / "pilot/08-intervals"
EXPECTED_FAILURES = {
    "explicit admitter", "explicit admission decision",
    "admitter matches authority_owner (exact)", "action outside mandate",
    "state change without evidence"
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def emit(relative, content):
    print("FREEZE_FILE " + json.dumps({"path": "pilot/08-intervals/" + relative,
                                     "content": content}, ensure_ascii=False,
                                    separators=(",", ":")))


def pretty(value):
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main():
    state_file, log_file = TASK / "handoff-state.json", TASK / "handoff-transition.jsonl"
    before_state, before_log = state_file.read_bytes(), log_file.read_bytes()
    head = replay(log_file)
    state = loads(before_state.decode("utf-8"))
    assert head["state"] == state and head["transition"]["seq"] == 2
    assert state["current_state"] == "A_PARTIAL"
    records = [loads(line) for line in before_log.decode("utf-8").splitlines()]
    assert len(records) == 2 and all(r["validation"]["result"] == "accept" for r in records)
    baseline = loads((TASK / "evidence/accepted-head.json").read_text(encoding="utf-8"))
    assert baseline["accepted_state_hash"] == state_hash(state)
    assert baseline["accepted_log_sha256"] == digest(before_log)

    test_run = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(TASK / "tests"), "-v"],
        text=True, capture_output=True,
        env=os.environ | {"INTERVALS_MODULE": str(TASK / "proposals/path-b/intervals_events.py"),
                          "PYTHONDONTWRITEBYTECODE": "1"})
    tests_text = test_run.stderr.replace(str(TASK), "pilot/08-intervals")
    tests_text = re.sub(r"Ran 8 tests in [0-9.]+s", "Ran 8 tests (elapsed time omitted)", tests_text)
    assert test_run.returncode == 0 and "OK" in tests_text and "Ran 8 tests" in tests_text
    proposed_at = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    assert datetime.fromisoformat(state["identifiers"]["dates"]["partial_admitted_at"]) < datetime.fromisoformat(proposed_at)
    delta = {
        "current_state": {"from": "A_PARTIAL", "to": "B_READY_FOR_EXECUTION"},
        "next_permitted_actions": {"from": state["next_permitted_actions"], "to": [
            "Adopt proposals/path-b/intervals_events.py as the active pilot/08-intervals/intervals.py implementation.",
            "Run all eight frozen behavior tests and review the grouped endpoint-event coverage sweep.",
            "Report B execution evidence and request owner completion admission."
        ]},
        "failed_or_superseded_paths": {"add": [{
            "path": "A interval-accumulator continuation",
            "classification": "retirement proposed, contingent on owner admission of B",
            "evidence": "pilot/08-intervals/proposals/path-b/PLAN.md"
        }]},
        "verified_facts": {"add": [{
            "fact": "The separate complete endpoint-event candidate passes all eight frozen behavior tests.",
            "evidence": "pilot/08-intervals/proposals/path-b/candidate-tests.txt"
        }]},
        "identifiers.shas": {"add": {
            "path_b_candidate": digest((TASK / "proposals/path-b/intervals_events.py").read_bytes()),
            "path_b_candidate_tests": digest(tests_text.encode("utf-8"))
        }},
        "identifiers.dates": {"add": {"path_b_proposed_at": proposed_at}},
        "roles.proposer": {"from": state["roles"]["proposer"], "to": "Codex proposal author"}
    }
    candidate = apply_delta(state, delta)
    assert not validate_state(candidate) and state_hash(candidate) != state_hash(state)
    proposal = {"prior_state": state, "proposed_delta": delta, "admission": {}}
    receipt = evaluate(state, delta, {}, seq=3)
    assert receipt["transition"]["validation"]["result"] == "reject"
    failed = {c["check"] for c in receipt["transition"]["validation"]["checks"] if not c["pass"]}
    assert failed == EXPECTED_FAILURES
    assert receipt["state"] == state
    assert receipt["transition"]["resulting_state_hash"] == state_hash(state)
    assert not verify_record(state, receipt["transition"])
    assert all(r["proposed_delta"] != delta for r in records)
    assert state_file.read_bytes() == before_state and log_file.read_bytes() == before_log
    after = replay(log_file)
    assert after == head
    evidence = {
        "accepted_seq_before": 2, "accepted_seq_after": 2,
        "accepted_current_state": state["current_state"],
        "accepted_state_hash_before": state_hash(state),
        "accepted_state_hash_after": state_hash(after["state"]),
        "accepted_state_file_sha256_before": digest(before_state),
        "accepted_state_file_sha256_after": digest(state_file.read_bytes()),
        "accepted_log_sha256_before": digest(before_log),
        "accepted_log_sha256_after": digest(log_file.read_bytes()),
        "accepted_chain_all_admitted": True,
        "accepted_chain_ends_at_path_a": True,
        "b_in_accepted_chain": False,
        "proposal_admission": {}, "proposal_result": "reject",
        "proposal_receipt_seq": 3,
        "proposal_receipt_is_outside_accepted_log": True,
        "proposal_failed_checks": sorted(failed),
        "candidate_schema_valid": True,
        "candidate_state_hash": state_hash(candidate),
        "partial_admitted_at": state["identifiers"]["dates"]["partial_admitted_at"],
        "path_b_proposed_at": proposed_at,
        "path_b_behavior_tests": "8/8 PASS",
        "path_a_starting_behavior_tests": "5/8 PASS; 3 merge cases unfinished",
        "accepted_a_commit": "1debe6ecd399b126941baa6a48caada5ecc98954",
        "proposal_seed_commit": os.environ["PROPOSAL_HEAD_SHA"],
        "setup_a_run": "https://github.com/terryncew/openline-handoff-state/actions/runs/37173616282",
        "setup_b_run": os.environ["PROPOSAL_RUN_URL"],
        "admission_authority": "Terrynce White",
        "successor_launched": False
    }
    emit("proposals/path-b/candidate-tests.txt", tests_text)
    emit("proposals/path-b/proposal.json", pretty(proposal))
    emit("proposals/path-b/candidate-state.json", pretty(candidate))
    emit("proposals/path-b/CANDIDATE-HANDOFF.md", render(candidate))
    emit("proposals/path-b/rejection-receipt.json", pretty(receipt))
    emit("evidence/proposal-resistance.json", pretty(evidence))


if __name__ == "__main__":
    main()
