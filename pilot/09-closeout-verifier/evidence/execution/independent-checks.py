"""Independent REAL-HANDOFF-09 verification; no repository writes."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path.cwd()))
from handoff.canonical import canonical_json, loads
from handoff.closeout import Allowlist, verify_closeout
from handoff.core import evaluate, verify_record

spec = importlib.util.spec_from_file_location(
    "frozen_fixture",
    Path.cwd() / "pilot/09-closeout-verifier/tests/test_closeout_verifier.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
module.Fixture.setUpClass()
fixture = module.Fixture()
TASK = module.TASK
results = []


def fresh():
    return fixture.base_kwargs()


def check(name, expected, kwargs):
    result = verify_closeout(**kwargs)
    failures = [{"check": f.check, "detail": f.detail} for f in result.failures]
    assert result.passed is expected, (name, expected, result.passed, failures)
    results.append({"case": name, "expected": expected,
                    "passed": result.passed, "failures": failures})


def put_log(kwargs, text):
    kwargs["candidate_log_text"] = text
    kwargs["candidate_files"][TASK + "/handoff-transition.jsonl"] = text.encode()


def edit_record(kwargs, index, edit):
    lines = kwargs["candidate_log_text"].split("\n")[:-1]
    record = loads(lines[index])
    edit(record)
    lines[index] = canonical_json(record)
    put_log(kwargs, "\n".join(lines) + "\n")


def put_state(kwargs, state):
    kwargs["candidate_state"] = state
    kwargs["candidate_files"][TASK + "/handoff-state.json"] = (
        canonical_json(state) + "\n").encode()


check("positive: legitimate admitted REAL-HANDOFF-08 closeout", True, fresh())

kwargs = fresh()
kwargs["candidate_files"][TASK + "/intervals.py"] += b"\n# allowed change\n"
check("positive: explicitly allowed implementation change", True, kwargs)

kwargs = fresh()
extra = TASK + "/evidence/execution/independent-allowed-note.txt"
kwargs["candidate_files"][extra] = b"independent evidence\n"
kwargs["allowlist"].evidence_added.append(extra)
check("positive: explicitly allowed evidence addition", True, kwargs)

kwargs = fresh()
alternate = "examples/reusable-closeout"


def moved(path):
    return alternate + path[len(TASK):] if path.startswith(TASK + "/") else path


for field in ("frozen_files", "candidate_files"):
    kwargs[field] = {moved(p): data for p, data in kwargs[field].items()}
kwargs["allowlist"] = Allowlist(
    implementation_changed=[moved(p) for p in kwargs["allowlist"].implementation_changed],
    evidence_added=[moved(p) for p in kwargs["allowlist"].evidence_added])
kwargs["task_dir"] = alternate
check("positive: alternate task directory and explicit allowlist", True, kwargs)

kwargs = fresh()
edit_record(kwargs, 0, lambda r: r.update(
    rendered_prose=r["rendered_prose"] + " rewritten"))
check("negative: rewritten historical transition", False, kwargs)

kwargs = fresh()
put_log(kwargs, "\n".join(kwargs["candidate_log_text"].split("\n")[1:]))
check("negative: deleted historical transition", False, kwargs)

for name, edit in (
    ("wrong prior hash", lambda r: r.update(prior_state_hash="sha256:" + "0" * 64)),
    ("skipped first new sequence", lambda r: r.update(seq=5)),
    ("missing owner admission", lambda r: r.update(admission={})),
    ("incorrect exact owner admission", lambda r: r["admission"].update(by="terrynce white")),
    ("unadmitted proposal marked accepted", lambda r: r["validation"].update(result="reject")),
    ("recorded final hash mismatch", lambda r: r.update(resulting_state_hash="sha256:" + "0" * 64)),
):
    kwargs = fresh()
    edit_record(kwargs, 2, edit)
    check("negative: " + name, False, kwargs)

kwargs = fresh()
state = copy.deepcopy(kwargs["candidate_state"])
state["verified_facts"].append({"fact": "injected", "evidence": "unauthorized"})
put_state(kwargs, state)
check("negative: final candidate state/hash mismatch", False, kwargs)

kwargs = fresh()
kwargs["candidate_files"][TASK + "/SPEC.md"] += b"\n# unauthorized mutation\n"
check("negative: protected-file mutation", False, kwargs)

kwargs = fresh()
kwargs["candidate_files"][TASK + "/evidence/execution/unlisted.txt"] = b"unlisted\n"
check("negative: unlisted new file", False, kwargs)

kwargs = fresh()
kwargs["allowlist"].implementation_changed = []
check("negative: change outside implementation_changed", False, kwargs)

kwargs = fresh()
kwargs["allowlist"].evidence_added = []
check("negative: addition outside evidence_added", False, kwargs)

kwargs = fresh()
del kwargs["candidate_files"][TASK + "/SPEC.md"]
check("negative: protected-file deletion", False, kwargs)

kwargs = fresh()
del kwargs["candidate_files"][TASK + "/intervals.py"]
check("negative: allowed implementation deleted", False, kwargs)

kwargs = fresh()
old_evidence = TASK + "/evidence/midtask-tests.txt"
kwargs["candidate_files"][old_evidence] += b"\nrewritten evidence\n"
kwargs["allowlist"].evidence_added.append(old_evidence)
check("negative: evidence_added cannot authorize historical evidence rewrite",
      False, kwargs)

for missing in ("frozen_files", "candidate_files", "allowlist"):
    kwargs = fresh()
    kwargs[missing] = None
    check("negative: missing " + missing, False, kwargs)

kwargs = fresh()
different = copy.deepcopy(kwargs["candidate_state"])
different["current_state"] = "TAMPERED_FILE_ONLY"
kwargs["candidate_files"][TASK + "/handoff-state.json"] = (
    canonical_json(different) + "\n").encode()
check("negative: actual state file differs from replay/state argument", False, kwargs)

kwargs = fresh()
kwargs["candidate_files"][TASK + "/handoff-transition.jsonl"] += b"\n"
check("negative: actual log file differs from log argument", False, kwargs)

kwargs = fresh()
kwargs["candidate_files"][TASK + "/HANDOFF.md"] += b"\ntampered rendering\n"
check("negative: HANDOFF differs from canonical rendering", False, kwargs)

kwargs = fresh()
kwargs["candidate_files"][TASK + "/HANDOFF.md"] += b"\nbypass attempt\n"
kwargs["allowlist"].implementation_changed.append(TASK + "/HANDOFF.md")
check("negative: implementation allowlist cannot override structural rendering",
      False, kwargs)

kwargs = fresh()
del kwargs["candidate_files"][TASK + "/handoff-state.json"]
check("negative: missing structural state file", False, kwargs)

kwargs = fresh()
put_log(kwargs, kwargs["candidate_log_text"].replace("\n", "\r\n", 1))
check("negative: frozen raw log prefix newline mutation", False, kwargs)

# Core-generated records below exist only in memory for hypothetical checks.
kwargs = fresh()
prior = kwargs["candidate_state"]
delta = {"current_state": {"from": prior["current_state"], "to": prior["current_state"]}}
rejected = evaluate(prior, delta, {}, seq=4)
assert rejected["transition"]["validation"]["result"] == "reject"
assert not verify_record(prior, rejected["transition"])
put_log(kwargs, kwargs["candidate_log_text"] + canonical_json(rejected["transition"]) + "\n")
check("negative: canonical rejection receipt appended to accepted history",
      False, kwargs)

kwargs = fresh()
prior = kwargs["candidate_state"]
admission = copy.deepcopy(loads(
    kwargs["candidate_log_text"].split("\n")[-2])["admission"])
admission["evidence"] = "HYPOTHETICAL independent validation preflight only"
accepted = evaluate(prior, delta, admission, seq=4)
assert accepted["transition"]["validation"]["result"] == "accept"
assert not verify_record(prior, accepted["transition"])
put_log(kwargs, kwargs["candidate_log_text"] + canonical_json(accepted["transition"]) + "\n")
check("positive: canonical accepted fourth record", True, kwargs)

kwargs = fresh()
skipped = evaluate(kwargs["candidate_state"], delta, admission, seq=5)
assert skipped["transition"]["validation"]["result"] == "accept"
assert not verify_record(kwargs["candidate_state"], skipped["transition"])
put_log(kwargs, kwargs["candidate_log_text"] + canonical_json(skipped["transition"]) + "\n")
check("negative: canonical later record with skipped sequence", False, kwargs)

START = "30349b77a154c44a0d8b076b45bff49f826cd5bc"


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True).stdout


# Entire existing 08 subtree must match starting main, including closeout evidence.
assert git("ls-tree", "-r", START, "--", TASK) == git("ls-tree", "-r", "HEAD", "--", TASK)
manifest = loads(Path(TASK + "/FREEZE.json").read_text())
legitimate_changes = {TASK + "/" + p for p in (
    "HANDOFF.md", "handoff-state.json", "handoff-transition.jsonl", "intervals.py")}
protected = {p: digest for p, digest in manifest["artifact_sha256"].items()
             if p not in legitimate_changes}
for path, digest in protected.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
assert Path(TASK + "/FREEZE.json").read_bytes() == git(
    "show", module.FROZEN + ":" + TASK + "/FREEZE.json")
for path in (
    "pilot/09-closeout-verifier/SPEC.md",
    "pilot/09-closeout-verifier/tests/test_closeout_verifier.py",
    "pilot/09-closeout-verifier/evidence/midtask-tests.txt",
    "pilot/09-closeout-verifier/handoff-state.json",
    "pilot/09-closeout-verifier/handoff-transition.jsonl",
    "pilot/09-closeout-verifier/HANDOFF.md",
):
    assert Path(path).read_bytes() == git("show", START + ":" + path), path
print("INDEPENDENT_JSON=" + json.dumps({
    "independent_verification": "PASS",
    "positive_cases": sum(item["expected"] for item in results),
    "negative_cases": sum(not item["expected"] for item in results),
    "cases": results,
    "entire_existing_08_subtree_unchanged": True,
    "original_08_protected_manifest_digests_verified": len(protected),
    "original_08_FREEZE_unchanged": True,
    "09_frozen_spec_tests_evidence_and_accepted_artifacts_unchanged": True,
    "implementation_sha256": hashlib.sha256(Path("handoff/closeout.py").read_bytes()).hexdigest(),
}, separators=(",", ":")))
