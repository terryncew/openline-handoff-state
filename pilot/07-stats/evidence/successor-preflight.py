"""Read-only checks for the unaccepted REAL-HANDOFF-07 completion proposal."""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from handoff.canonical import loads, state_hash
from handoff.core import evaluate, same, verify_record
from handoff.store import replay

task = ROOT / "pilot/07-stats"
log = task / "handoff-transition.jsonl"
state_file = task / "handoff-state.json"
proposal_file = task / "proposed-completion.json"
expected_hash = "sha256:90d4553808ac86b086fd26086f3a405c8430dee58404333f656d50838d80b587"
historical_hash = "sha256:2a2eadac6d3acf171250a45aac5542e53345549b81e3d060419e613eeab7301d"
log_before = log.read_bytes()
state_before = state_file.read_bytes()
proposal = loads(proposal_file.read_text(encoding="utf-8"))
assert set(proposal) == {"prior_state", "proposed_delta", "admission"}
assert proposal["admission"] == {}
head = replay(log)
prior = head["state"]
assert head["transition"]["seq"] == 2
assert state_hash(prior) == expected_hash
assert same(prior, loads(state_file.read_text(encoding="utf-8")))
assert same(prior, proposal["prior_state"])
records = [loads(line) for line in log_before.decode("utf-8").splitlines()]
assert len(records) == 2
assert records[0]["validation"]["result"] == "accept"
assert records[1]["validation"]["result"] == "accept"
assert records[0]["resulting_state_hash"] == historical_hash
assert records[1]["prior_state_hash"] == historical_hash
assert records[1]["resulting_state_hash"] == expected_hash
assert prior["current_state"] == "MID_TASK_STRICT_INPUT"
assert prior["failed_or_superseded_paths"]
delta = proposal["proposed_delta"]
assert delta["current_state"] == {"from": "MID_TASK_STRICT_INPUT", "to": "COMPLETE_STRICT_INPUT"}
assert hashlib.sha256((task / "stats.py").read_bytes()).hexdigest() == delta["identifiers.shas"]["add"]["successor_stats_py"]

unadmitted = evaluate(prior, delta, {}, seq=3)
assert unadmitted["transition"]["validation"]["result"] == "reject"
assert same(unadmitted["state"], prior)
assert unadmitted["transition"]["prior_state_hash"] == expected_hash
assert unadmitted["transition"]["resulting_state_hash"] == expected_hash
assert verify_record(prior, unadmitted["transition"]) == []
print("UNADMITTED_PROPOSAL: REJECT")
print("ACCEPTED_STATE_AND_HASH_WITHOUT_ADMISSION: UNCHANGED")

# An in-memory mechanical hypothesis only. Never append or persist this receipt.
hypothetical_admission = {
    "by": prior["authority_owner"],
    "decision": "admit",
    "at": "2026-10-04T00:00:00+00:00",
    "evidence": "HYPOTHETICAL OWNER-ADMISSION PREFLIGHT ONLY: no owner declaration was obtained; no actual admission is performed.",
}
hypothetical = evaluate(prior, delta, hypothetical_admission, seq=3)
assert hypothetical["transition"]["validation"]["result"] == "accept", hypothetical["transition"]["validation"]
assert all(item["pass"] for item in hypothetical["transition"]["validation"]["checks"])
assert verify_record(prior, hypothetical["transition"]) == []
candidate = hypothetical["state"]
for field in (
    "schema", "task_id", "goal", "authority_owner", "claims",
    "frozen_invariants", "canonical_terms", "open_questions",
    "failed_or_superseded_paths", "stop_conditions", "roles",
):
    assert same(candidate[field], prior[field]), field
assert same(candidate["verified_facts"][:len(prior["verified_facts"])], prior["verified_facts"])
for group, identifiers in prior["identifiers"].items():
    for key, value in identifiers.items():
        assert same(candidate["identifiers"][group][key], value)

for text in ("1,2\n", "1\n2,3\n", ",\n"):
    result = subprocess.run(
        [sys.executable, "-B", str(task / "stats.py")],
        input=text, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 1
    assert result.stderr == "BAD_INPUT\n"
    assert result.stdout == ""

assert log.read_bytes() == log_before
assert state_file.read_bytes() == state_before
after = replay(log)
assert after["transition"]["seq"] == 2
assert state_hash(after["state"]) == expected_hash
print("HYPOTHETICAL_OWNER_ADMISSION_PREFLIGHT: PASS")
print("ACCEPTED_HISTORY_AND_CONSTRAINTS_PRESERVED: PASS")
print("CURRENT_HEAD: seq 2 " + expected_hash)
print("SUPERSEDED_COMMA_ACCEPTANCE: NOT_REVIVED")
print("ACTUAL_OWNER_ADMISSION: NOT_PERFORMED")
