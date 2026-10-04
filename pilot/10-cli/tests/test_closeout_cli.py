"""Acceptance tests for the REAL-HANDOFF-10 closeout CLI (frozen with SPEC.md).

The CLI wraps the canonical verify_closeout(); these tests invoke the real
command as a subprocess. Positive cases use the real REAL-HANDOFF-08
fixture refs. Mutation negatives use an ephemeral git repo seeded from the
real fixture trees (no fabricated authority: the records are the real
admitted ones).
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

FROZEN = "c45b3c611ecb496d6facc62643f0d685fe039f2a"
CLOSEOUT = "bd58f07fdad7076783f3dffaa28ca1fa1b4060a0"
TASK = "pilot/08-intervals"
OWNER = "Terrynce White"

ALLOW = [
    "--allow-implementation-changed", f"{TASK}/intervals.py",
    "--allow-evidence-added", f"{TASK}/evidence/execution/canonical-python-preflight.txt",
    "--allow-evidence-added", f"{TASK}/evidence/execution/closeout-ci-record.md",
]
BASE = ["--frozen-ref", FROZEN, "--candidate-ref", CLOSEOUT,
        "--task-dir", TASK, "--owner", OWNER]


def run_cli(args, cwd):
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    return subprocess.run(
        [sys.executable, "-m", "handoff", "verify-closeout", *args],
        cwd=cwd, capture_output=True, text=True, env=env)


class RealFixtureTest(unittest.TestCase):
    """Positive path and allowlist mechanics against the real 08 fixture."""

    def test_legitimate_closeout_passes_exit_0(self):
        proc = run_cli(BASE + ALLOW, cwd=ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertTrue(report["passed"])
        self.assertEqual(report["failures"], [])

    def test_output_is_machine_readable_json(self):
        proc = run_cli(BASE + ALLOW, cwd=ROOT)
        report = json.loads(proc.stdout)
        for key in ("passed", "failures", "checks_run", "file_checks",
                    "frozen_ref", "candidate_ref", "task_dir", "authority_owner"):
            self.assertIn(key, report)
        self.assertEqual(report["frozen_ref"], FROZEN)
        self.assertEqual(report["candidate_ref"], CLOSEOUT)
        self.assertEqual(report["task_dir"], TASK)
        self.assertEqual(report["authority_owner"], OWNER)

    def test_evidence_allowance_is_required(self):
        args = BASE + ["--allow-implementation-changed", f"{TASK}/intervals.py"]
        proc = run_cli(args, cwd=ROOT)
        self.assertEqual(proc.returncode, 1)
        report = json.loads(proc.stdout)
        self.assertFalse(report["passed"])
        self.assertTrue(any("unlisted new file" in f["detail"]
                            for f in report["failures"]), report["failures"])

    def test_implementation_allowance_is_required(self):
        args = BASE + [
            "--allow-evidence-added",
            f"{TASK}/evidence/execution/canonical-python-preflight.txt",
            "--allow-evidence-added",
            f"{TASK}/evidence/execution/closeout-ci-record.md",
        ]
        proc = run_cli(args, cwd=ROOT)
        self.assertEqual(proc.returncode, 1)
        report = json.loads(proc.stdout)
        self.assertFalse(report["passed"])
        self.assertTrue(any("protected bytes changed" in f["detail"]
                            for f in report["failures"]), report["failures"])

    def test_wrong_owner_rejected(self):
        args = ["--frozen-ref", FROZEN, "--candidate-ref", CLOSEOUT,
                "--task-dir", TASK, "--owner", "Someone Else"] + ALLOW
        proc = run_cli(args, cwd=ROOT)
        self.assertNotEqual(proc.returncode, 0)
        report = json.loads(proc.stdout)
        self.assertFalse(report["passed"])

    def test_nonexistent_ref_rejected_cleanly(self):
        args = ["--frozen-ref", "deadbeef" * 5, "--candidate-ref", CLOSEOUT,
                "--task-dir", TASK, "--owner", OWNER] + ALLOW
        proc = run_cli(args, cwd=ROOT)
        self.assertEqual(proc.returncode, 2)

    def test_malformed_allowlist_rejected_cleanly(self):
        args = BASE + ["--allow-evidence-added", "../evil.txt"]
        proc = run_cli(args, cwd=ROOT)
        self.assertEqual(proc.returncode, 2)

    def test_missing_required_argument_rejected(self):
        args = ["--frozen-ref", FROZEN, "--candidate-ref", CLOSEOUT,
                "--task-dir", TASK] + ALLOW  # no --owner
        proc = run_cli(args, cwd=ROOT)
        self.assertEqual(proc.returncode, 2)


class TempRepoFixture(unittest.TestCase):
    """Mutation negatives in an ephemeral repo seeded from real fixture trees."""

    @classmethod
    def setUpClass(cls):
        cls.workdir = Path(tempfile.mkdtemp(prefix="handoff10-"))
        cls._git("init", "-q")
        cls._git("config", "user.email", "test@local")
        cls._git("config", "user.name", "Test")
        cls._extract(FROZEN, "frozen start")
        cls.ref_frozen = cls._git("rev-parse", "HEAD").strip()
        cls._extract(CLOSEOUT, "legitimate closeout")
        cls.ref_closeout = cls._git("rev-parse", "HEAD").strip()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.workdir, ignore_errors=True)

    @classmethod
    def _git(cls, *args):
        result = subprocess.run(["git", *args], cwd=cls.workdir,
                                capture_output=True, text=True)
        assert result.returncode == 0, args
        return result.stdout

    @classmethod
    def _extract(cls, sha, message):
        archive = subprocess.run(
            ["git", "-C", str(ROOT), "archive", sha, "--", TASK + "/"],
            capture_output=True)
        assert archive.returncode == 0
        tar = subprocess.run(["tar", "-x", "-C", str(cls.workdir)],
                             input=archive.stdout, capture_output=True)
        assert tar.returncode == 0
        cls._git("add", "-A")
        cls._git("commit", "-qm", message)

    def _base(self, candidate):
        return ["--frozen-ref", self.ref_frozen, "--candidate-ref", candidate,
                "--task-dir", TASK, "--owner", OWNER] + ALLOW

    def test_seeded_legitimate_closeout_passes(self):
        proc = run_cli(self._base(self.ref_closeout), cwd=self.workdir)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(json.loads(proc.stdout)["passed"])

    def test_protected_file_mutation_rejected(self):
        target = self.workdir / TASK / "SPEC.md"
        target.write_text(target.read_text() + "\nmutated\n", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "protected mutation")
        ref = self._git("rev-parse", "HEAD").strip()
        proc = run_cli(self._base(ref), cwd=self.workdir)
        self.assertEqual(proc.returncode, 1)
        report = json.loads(proc.stdout)
        self.assertFalse(report["passed"])
        self.assertTrue(any("protected bytes changed" in f["detail"]
                            for f in report["failures"]), report["failures"])

    def test_unlisted_new_file_rejected(self):
        sneaky = self.workdir / TASK / "evidence" / "execution" / "sneaky.txt"
        sneaky.write_text("unlisted", encoding="utf-8")
        self._git("add", "-A")
        self._git("commit", "-qm", "unlisted file")
        ref = self._git("rev-parse", "HEAD").strip()
        proc = run_cli(self._base(ref), cwd=self.workdir)
        self.assertEqual(proc.returncode, 1)
        report = json.loads(proc.stdout)
        self.assertFalse(report["passed"])
        self.assertTrue(any("unlisted new file" in f["detail"]
                            for f in report["failures"]), report["failures"])


if __name__ == "__main__":
    unittest.main()
