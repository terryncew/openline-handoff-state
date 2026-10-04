"""Independent execution evidence; calls the existing CLI and canonical verifier."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
START = "4b655c310c9cb8601a8d5de9f459b1cb45393a25"
IMPLEMENTATION = "a981dc89c36ebcccebf989e622e981db5fedd454"
FROZEN = "c45b3c611ecb496d6facc62643f0d685fe039f2a"
CANDIDATE = "bd58f07fdad7076783f3dffaa28ca1fa1b4060a0"
TASK = "pilot/08-intervals"
OWNER = "Terrynce White"
IMPL = TASK + "/intervals.py"
EVIDENCE = [
    TASK + "/evidence/execution/canonical-python-preflight.txt",
    TASK + "/evidence/execution/closeout-ci-record.md",
]
ALLOW = ["--allow-implementation-changed", IMPL]
for path in EVIDENCE:
    ALLOW += ["--allow-evidence-added", path]
CASES = {}


def git(*args, cwd=ROOT):
    return subprocess.run(["git", *args], cwd=cwd, check=True,
                          capture_output=True).stdout


def invoke(label, expected, *, frozen=FROZEN, candidate=CANDIDATE,
           owner=OWNER, allowance=None, cwd=ROOT, detail=None):
    arguments = [sys.executable, "-m", "handoff", "verify-closeout",
                 "--frozen-ref", frozen, "--candidate-ref", candidate,
                 "--task-dir", TASK, "--owner", owner]
    arguments += ALLOW if allowance is None else allowance
    process = subprocess.run(arguments, cwd=cwd,
                             env=dict(os.environ, PYTHONPATH=str(ROOT)),
                             capture_output=True, text=True)
    assert process.returncode == expected, (label, process.returncode,
                                            process.stdout, process.stderr)
    report = json.loads(process.stdout) if expected != 2 else None
    if report is not None:
        assert report["passed"] is (expected == 0), (label, report)
        if detail:
            assert any(detail in failure["detail"]
                       for failure in report["failures"]), (label, report)
    CASES[label] = {"exit": process.returncode, "report": report,
                    "stderr": process.stderr}
    return report


positive = invoke("real08_cli_pass", 0)
assert positive["failures"] == [] and positive["file_checks"] == "passed"
required = {"passed", "failures", "checks_run", "file_checks",
            "frozen_ref", "candidate_ref", "task_dir", "authority_owner"}
assert required <= positive.keys()
invoke("without_evidence_allowances", 1,
       allowance=["--allow-implementation-changed", IMPL],
       detail="unlisted new file")
only_evidence = []
for path in EVIDENCE:
    only_evidence += ["--allow-evidence-added", path]
invoke("without_implementation_allowance", 1,
       allowance=only_evidence, detail="protected bytes changed")
invoke("wrong_owner", 1, owner="Someone Else", detail="owner admission")
invoke("unresolvable_ref", 2, frozen="deadbeef" * 5)
invoke("malformed_ref", 2, frozen="bad ref")
invoke("malformed_allowlist", 2,
       allowance=["--allow-evidence-added", "../forbidden.txt"])

with tempfile.TemporaryDirectory(prefix="real-handoff10-independent-") as folder:
    work = Path(folder)
    git("init", "-q", cwd=work)
    git("config", "user.name", "Isolated execution test", cwd=work)
    git("config", "user.email", "isolated-test@local", cwd=work)

    def seed(ref):
        names = git("ls-tree", "-r", "-z", "--name-only", ref,
                    "--", TASK + "/").decode().split("\0")
        for name in filter(None, names):
            target = work / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(git("show", ref + ":" + name))
        git("add", "-A", cwd=work)
        git("commit", "-qm", "Fixture snapshot", cwd=work)
        return git("rev-parse", "HEAD", cwd=work).decode().strip()

    frozen = seed(FROZEN)
    candidate = seed(CANDIDATE)
    invoke("isolated_real_fixture", 0, frozen=frozen, candidate=candidate, cwd=work)
    target = work / TASK / "SPEC.md"
    target.write_bytes(target.read_bytes() + b"\nprotected mutation\n")
    git("add", "-A", cwd=work)
    git("commit", "-qm", "Isolated protected mutation", cwd=work)
    mutated = git("rev-parse", "HEAD", cwd=work).decode().strip()
    invoke("protected_mutation", 1, frozen=frozen, candidate=mutated,
           cwd=work, detail="protected bytes changed")
    git("reset", "--hard", candidate, cwd=work)
    target = work / TASK / "evidence/execution/unlisted-independent.txt"
    target.write_text("unlisted file", encoding="utf-8")
    git("add", "-A", cwd=work)
    git("commit", "-qm", "Isolated unlisted addition", cwd=work)
    mutated = git("rev-parse", "HEAD", cwd=work).decode().strip()
    invoke("unlisted_addition", 1, frozen=frozen, candidate=mutated,
           cwd=work, detail="unlisted new file")

from handoff.__main__ import _load_closeout_inputs
from handoff.closeout import Allowlist, verify_closeout
from handoff.core import EVALUATOR_VERSION
from handoff.canonical import canonical_json, state_hash
from handoff.store import replay

assert EVALUATOR_VERSION == "0.1.1"
inputs = _load_closeout_inputs(FROZEN, CANDIDATE, TASK)
library = verify_closeout(
    frozen_log_text=inputs["frozen_log"],
    candidate_log_text=inputs["candidate_log"],
    frozen_head_state=inputs["frozen_state"],
    candidate_state=inputs["candidate_state"],
    frozen_files=inputs["frozen_files"],
    candidate_files=inputs["candidate_files"],
    allowlist=Allowlist(implementation_changed=[IMPL], evidence_added=EVIDENCE),
    authority_owner=OWNER, task_dir=TASK)
assert library.passed and library.failures == []
assert list(library.checks_run) == positive["checks_run"]
assert library.file_checks == positive["file_checks"]

# These comparisons audit preservation; they never supply file permissions.
old = git("ls-tree", "-r", "-z", "--name-only", START).decode().split("\0")
old = list(filter(None, old))
for path in old:
    original = git("show", START + ":" + path)
    assert git("show", IMPLEMENTATION + ":" + path) == original, path
    assert git("show", "HEAD:" + path) == original, path
    assert (ROOT / path).read_bytes() == original, path

logs = [path for path in old if path.endswith("handoff-transition.jsonl")]
replayed = {}
for path in logs:
    receipt = replay(ROOT / path)
    assert receipt is not None
    replayed[path] = {"seq": receipt["transition"]["seq"],
                      "state_hash": state_hash(receipt["state"])}
accepted = replay(ROOT / "pilot/10-cli/handoff-transition.jsonl")
assert accepted["transition"]["seq"] == 1
assert state_hash(accepted["state"]) == (
    "sha256:10a1bc1f1434afa833b1f8667bd95537d8271b030e66e14a223f82ffebd4be9a")
summary = {
    "cases": CASES,
    "canonical_library_pass": library.passed,
    "evaluator_version": EVALUATOR_VERSION,
    "all_starting_blobs_unchanged": len(old),
    "historical_replay": replayed,
    "accepted_seq": accepted["transition"]["seq"],
    "accepted_state_hash": state_hash(accepted["state"]),
    "implementation_commit": IMPLEMENTATION,
}
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text(canonical_json(summary) + "\n", encoding="utf-8")
print("INDEPENDENT=" + canonical_json(summary))
