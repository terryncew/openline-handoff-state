"""Focused tests for QUESTION-LIFECYCLE-001 (evaluator v0.1.2).

The question-resolution lane: an accepted open question may be removed
from open_questions only via an explicit from/to compare-and-replace with
complete exact-owner admission, exact prior ownership of every removed
question, and at least one new evidenced verified fact. Unchanged and
append-only questions keep existing behavior.
"""
import copy
import unittest

from handoff.canonical import state_hash
from handoff.core import evaluate, verify_record

OWNER = "Terrynce White"

Q1 = {"question": "First open question.", "owner": OWNER}
Q2 = {"question": "Second open question.", "owner": OWNER}
Q_OTHER = {"question": "Owned by someone else.", "owner": "Someone Else"}


def make_state(questions=(Q1, Q2), facts=()):
    return {
        "schema": "openline.handoff-state.v0.1",
        "task_id": "question-lifecycle-test",
        "goal": "test the question-resolution lane",
        "authority_owner": OWNER,
        "current_state": "MID_TASK",
        "frozen_invariants": ["do not change"],
        "verified_facts": [
            {"fact": f"fact {i}", "evidence": f"evidence {i}"} for i in range(facts)
        ] if isinstance(facts, int) else list(facts),
        "claims": [{"claim": "c", "basis": "b", "ceiling": "e"}],
        "open_questions": [copy.deepcopy(q) for q in questions],
        "failed_or_superseded_paths": [],
        "canonical_terms": {},
        "proposed_state_changes": [],
        "next_permitted_actions": ["act"],
        "stop_conditions": ["stop"],
        "identifiers": {"shas": {}, "paths": {}, "versions": {},
                       "dates": {}, "receipts": {}},
        "roles": {"admitter": OWNER, "author": "Muse", "executor": "Muse",
                  "proposer": OWNER, "verifier": "Muse"},
    }


def owner_admission(by=OWNER):
    return {"decision": "admit", "by": by, "at": "2026-10-04T00:00:00+00:00",
            "evidence": "test admission"}


def run(prior, delta, admission):
    out = evaluate(copy.deepcopy(prior), delta, admission, seq=2)
    t = out["transition"]
    return (t["validation"]["result"],
            [c["check"] for c in t["validation"]["checks"] if not c["pass"]],
            t["resulting_state_hash"] != state_hash(prior),
            out)


def remove_delta(prior, new_questions):
    return {"open_questions": {"from": copy.deepcopy(prior["open_questions"]),
                               "to": copy.deepcopy(new_questions)}}


