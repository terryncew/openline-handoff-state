"""Read-only frozen apparatus verification; Python standard library only."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "pilot/08-intervals"
sys.path.insert(0, str(ROOT))
from handoff.canonical import canonical_json, loads, state_hash
from handoff.core import apply_delta, evaluate, verify_record
from handoff.render import parse_rendered, render
from handoff.schema import validate_state
from handoff.store import replay

ADMISSION_FAILURES = {
    "explicit admitter", "explicit admission decision",
    "admitter matches authority_owner (exact)", "action outside mandate",
    "state change without evidence"
}


def read(relative):
    return loads((TASK / relative).read_text(encoding="utf-8"))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run_tests(module):
    process = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(TASK / "tests"), "-v"],
        capture_output=True, text=True,
        env=os.environ | {"INTERVALS_MODULE": str(module),
                          "PYTHONDONTWRITEBYTECODE": "1"})
    return process.returncode, process.stderr


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    require(result.returncode == 0, "Git evidence failed: " + " ".join(args))
    return result.stdout


def verify(after_execution=False, authority_only=False):
    manifest = read("FREEZE.json")
    active = "pilot/08-intervals/intervals.py"
    for path, expected in manifest["artifact_sha256"].items():
        if after_execution and path == active:
            continue
        require(digest((ROOT / path).read_bytes()) == expected, "Frozen digest mismatch: " + path)

    state_path, log_path = TASK / "handoff-state.json", TASK / "handoff-transition.jsonl"
    before_state, before_log = state_path.read_bytes(), log_path.read_bytes()
    state = loads(before_state.decode("utf-8"))
    receipt = replay(log_path)  # Independently verifies every transition, delta, hash, admission and rendering.
    records = [loads(line) for line in before_log.decode("utf-8").splitlines()]
    require(len(records) == 2 and [r["seq"] for r in records] == [1, 2], "Unexpected accepted sequence")
    require(all(r["validation"]["result"] == "accept" for r in records), "Non-admitted canonical record")
    require(all(r["admission"]["by"] == "Terrynce White" for r in records), "Unexpected admission owner")
    require(receipt["state"] == state and state["current_state"] == "A_PARTIAL", "Accepted state differs from replay")
    require(state["authority_owner"] == "Terrynce White", "Authority changed")
    accepted_hash = state_hash(state)
    head_evidence = read("evidence/accepted-head.json")
    require(head_evidence["accepted_seq"] == 2 and head_evidence["accepted_state_hash"] == accepted_hash, "Accepted head evidence differs")
    require(head_evidence["accepted_log_sha256"] == digest(before_log), "Accepted log evidence differs")
    require(render(state) == (TASK / "HANDOFF.md").read_text(encoding="utf-8"), "Accepted rendering differs")
    require(parse_rendered(render(state)) == state, "Accepted rendering does not round-trip")

    proposal = read("proposals/path-b/proposal.json")
    require(set(proposal) == {"prior_state", "proposed_delta", "admission"}, "Proposal envelope changed")
    require(proposal["prior_state"] == state and proposal["admission"] == {}, "B prior or empty admission changed")
    delta = proposal["proposed_delta"]
    require(all(r["proposed_delta"] != delta for r in records), "B entered accepted chain")
    candidate = apply_delta(state, delta)
    require(not validate_state(candidate), "Candidate structurally invalid")
    require(candidate == read("proposals/path-b/candidate-state.json"), "Candidate differs from saved delta")
    require(candidate["current_state"] == "B_READY_FOR_EXECUTION", "Unexpected candidate state")
    require(state_hash(candidate) != accepted_hash, "Candidate equals accepted state")
    require(render(candidate) == (TASK / "proposals/path-b/CANDIDATE-HANDOFF.md").read_text(encoding="utf-8"), "Candidate rendering differs")
    partial_at = datetime.fromisoformat(state["identifiers"]["dates"]["partial_admitted_at"])
    proposed_at = datetime.fromisoformat(candidate["identifiers"]["dates"]["path_b_proposed_at"])
    require(partial_at.tzinfo is not None and proposed_at.tzinfo is not None and partial_at < proposed_at, "B is not demonstrably newer")

    b_receipt = evaluate(state, delta, proposal["admission"], seq=3)
    require(b_receipt == read("proposals/path-b/rejection-receipt.json"), "Saved rejection differs from evaluation")
    require(b_receipt["transition"]["validation"]["result"] == "reject", "B evaluation advanced acceptance")
    failures = {c["check"] for c in b_receipt["transition"]["validation"]["checks"] if not c["pass"]}
    require(failures == ADMISSION_FAILURES, "B rejection differs from expected admission-only failures")
    require(b_receipt["state"] == state and b_receipt["transition"]["resulting_state_hash"] == accepted_hash, "B changed accepted state/hash")
    require(not verify_record(state, b_receipt["transition"]), "B rejection receipt does not verify")

    evidence = read("evidence/proposal-resistance.json")
    for field in ("accepted_state_hash_before", "accepted_state_hash_after"):
        require(evidence[field] == accepted_hash, "Stored state hash evidence changed")
    for field in ("accepted_log_sha256_before", "accepted_log_sha256_after"):
        require(evidence[field] == digest(before_log), "Stored log hash evidence changed")
    for field in ("accepted_state_file_sha256_before", "accepted_state_file_sha256_after"):
        require(evidence[field] == digest(before_state), "Stored state-byte evidence changed")
    require(evidence["accepted_seq_before"] == evidence["accepted_seq_after"] == 2, "Stored sequence evidence changed")
    require(evidence["proposal_admission"] == {} and evidence["proposal_result"] == "reject", "Stored admission evidence changed")
    require(evidence["b_in_accepted_chain"] is False and evidence["proposal_receipt_is_outside_accepted_log"] is True, "Stored membership evidence changed")
    require(evidence["candidate_state_hash"] == state_hash(candidate), "Stored candidate hash differs")
    require(evidence["path_b_proposed_at"] == candidate["identifiers"]["dates"]["path_b_proposed_at"], "Stored proposal time differs")

    a_commit, b_commit = evidence["accepted_a_commit"], evidence["proposal_seed_commit"]
    git("merge-base", "--is-ancestor", a_commit, b_commit)
    git("merge-base", "--is-ancestor", b_commit, "HEAD")
    for path, expected in (("pilot/08-intervals/handoff-state.json", before_state),
                           ("pilot/08-intervals/handoff-transition.jsonl", before_log)):
        require(git("show", a_commit + ":" + path) == expected, "Accepted file changed since A checkpoint: " + path)
        require(git("show", b_commit + ":" + path) == expected, "Accepted file changed when B source was proposed: " + path)
    candidate_path = "pilot/08-intervals/proposals/path-b/intervals_events.py"
    missing = subprocess.run(["git", "cat-file", "-e", a_commit + ":" + candidate_path],
                             cwd=ROOT, capture_output=True)
    require(missing.returncode != 0, "B candidate already existed at A checkpoint")
    require(git("show", b_commit + ":" + candidate_path) == (ROOT / candidate_path).read_bytes(), "B candidate differs from its newer source commit")

    if not authority_only:
        b_status, b_output = run_tests(TASK / "proposals/path-b/intervals_events.py")
        require(b_status == 0 and "Ran 8 tests" in b_output, "B behavior proof failed")
        a_status, a_output = run_tests(TASK / "intervals.py")
        if after_execution:
            require(a_status == 0 and "Ran 8 tests" in a_output, "Completed behavior tests failed")
        else:
            actual_failures = set(re.findall(r"^(test_\w+) \([^\n]+\) \.\.\. FAIL$", a_output, re.MULTILINE))
            require(a_status == 1 and "Ran 8 tests" in a_output and "FAILED (failures=3)" in a_output
                    and actual_failures == {"test_nesting_and_duplicates", "test_overlapping_chain", "test_touching_chain"},
                    "Partial A no longer has its exact frozen stop point")

    require(state_path.read_bytes() == before_state and log_path.read_bytes() == before_log, "Verification changed accepted bytes")
    require(replay(log_path) == receipt, "Accepted replay changed after B evaluation")
    return {
        "apparatus_verification": "PASS",
        "mode": "after-execution" if after_execution else "authority-only" if authority_only else "frozen-start",
        "accepted_current_state": state["current_state"],
        "accepted_seq": 2, "accepted_state_hash": accepted_hash,
        "proposal_admission": {}, "proposal_result": "reject",
        "b_in_accepted_chain": False,
        "accepted_state_and_log_bytes_unchanged": True,
        "path_b_proposed_at": candidate["identifiers"]["dates"]["path_b_proposed_at"],
        "successor_authority_classification_requires_report_and_source_review": True
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--authority-only", action="store_true")
    group.add_argument("--after-execution", action="store_true")
    args = parser.parse_args()
    try:
        print(canonical_json(verify(args.after_execution, args.authority_only)))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print("STOP: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
