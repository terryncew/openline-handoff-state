"""Acceptance tests for the phase-aware closeout verifier (REAL-HANDOFF-09).

Frozen with pilot/09-closeout-verifier/SPEC.md — do not modify to pass.

Real fixture: REAL-HANDOFF-08. Frozen start c45b3c6 (2 accepted records,
A_PARTIAL) and legitimate admitted closeout bd58f07 (seq 3 appended,
A_COMPLETE_PENDING_OWNER_ADMISSION). The verifier must pass that pair
and must fail tampered or unauthorized variants.

Helper builds candidate variants by mutating COPIES of the real closeout.
"""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from handoff.canonical import canonical_json, loads
from handoff.closeout import Allowlist, verify_closeout

FROZEN = "c45b3c611ecb496d6facc62643f0d685fe039f2a"
CLOSEOUT = "bd58f07fdad7076783f3dffaa28ca1fa1b4060a0"
TASK = "pilot/08-intervals"
OWNER = "Terrynce White"

ALLOWLIST = Allowlist(
    implementation_changed=[f"{TASK}/intervals.py"],
    evidence_added=[
        f"{TASK}/evidence/execution/canonical-python-preflight.txt",
        f"{TASK}/evidence/execution/closeout-ci-record.md",
    ],
)


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    assert result.returncode == 0, args
    return result.stdout


def load_tree(sha):
    names = git("ls-tree", "-r", "--name-only", sha, "--", TASK + "/").decode().split()
    return {name: git("show", f"{sha}:{name}") for name in names}


class Fixture:
    @classmethod
    def setUpClass(cls):
        cls.frozen_log = git("show", f"{FROZEN}:{TASK}/handoff-transition.jsonl").decode()
        cls.closeout_log = git("show", f"{CLOSEOUT}:{TASK}/handoff-transition.jsonl").decode()
        cls.frozen_state = json.loads(git("show", f"{FROZEN}:{TASK}/handoff-state.json").decode())
        cls.closeout_state = json.loads(git("show", f"{CLOSEOUT}:{TASK}/handoff-state.json").decode())
        cls.frozen_files = load_tree(FROZEN)
        cls.closeout_files = load_tree(CLOSEOUT)

    def base_kwargs(self):
        return dict(
            frozen_log_text=self.frozen_log,
            candidate_log_text=self.closeout_log,
            frozen_head_state=copy.deepcopy(self.frozen_state),
            candidate_state=copy.deepcopy(self.closeout_state),
            frozen_files=dict(self.frozen_files),
            candidate_files=dict(self.closeout_files),
            allowlist=copy.deepcopy(ALLOWLIST),
            authority_owner=OWNER,
            task_dir=TASK,
        )

    def mutate_log(self, index, transform):
        lines = self.closeout_log.strip().splitlines()
        record = loads(lines[index])
        transform(record)
        lines[index] = canonical_json(record)
        return "\n".join(lines) + "\n"


class CloseoutVerifierTest(Fixture, unittest.TestCase):
    def test_legitimate_08_closeout_passes(self):
        result = verify_closeout(**self.base_kwargs())
        self.assertTrue(result.passed, [f.detail for f in result.failures])

    def test_rewritten_historical_record_fails(self):
        log = self.mutate_log(0, lambda r: r.update(
            {"rendered_prose": r["rendered_prose"] + " tampered"}))
        kwargs = self.base_kwargs()
        kwargs["candidate_log_text"] = log
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_deleted_historical_record_fails(self):
        lines = self.closeout_log.strip().splitlines()
        kwargs = self.base_kwargs()
        kwargs["candidate_log_text"] = "\n".join(lines[1:]) + "\n"
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_wrong_prior_hash_fails(self):
        log = self.mutate_log(2, lambda r: r.update(
            {"prior_state_hash": "sha256:" + "0" * 64}))
        kwargs = self.base_kwargs()
        kwargs["candidate_log_text"] = log
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_skipped_sequence_fails(self):
        log = self.mutate_log(2, lambda r: r.update({"seq": 5}))
        kwargs = self.base_kwargs()
        kwargs["candidate_log_text"] = log
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_missing_admission_fails(self):
        log = self.mutate_log(2, lambda r: r.update({"admission": {}}))
        kwargs = self.base_kwargs()
        kwargs["candidate_log_text"] = log
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_unadmitted_proposal_as_accepted_fails(self):
        def flip(record):
            record["validation"] = dict(record["validation"], result="reject")
        log = self.mutate_log(2, flip)
        kwargs = self.base_kwargs()
        kwargs["candidate_log_text"] = log
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_unexpected_protected_file_change_fails(self):
        kwargs = self.base_kwargs()
        spec = f"{TASK}/SPEC.md"
        kwargs["candidate_files"][spec] = kwargs["candidate_files"][spec] + b"\n# tampered\n"
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_final_state_hash_mismatch_fails(self):
        kwargs = self.base_kwargs()
        kwargs["candidate_state"] = copy.deepcopy(self.closeout_state)
        kwargs["candidate_state"]["verified_facts"].append(
            {"fact": "injected", "evidence": "none"})
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)

    def test_allowed_evidence_addition_passes(self):
        kwargs = self.base_kwargs()
        extra = f"{TASK}/evidence/execution/extra-note.md"
        kwargs["candidate_files"][extra] = b"closeout note\n"
        kwargs["allowlist"].evidence_added.append(extra)
        result = verify_closeout(**kwargs)
        self.assertTrue(result.passed, [f.detail for f in result.failures])

    def test_unlisted_new_file_fails(self):
        kwargs = self.base_kwargs()
        kwargs["candidate_files"][f"{TASK}/evidence/execution/sneaky.md"] = b"sneaky\n"
        result = verify_closeout(**kwargs)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
