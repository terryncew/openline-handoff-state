"""Repository-wide historical replay compatibility audit.

Proves evaluator 0.1.1 changes only the newly authorized claim-evolution
lane: every committed handoff-transition.jsonl replays byte-semantically
identically under the repaired evaluator (same disposition, check names/
values, resulting hash, rendered prose, accepted state at each step).

Runs in CI on every PR touching the repo. Uses git to enumerate committed
logs; skips if git is unavailable.
"""
import json
import subprocess
import unittest
from pathlib import Path

from handoff.canonical import loads, state_hash
from handoff.core import apply_delta, evaluate, same, verify_record

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    if result.returncode != 0:
        raise unittest.SkipTest("git unavailable for replay audit")
    return result.stdout


class ReplayCompatibilityTest(unittest.TestCase):
    def test_all_historical_records_replay_identically(self):
        logs = sorted(
            p for p in git("ls-tree", "-r", "--name-only", "HEAD").decode().split()
            if p.endswith("handoff-transition.jsonl"))
        self.assertGreater(len(logs), 0, "no transition logs found")
        counts = {"records": 0, "accept": 0, "reject": 0, "quarantine": 0}
        for log_path in logs:
            with self.subTest(log=log_path):
                text = git("show", f"HEAD:{log_path}").decode()
                records = [loads(l) for l in text.splitlines() if l.strip()]
                self.assertGreater(len(records), 0)
                state = None
                for rec in records:
                    counts["records"] += 1
                    counts[rec["validation"]["result"]] += 1
                    errors = verify_record(state, rec)
                    self.assertEqual(errors, [],
                                     f"{log_path} seq {rec['seq']}: {errors}")
                    reported_conflict = any(
                        item == {"check": "semantic conflict", "pass": False}
                        for item in rec["validation"]["checks"])
                    out = evaluate(state, rec["proposed_delta"], rec["admission"],
                                   seq=rec["seq"], semantic_conflict=reported_conflict)
                    t = out["transition"]
                    for field in ("schema", "task_id", "seq", "prior_state_hash",
                                  "proposed_delta", "admission",
                                  "resulting_state_hash", "rendered_prose"):
                        self.assertTrue(same(t[field], rec[field]),
                                        f"{log_path} seq {rec['seq']}: field {field} differs")
                    self.assertEqual(
                        [(c["check"], c["pass"]) for c in t["validation"]["checks"]],
                        [(c["check"], c["pass"]) for c in rec["validation"]["checks"]],
                        f"{log_path} seq {rec['seq']}: checks differ")
                    self.assertEqual(t["validation"]["result"],
                                     rec["validation"]["result"])
                    state = out["state"]
        # Sanity: the audit actually saw history (not an empty pass).
        self.assertGreater(counts["records"], 0)
        self.assertGreater(counts["accept"], 0)

    def test_post_genesis_claim_deltas_are_lane_authorized(self):
        """v0.1.1 added the explicit claim-evolution lane; REAL-HANDOFF-09
        seq 2 is its first legitimate use. Every committed post-genesis
        claim delta must be lane-authorized: the record is accepted, and
        the admission names the prior state's authority owner exactly.
        (The replay test above already proves identical re-evaluation,
        and the lane accepts only complete exact-owner admissions with
        evidence-backed extensions.) An unadmitted or non-accept claim
        mutation in history would indicate smuggling or reinterpretation.
        """
        logs = [p for p in git("ls-tree", "-r", "--name-only", "HEAD").decode().split()
                if p.endswith("handoff-transition.jsonl")]
        for log_path in logs:
            with self.subTest(log=log_path):
                text = git("show", f"HEAD:{log_path}").decode()
                records = [loads(l) for l in text.splitlines() if l.strip()]
                state = None
                for rec in records:
                    if rec["seq"] > 1 and "claims" in rec["proposed_delta"]:
                        self.assertEqual(
                            rec["validation"]["result"], "accept",
                            f"{log_path} seq {rec['seq']}: claim delta is not an accepted record")
                        self.assertEqual(
                            rec["admission"].get("by"), state["authority_owner"],
                            f"{log_path} seq {rec['seq']}: claim delta admission "
                            f"is not by the exact authority owner")
                    reported_conflict = any(
                        item == {"check": "semantic conflict", "pass": False}
                        for item in rec["validation"]["checks"])
                    out = evaluate(state, rec["proposed_delta"], rec["admission"],
                                   seq=rec["seq"], semantic_conflict=reported_conflict)
                    state = out["state"]


if __name__ == "__main__":
    unittest.main()