class QuestionLifecycleTest(unittest.TestCase):
    def test_unchanged_questions_accept(self):
        prior = make_state()
        delta = {"current_state": {"from": "MID_TASK", "to": "MID_TASK2"}}
        disp, failing, advanced, _ = run(prior, delta, owner_admission())
        self.assertEqual(disp, "accept", failing)
        self.assertTrue(advanced)

    def test_append_only_questions_accept(self):
        prior = make_state()
        delta = {"open_questions": {"add": [copy.deepcopy(Q_OTHER)]}}
        disp, failing, advanced, _ = run(prior, delta, owner_admission())
        self.assertEqual(disp, "accept", failing)
        self.assertTrue(advanced)

    def test_remove_with_empty_admission_rejects(self):
        prior = make_state()
        disp, failing, advanced, _ = run(
            prior, remove_delta(prior, [Q2]), {})
        self.assertEqual(disp, "reject")
        self.assertIn("accepted evidence and questions preserved", failing)
        self.assertFalse(advanced)

    def test_remove_with_wrong_owner_rejects(self):
        prior = make_state()
        delta = remove_delta(prior, [Q2])
        delta["verified_facts"] = {
            "add": [{"fact": "resolved", "evidence": "e"}]}
        disp, failing, advanced, _ = run(
            prior, delta, owner_admission(by="Someone Else"))
        self.assertEqual(disp, "reject")
        self.assertFalse(advanced)

    def test_exact_owner_removal_with_evidence_accepts(self):
        prior = make_state()
        delta = remove_delta(prior, [Q2])
        delta["verified_facts"] = {
            "add": [{"fact": "Q1 resolved: done.", "evidence": "run log"}]}
        disp, failing, advanced, out = run(prior, delta, owner_admission())
        self.assertEqual(disp, "accept", failing)
        self.assertTrue(advanced)
        self.assertEqual(out["state"]["open_questions"], [Q2])

    def test_old_question_recoverable_from_prior(self):
        prior = make_state()
        self.assertIn(Q1, prior["open_questions"])
        # The prior accepted record itself is the immutable history.
        self.assertEqual(prior["open_questions"][0]["owner"], OWNER)

    def test_removal_without_added_evidence_rejects(self):
        prior = make_state()
        disp, failing, advanced, _ = run(
            prior, remove_delta(prior, [Q2]), owner_admission())
        self.assertEqual(disp, "reject")
        self.assertIn("accepted evidence and questions preserved", failing)
        self.assertFalse(advanced)

    def test_mutation_of_question_text_rejects(self):
        prior = make_state()
        mutated = {"question": "First open question (edited).", "owner": OWNER}
        disp, failing, advanced, _ = run(
            prior, remove_delta(prior, [mutated, Q2]),
            owner_admission())
        # from/to must still carry the exact prior list; the candidate
        # then differs from "to" -> delta invalid or question check fails.
        self.assertEqual(disp, "reject")
        self.assertFalse(advanced)

    def test_mutation_of_question_owner_rejects(self):
        prior = make_state()
        mutated = {"question": "Second open question.", "owner": "Someone Else"}
        disp, failing, advanced, _ = run(
            prior, remove_delta(prior, [Q1, mutated]), owner_admission())
        self.assertEqual(disp, "reject")
        self.assertFalse(advanced)

    def test_reorder_of_remaining_questions_rejects(self):
        prior = make_state(questions=(Q1, Q2, Q_OTHER))
        # Remove Q_OTHER but swap Q1/Q2 order.
        disp, failing, advanced, _ = run(
            prior, remove_delta(prior, [Q2, Q1]), owner_admission())
        self.assertEqual(disp, "reject")
        self.assertFalse(advanced)

    def test_remove_plus_silent_add_rejects(self):
        prior = make_state()
        smuggled = {"question": "Brand new question.", "owner": OWNER}
        delta = remove_delta(prior, [Q2, smuggled])
        delta["verified_facts"] = {
            "add": [{"fact": "resolved", "evidence": "e"}]}
        disp, failing, advanced, _ = run(prior, delta, owner_admission())
        self.assertEqual(disp, "reject")
        self.assertFalse(advanced)

    def test_delete_all_questions_with_valid_resolution_accepts(self):
        prior = make_state()
        delta = remove_delta(prior, [])
        delta["verified_facts"] = {
            "add": [{"fact": "all questions resolved", "evidence": "e"}]}
        disp, failing, advanced, out = run(prior, delta, owner_admission())
        self.assertEqual(disp, "accept", failing)
        self.assertTrue(advanced)
        self.assertEqual(out["state"]["open_questions"], [])

    def test_removal_of_other_owned_question_rejects(self):
        prior = make_state(questions=(Q1, Q_OTHER))
        delta = remove_delta(prior, [Q1])
        delta["verified_facts"] = {
            "add": [{"fact": "resolved", "evidence": "e"}]}
        disp, failing, advanced, _ = run(prior, delta, owner_admission())
        self.assertEqual(disp, "reject")
        self.assertFalse(advanced)

    def test_replay_and_verify_record_deterministic(self):
        prior = make_state()
        delta = remove_delta(prior, [Q2])
        delta["verified_facts"] = {
            "add": [{"fact": "Q1 resolved: done.", "evidence": "run log"}]}
        _, _, _, out1 = run(prior, delta, owner_admission())
        _, _, _, out2 = run(prior, delta, owner_admission())
        self.assertEqual(out1["transition"], out2["transition"])
        self.assertEqual(verify_record(prior, out1["transition"]), [])


if __name__ == "__main__":
    unittest.main()
