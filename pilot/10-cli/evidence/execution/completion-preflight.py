"""Canonical v0.1.1 proposal preflight. No actual admission or real log writes."""
from copy import deepcopy
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(subprocess.check_output(
    ["git", "rev-parse", "--show-toplevel"], text=True).strip())
sys.path.insert(0, str(ROOT))
from handoff.canonical import canonical_json, loads, state_hash
from handoff.core import EVALUATOR_VERSION, evaluate, same, verify_record
from handoff.store import replay

START = "4b655c310c9cb8601a8d5de9f459b1cb45393a25"
TASK = "pilot/10-cli"
STATE_PATH = TASK + "/handoff-state.json"
LOG_PATH = TASK + "/handoff-transition.jsonl"
EXPECTED_HASH = "sha256:10a1bc1f1434afa833b1f8667bd95537d8271b030e66e14a223f82ffebd4be9a"


def git_show(ref, path):
    return subprocess.check_output(["git", "show", ref + ":" + path], cwd=ROOT)


assert EVALUATOR_VERSION == "0.1.1"
original = {path: git_show(START, path) for path in (STATE_PATH, LOG_PATH)}
for path, content in original.items():
    assert (ROOT / path).read_bytes() == content, path
prior = loads(original[STATE_PATH].decode("utf-8"))
assert prior["current_state"] == "MID_TASK_CLOSEOUT_CLI"
assert state_hash(prior) == EXPECTED_HASH
ci_bytes = Path(sys.argv[1]).read_bytes()
ci = loads(ci_bytes.decode("utf-8"))
independent = loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
assert ci["workflow_path"] == ".github/workflows/closeout-cli-smoke.yml"
assert git_show(ci["head_sha"], ci["workflow_path"])
assert ci["conclusion"] == "success" and ci["smoke_exit"] == 0
smoke = ci["smoke_report"]
assert smoke["passed"] is True and smoke["failures"] == []
assert smoke["file_checks"] == "passed"
assert smoke["frozen_ref"] == prior["identifiers"]["shas"]["fixture_frozen"]
assert smoke["candidate_ref"] == prior["identifiers"]["shas"]["fixture_closeout"]
assert smoke["task_dir"] == "pilot/08-intervals"
assert smoke["authority_owner"] == prior["authority_owner"]
for name, count in (("cli", 11), ("handoff", 48), ("verifier", 11)):
    suite = ci["suites"][name]
    assert suite["testsRun"] == count and suite["successful"] is True
    assert "Ran " + str(count) + " tests" in suite["output"]
    assert suite["output"].endswith("OK")
assert independent["all_starting_blobs_unchanged"] > 0
assert independent["accepted_seq"] == 1
assert independent["accepted_state_hash"] == EXPECTED_HASH
assert independent["canonical_library_pass"] is True
assert independent["evaluator_version"] == "0.1.1"
for path in ("handoff/__main__.py", "handoff/closeout.py", "handoff/core.py",
             "handoff/canonical.py", "handoff/store.py", "handoff/schema.py",
             "handoff/render.py"):
    assert (ROOT / path).read_bytes() == git_show(START, path), path

ci_digest = hashlib.sha256(ci_bytes).hexdigest()
evidence = (
    f"GitHub Actions {ci['run_url']}; implementation {ci['head_sha']}; "
    f"workflow {ci['workflow_path']}; tested {ci['tested_at']}; "
    f"Ubuntu 24.04.5 / CPython 3.12.14; CI record sha256:{ci_digest}; "
    "pilot/10-cli/evidence/execution/ci-smoke.json; "
    "pilot/10-cli/evidence/execution/independent-verification.json"
)
facts = [
    {"fact": "The operational verify-closeout CLI exists in handoff/__main__.py and wraps canonical handoff.closeout.verify_closeout(); its implementation and canonical semantics remain byte-identical to the starting commit.",
     "evidence": evidence},
    {"fact": "The CI smoke actually invoked python -m handoff verify-closeout on real REAL-HANDOFF-08 frozen c45b3c611ecb496d6facc62643f0d685fe039f2a to admitted closeout bd58f07fdad7076783f3dffaa28ca1fa1b4060a0 with explicit implementation and evidence allowances: exit 0, valid JSON, passed true, no failures, file checks passed.",
     "evidence": evidence},
    {"fact": "Fresh CI passed 11/11 frozen REAL-HANDOFF-10 acceptance tests, 48/48 full Handoff State tests including historical replay compatibility, and 11/11 REAL-HANDOFF-09 verifier acceptance tests.",
     "evidence": evidence},
    {"fact": "Independent execution verified the positive CLI and allowance cases and rejection of protected mutation, unlisted addition, wrong owner, malformed or unresolvable ref, and malformed allowlist. All starting repository blobs, accepted history, REAL-HANDOFF-08 apparatus/evidence, and REAL-HANDOFF-09 history/evidence remain unchanged.",
     "evidence": evidence},
]
claims = [{
    "claim": "The existing canonical closeout CLI works through the added CI smoke on the real REAL-HANDOFF-08 fixture; frozen acceptance, full Handoff State, and verifier regression suites passed in the cited environment, with protected historical artifacts preserved.",
    "basis": evidence,
    "ceiling": "Bounded to the cited commits, Ubuntu 24.04.5 / CPython 3.12.14, real fixture, and executed cases. No general CI portability, networked verification, signatures, production hardening beyond tested cases, autonomous operation, or Stage 3 capability is claimed. Execution does not admit completion; Terrynce White alone has admission authority.",
}]
changes = deepcopy(prior["proposed_state_changes"])
pending = [item for item in changes if item["status"] == "remaining"]
assert len(pending) == 1
assert pending[0]["change"] == "CI smoke test/workflow demonstrating actual CLI invocation (SPEC requirement 11)"
pending[0].update(status="done", evidence=evidence)
delta = {
    "current_state": {"from": prior["current_state"], "to": "COMPLETE_CLOSEOUT_CLI"},
    "claims": {"from": deepcopy(prior["claims"]), "to": claims},
    "verified_facts": {"add": facts},
    "proposed_state_changes": {"from": deepcopy(prior["proposed_state_changes"]), "to": changes},
    "next_permitted_actions": {
        "from": deepcopy(prior["next_permitted_actions"]),
        "to": ["Terrynce White may review this unadmitted completion proposal and execution evidence and decide whether to admit it. No completion admission is recorded; no Stage 3 work is authorized."],
    },
}
proposal = {"prior_state": deepcopy(prior),
            "proposed_delta": deepcopy(delta), "admission": {}}
