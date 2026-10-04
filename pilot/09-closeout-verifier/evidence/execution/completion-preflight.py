"""Canonical Python v0.1 completion preflight; no actual owner admission."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path.cwd()))
from handoff.canonical import canonical_json, loads, state_hash
from handoff.core import apply_delta, evaluate, verify_record
from handoff.render import render
from handoff.store import replay

START = "30349b77a154c44a0d8b076b45bff49f826cd5bc"
IMPLEMENTATION = "37674170c4c0f50d5e0cc21065012ab0662b657c"
TASK = Path("pilot/09-closeout-verifier")
proposal_path = TASK / "proposals/completion/proposal.json"
proposal = loads(proposal_path.read_text(encoding="utf-8"))
state_path = TASK / "handoff-state.json"
log_path = TASK / "handoff-transition.jsonl"
prose_path = TASK / "HANDOFF.md"
before = {p: p.read_bytes() for p in (state_path, log_path, prose_path)}
prior = loads(before[state_path].decode("utf-8"))
assert proposal["prior_state"] == prior and proposal["admission"] == {}
accepted = replay(log_path)
assert accepted["state"] == prior and accepted["transition"]["seq"] == 1
assert not verify_record(None, accepted["transition"])
assert before[prose_path] == render(prior).encode("utf-8")
delta = proposal["proposed_delta"]
candidate = apply_delta(prior, delta)
for field in ("goal", "frozen_invariants", "stop_conditions", "authority_owner",
              "roles", "canonical_terms", "claims", "open_questions",
              "failed_or_superseded_paths"):
    assert canonical_json(candidate[field]) == canonical_json(prior[field]), field
assert candidate["verified_facts"][:len(prior["verified_facts"])] == prior["verified_facts"]
for group, values in prior["identifiers"].items():
    assert all(candidate["identifiers"][group][k] == v for k, v in values.items())
assert hashlib.sha256(Path("handoff/closeout.py").read_bytes()).hexdigest() == candidate[
    "identifiers"]["shas"]["closeout_py_completed"]

without = evaluate(prior, delta, {}, seq=2)
assert without["transition"]["validation"]["result"] == "reject"
assert without["state"] == prior
assert without["transition"]["resulting_state_hash"] == state_hash(prior)
assert not verify_record(prior, without["transition"])
cli = subprocess.run([sys.executable, "-m", "handoff", "validate", str(proposal_path)],
                     capture_output=True, text=True)
assert cli.returncode == 2
assert loads(cli.stdout)["transition"]["validation"]["result"] == "reject"

# A declaration used solely for mechanical hypothetical preflight.
# It is not an owner action and is never written to accepted repository files.
hypothetical_admission = {
    "decision": "admit", "by": "Terrynce White",
    "at": "2026-10-04T00:00:00Z",
    "evidence": "HYPOTHETICAL exact-owner preflight only; no actual owner admission",
}
hypothetical = evaluate(prior, delta, hypothetical_admission, seq=2)
assert hypothetical["transition"]["validation"]["result"] == "accept"
assert hypothetical["state"] == candidate
assert not verify_record(prior, hypothetical["transition"])
with tempfile.TemporaryDirectory() as directory:
    temp = Path(directory)
    hypothetical_log = temp / "hypothetical-only.jsonl"
    hypothetical_log.write_bytes(before[log_path] + (
        canonical_json(hypothetical["transition"]) + "\n").encode("utf-8"))
    assert replay(hypothetical_log) == hypothetical
    rejected_log = temp / "rejection-receipt-only.jsonl"
    rejected_log.write_bytes(before[log_path] + (
        canonical_json(without["transition"]) + "\n").encode("utf-8"))
    assert replay(rejected_log) == without
    envelope = temp / "hypothetical-only-proposal.json"
    request = dict(proposal, admission=hypothetical_admission)
    envelope.write_text(canonical_json(request), encoding="utf-8")
    hypothetical_cli = subprocess.run(
        [sys.executable, "-m", "handoff", "validate", str(envelope)],
        capture_output=True, text=True)
    assert hypothetical_cli.returncode == 0
    assert loads(hypothetical_cli.stdout)["state"] == candidate
assert all(path.read_bytes() == data for path, data in before.items())
assert replay(log_path) == accepted

def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout

assert git("ls-tree", "-r", START, "--", "pilot/08-intervals") == git(
    "ls-tree", "-r", "HEAD", "--", "pilot/08-intervals")
for path, data in before.items():
    assert git("show", START + ":" + str(path)) == data
assert git("show", IMPLEMENTATION + ":handoff/closeout.py") == Path(
    "handoff/closeout.py").read_bytes()
assert proposal_path.read_bytes() == git("show", "HEAD:" + str(proposal_path))
print("COMPLETION_PREFLIGHT_JSON=" + json.dumps({
    "without_admission": without["transition"]["validation"]["result"],
    "without_admission_failed_checks": [
        c["check"] for c in without["transition"]["validation"]["checks"] if not c["pass"]],
    "accepted_seq_before": accepted["transition"]["seq"],
    "accepted_seq_after": replay(log_path)["transition"]["seq"],
    "accepted_state_hash_before": state_hash(prior),
    "accepted_state_hash_after": state_hash(replay(log_path)["state"]),
    "accepted_artifact_bytes_unchanged": True,
    "hypothetical_exact_owner_preflight": hypothetical["transition"]["validation"]["result"],
    "hypothetical_failed_checks": [
        c["check"] for c in hypothetical["transition"]["validation"]["checks"] if not c["pass"]],
    "hypothetical_candidate_hash": state_hash(candidate),
    "receipt_verification": "PASS",
    "rejection_receipt_replay": "PASS",
    "hypothetical_accepted_replay": "PASS",
    "canonical_cli_without_admission_exit": cli.returncode,
    "canonical_cli_hypothetical_exit": hypothetical_cli.returncode,
    "proposal_file_sha256": hashlib.sha256(proposal_path.read_bytes()).hexdigest(),
    "no_actual_owner_admission": True,
}, separators=(",", ":")))
