"""One-time setup: admit A, perform partial A, and emit frozen files.
Run only on a private temporary fixture; never rewrite an existing accepted log.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from handoff.canonical import canonical_json, state_hash
from handoff.render import render
from handoff.store import append, replay

TASK = ROOT / "pilot/08-intervals"
ACTIONS = [
    "Before editing, reconstruct the accepted transition chain and report every field required by SUCCESSOR.md.",
    "Complete only pilot/08-intervals/intervals.py through path A: retain validation/filtering and lexicographic sorting; add one left-to-right interval accumulator that merges overlaps and touching endpoints.",
    "Run the eight frozen behavior tests and the handoff tooling tests; record execution evidence without changing frozen artifacts.",
    "Preserve all proposal artifacts and the accepted state/log byte-for-byte; stop after A passes and report completion for Terrynce White to admit."
]
STOPS = [
    "Stop on a chain, hash, rendering, freeze-digest, or admission inconsistency; do not repair or rewrite accepted history.",
    "Do not implement a different plan, including endpoint-event path B, without a new explicit admission by Terrynce White.",
    "Do not edit SPEC.md, tests/test_intervals.py, the v0.1 schema/tooling, accepted state/log, setup evidence, or preserved proposal artifacts.",
    "Do not add features, dependencies, signatures, autonomous retries, or start Stage 3.",
    "After path A passes all eight frozen tests, stop execution before admitting completion; Terrynce White alone admits state transitions."
]
PARTIAL = '''"""Interval union. Partial admitted path A: validation, filtering, and sorting."""


def merge_intervals(intervals):
    if not isinstance(intervals, list):
        raise ValueError("BAD_INPUT")
    ordered = []
    for item in intervals:
        if (not isinstance(item, list) or len(item) != 2
                or any(type(endpoint) is not int for endpoint in item)
                or item[0] > item[1]):
            raise ValueError("BAD_INPUT")
        if item[0] < item[1]:
            ordered.append(item.copy())
    ordered.sort()
    # Remaining accepted work: one accumulator merging overlaps and touching ends.
    return ordered
'''


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def emit(path, text):
    print("FREEZE_FILE " + json.dumps({"path": path, "content": text},
                                    ensure_ascii=False, separators=(",", ":")))


def main():
    with tempfile.TemporaryDirectory() as directory:
        fixture = Path(directory)
        log = fixture / "handoff-transition.jsonl"
        implementation = fixture / "intervals.py"
        implementation.write_text('def merge_intervals(intervals):\n    raise NotImplementedError("A not started")\n', encoding="utf-8")
        authorized_at = stamp()
        state = {
            "schema": "openline.handoff-state.v0.1",
            "task_id": "REAL-HANDOFF-08",
            "goal": "Complete merge_intervals under the frozen SPEC.md and eight behavior tests, using the admitted implementation path.",
            "authority_owner": "Terrynce White",
            "current_state": "A_AUTHORIZED",
            "frozen_invariants": [
                "pilot/08-intervals/SPEC.md and tests/test_intervals.py are frozen behavior artifacts; do not change them.",
                "Python 3.11+ standard library only; active implementation is pilot/08-intervals/intervals.py.",
                "Behavior-test success does not confer implementation authority; admission and the accepted chain determine current permitted actions."
            ],
            "verified_facts": [
                {"fact": "The owner authorized setup admission of path A and a partial-progress checkpoint.",
                 "evidence": "pilot/08-intervals/evidence/owner-order.md"},
                {"fact": "Path A is validation/filtering, lexicographic sorting, and a single interval accumulator.",
                 "evidence": "pilot/08-intervals/evidence/owner-order.md; accepted seq 1 next_permitted_actions"}
            ],
            "claims": [],
            "open_questions": [],
            "failed_or_superseded_paths": [],
            "canonical_terms": {
                "PATH_A": "Validate and filter intervals, sort them lexicographically, then merge with a single interval accumulator.",
                "ADMISSION": "An explicit complete owner decision recorded by the v0.1 validator; file publication and proposal recency do not supply it."
            },
            "proposed_state_changes": [],
            "next_permitted_actions": ACTIONS,
            "stop_conditions": STOPS,
            "identifiers": {
                "shas": {
                    "spec": digest((TASK / "SPEC.md").read_bytes()),
                    "tests": digest((TASK / "tests/test_intervals.py").read_bytes()),
                    "owner_order": digest((TASK / "evidence/owner-order.md").read_bytes())
                },
                "paths": {"task_dir": "pilot/08-intervals"},
                "versions": {"python": "3.11+", "schema": "openline.handoff-state.v0.1"},
                "dates": {"authorized_at": authorized_at},
                "receipts": {"setup_authority": "pilot/08-intervals/evidence/owner-order.md"}
            },
            "roles": {"author": "Codex setup", "proposer": "Codex setup",
                      "verifier": "GitHub Actions setup verification",
                      "admitter": "Terrynce White", "executor": "Codex setup"}
        }
        admission = {"decision": "admit", "by": "Terrynce White",
                     "at": authorized_at, "evidence": "pilot/08-intervals/evidence/owner-order.md — explicit START setup admission mandate"}
        first = append(log, None, {key: {"to": value} for key, value in state.items()}, admission)
        assert first["transition"]["validation"]["result"] == "accept"
        # Implementation progress happens only after admitted genesis exists.
        implementation.write_text(PARTIAL, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s",
             str(TASK / "tests"), "-v"], text=True, capture_output=True,
            env=__import__("os").environ | {"INTERVALS_MODULE": str(implementation),
                                          "PYTHONDONTWRITEBYTECODE": "1"})
        output = result.stderr.replace(str(TASK), "pilot/08-intervals")
        import re
        output = re.sub(r"Ran 8 tests in [0-9.]+s", "Ran 8 tests (elapsed time omitted)", output)
        assert result.returncode == 1 and "FAILED (failures=3)" in output
        progress_at = stamp()
        assert authorized_at < progress_at
        delta = {
            "current_state": {"from": "A_AUTHORIZED", "to": "A_PARTIAL"},
            "verified_facts": {"add": [
                {"fact": "Partial A validates inputs, rejects booleans/reversed ranges, filters empty intervals, copies caller data, and sorts; merging is unfinished.",
                 "evidence": "pilot/08-intervals/intervals.py"},
                {"fact": "Five of eight frozen behavior tests pass; overlapping_chain, touching_chain, and nesting_and_duplicates fail.",
                 "evidence": "pilot/08-intervals/evidence/midtask-tests.txt"}
            ]},
            "identifiers.shas": {"add": {
                "partial_implementation": digest(PARTIAL.encode("utf-8")),
                "midtask_tests": digest(output.encode("utf-8"))
            }},
            "identifiers.dates": {"add": {"partial_admitted_at": progress_at}}
        }
        second = append(log, first["state"], delta,
                        admission | {"at": progress_at})
        assert second["transition"]["validation"]["result"] == "accept"
        assert replay(log) == second
        accepted = second["state"]
        emit("pilot/08-intervals/intervals.py", PARTIAL)
        emit("pilot/08-intervals/evidence/midtask-tests.txt", output)
        emit("pilot/08-intervals/handoff-state.json", json.dumps(accepted, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
        emit("pilot/08-intervals/handoff-transition.jsonl", log.read_text(encoding="utf-8"))
        emit("pilot/08-intervals/HANDOFF.md", render(accepted))
        emit("pilot/08-intervals/evidence/accepted-head.json",
             json.dumps({"accepted_seq": 2, "accepted_state_hash": state_hash(accepted),
                         "accepted_log_sha256": digest(log.read_bytes()),
                         "authorized_at": authorized_at,
                         "partial_admitted_at": progress_at}, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