before = canonical_json(proposal)
with TemporaryDirectory(prefix="handoff10-hypothetical-only-") as directory:
    temporary_log = Path(directory) / "hypothetical-only.jsonl"
    temporary_log.write_bytes(original[LOG_PATH])
    baseline = replay(temporary_log)
    assert same(baseline["state"], prior)
    seq = baseline["transition"]["seq"] + 1
    assert seq == 2
    unadmitted = evaluate(prior, delta, {}, seq=seq)
    assert unadmitted["transition"]["validation"]["result"] == "reject"
    assert same(unadmitted["state"], prior)
    assert state_hash(unadmitted["state"]) == EXPECTED_HASH
    assert unadmitted["transition"]["resulting_state_hash"] == EXPECTED_HASH
    assert verify_record(prior, unadmitted["transition"]) == []
    hypothetical_admission = {
        "decision": "admit", "by": prior["authority_owner"], "at": ci["tested_at"],
        "evidence": "HYPOTHETICAL PREFLIGHT ONLY. No actual owner decision or admission is asserted.",
    }
    hypothetical = evaluate(prior, delta, hypothetical_admission, seq=seq)
    assert hypothetical["transition"]["validation"]["result"] == "accept"
    assert verify_record(prior, hypothetical["transition"]) == []
    for field in set(prior) - set(delta):
        assert same(prior[field], hypothetical["state"][field]), field
    assert same(hypothetical["state"]["verified_facts"][:len(prior["verified_facts"])],
                prior["verified_facts"])
    temporary_log.write_text(
        original[LOG_PATH].decode("utf-8") +
        canonical_json(hypothetical["transition"]) + "\n",
        encoding="utf-8", newline="")
    replayed = replay(temporary_log)
    assert same(replayed["state"], hypothetical["state"])
    assert replayed["transition"]["resulting_state_hash"] == state_hash(hypothetical["state"])
    # Replay a rejection separately; accepted state must still remain at seq-1's hash.
    temporary_log.write_text(
        original[LOG_PATH].decode("utf-8") +
        canonical_json(unadmitted["transition"]) + "\n",
        encoding="utf-8", newline="")
    rejected_replay = replay(temporary_log)
    assert same(rejected_replay["state"], prior)
    assert rejected_replay["transition"]["resulting_state_hash"] == EXPECTED_HASH
assert canonical_json(proposal) == before and proposal["admission"] == {}
for path, content in original.items():
    assert (ROOT / path).read_bytes() == content, path
summary = {
    "passed": True, "evaluator_version": EVALUATOR_VERSION,
    "starting_ref": START, "proposed_seq": seq,
    "accepted_seq": 1, "prior_state_hash": EXPECTED_HASH,
    "unadmitted_result": "reject", "unadmitted_state_and_hash_unchanged": True,
    "unadmitted_verify_record_passed": True, "unadmitted_temporary_replay_passed": True,
    "hypothetical_only": True, "hypothetical_result": "accept",
    "hypothetical_verify_record_passed": True, "hypothetical_temporary_replay_passed": True,
    "hypothetical_resulting_state_hash": state_hash(hypothetical["state"]),
    "accepted_state_and_history_bytes_unchanged": True,
    "ci_run_url": ci["run_url"], "ci_head_sha": ci["head_sha"],
    "ci_evidence_sha256": ci_digest,
}
print("COMPPROPOSAL=" + canonical_json(proposal))
print("PREFLIGHT=" + canonical_json(summary))
