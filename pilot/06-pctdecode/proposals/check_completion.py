"""Read-only completion-proposal preflight; never records owner admission."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from handoff.canonical import loads, state_hash
from handoff.core import apply_delta, evaluate, same, verify_record
from handoff.render import parse_rendered
from handoff.schema import validate_state
from handoff.store import replay

START = "bc66ddbc4b6f8ed26c57e5df138cb1d0a634207d"
SUCCESSOR = "05c2af845d224efcaf41eb5058e24d3595cc4633"
TASK = ROOT / "pilot/06-pctdecode"
CODE_PATH = "pilot/06-pctdecode/pctdecode.py"

def git_bytes(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def tree(ref):
    entries = {}
    for item in git_bytes("ls-tree", "-rz", "--full-tree", ref).split(b"\0"):
        if item:
            metadata, path = item.split(b"\t", 1)
            entries[path.decode("utf-8")] = metadata.decode("ascii")
    return entries

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

proposal = loads((TASK / "proposals/completion.json").read_text(encoding="utf-8"))
assert set(proposal) == {"prior_state", "proposed_delta", "admission"}
assert proposal["admission"] == {}
log_path = TASK / "handoff-transition.jsonl"
log_before = log_path.read_bytes()
state_before = (TASK / "handoff-state.json").read_bytes()
head = replay(log_path)
prior = head["state"]
assert same(loads(state_before.decode("utf-8")), prior)
assert same(proposal["prior_state"], prior)
seq = head["transition"]["seq"] + 1
accepted_hash = state_hash(prior)
assert seq == 2
assert accepted_hash == "sha256:398982ebfddaed95c2741ccedb1aa462c29fc642532403335854e6e89703814a"
assert head["transition"]["resulting_state_hash"] == accepted_hash

starting_tree = tree(START)
successor_tree = tree(SUCCESSOR)
current_tree = tree("HEAD")
assert git_bytes("rev-parse", SUCCESSOR + "^").decode().strip() == START
assert set(successor_tree) == set(starting_tree)
assert {path for path in starting_tree
        if starting_tree[path] != successor_tree[path]} == {CODE_PATH}
assert all(current_tree.get(path) == metadata
           for path, metadata in starting_tree.items() if path != CODE_PATH)
assert current_tree[CODE_PATH] == successor_tree[CODE_PATH]

original = git_bytes("show", START + ":" + CODE_PATH).decode("utf-8")
expected = original.replace(
    "MID-TASK STATE: %XX decoding works (4/6 pass). Malformed-% handling NOT\n"
    "done: a '%' not followed by two hex digits currently aborts with\n"
    "BAD_ESCAPE instead of the spec-required literal passthrough\n"
    "(test_malformed_left_literal and test_lone_percent_end fail).\n\n", "")
expected = expected.replace(
    "                return None  # MID-TASK GAP: spec requires literal '%'\n",
    '                out.append("%")\n                i += 1\n                continue\n')
source = (TASK / "pctdecode.py").read_bytes()
assert source.decode("utf-8") == expected

delta = proposal["proposed_delta"]
candidate = apply_delta(prior, delta)
assert validate_state(candidate) == []
assert candidate["current_state"] == "FROZEN_ACCEPTANCE_COMPLETE_PLUS_UNRESOLVED"
for field in (
    "schema", "task_id", "goal", "authority_owner", "roles", "claims",
    "canonical_terms", "frozen_invariants", "stop_conditions", "open_questions",
    "proposed_state_changes",
):
    assert same(candidate[field], prior[field]), field
for field in ("verified_facts", "failed_or_superseded_paths"):
    assert len(candidate[field]) >= len(prior[field])
    assert same(candidate[field][:len(prior[field])], prior[field]), field
for group, values in prior["identifiers"].items():
    assert all(same(candidate["identifiers"][group][key], value)
               for key, value in values.items()), group
assert candidate["identifiers"]["receipts"]["successor_commit"] == SUCCESSOR
assert digest(source) == candidate["identifiers"]["shas"]["pctdecode_successor"]
for key, name in (
    ("successor_task_tests", "evidence/successor-task-tests.txt"),
    ("successor_handoff_tests", "evidence/successor-handoff-tests.txt"),
):
    value = digest((TASK / name).read_bytes())
    assert value == candidate["identifiers"]["shas"][key]
    assert any("sha256:" + value in fact["evidence"]
               for fact in delta["verified_facts"]["add"])

missing = evaluate(prior, delta, {}, seq=seq)
record = missing["transition"]
assert record["validation"]["result"] == "reject"
assert same(missing["state"], prior)
assert record["prior_state_hash"] == accepted_hash
assert record["resulting_state_hash"] == accepted_hash
assert verify_record(prior, record) == []
assert same(parse_rendered(record["rendered_prose"]), prior)

# Pure evaluation of a hypothetical declaration only. No store.append call.
hypothesis = {
    "decision": "admit",
    "by": prior["authority_owner"],
    "at": "2026-10-04T00:00:00Z",
    "evidence": "HYPOTHETICAL PREFLIGHT ONLY; no owner admission recorded",
}
hypothetical = evaluate(prior, delta, hypothesis, seq=seq)
assert hypothetical["transition"]["validation"]["result"] == "accept"
assert all(item["pass"] for item in hypothetical["transition"]["validation"]["checks"])
assert same(hypothetical["state"], candidate)
assert verify_record(prior, hypothetical["transition"]) == []
assert same(parse_rendered(hypothetical["transition"]["rendered_prose"]), candidate)

assert log_path.read_bytes() == log_before
assert (TASK / "handoff-state.json").read_bytes() == state_before
assert state_hash(replay(log_path)["state"]) == accepted_hash
assert replay(log_path)["transition"]["seq"] == 1

print(json.dumps({
    "starting_commit": START,
    "successor_commit": SUCCESSOR,
    "successor_changes_only": [CODE_PATH],
    "pctdecode_successor_sha256": digest(source),
    "unadmitted_result": record["validation"]["result"],
    "unadmitted_failed_checks": [x["check"] for x in record["validation"]["checks"] if not x["pass"]],
    "accepted_state_unchanged": True,
    "accepted_hash_before": accepted_hash,
    "accepted_hash_after": state_hash(replay(log_path)["state"]),
    "accepted_sequence": 1,
    "protected_starting_artifacts_unchanged": True,
    "claims_preserved_exactly": True,
    "claim_ceiling_preserved_exactly": True,
    "open_questions_preserved_exactly": True,
    "canonical_terms_preserved_exactly": True,
    "frozen_invariants_preserved_exactly": True,
    "stop_conditions_preserved_exactly": True,
    "historical_evidence_preserved": True,
    "hypothetical_owner_preflight": hypothetical["transition"]["validation"]["result"],
    "hypothetical_all_checks_pass": True,
    "hypothetical_receipt_verified": True,
    "actual_owner_admission_performed": False,
    "history_written": False
}, sort_keys=True, indent=2))
