"""Focused tests for the CLAIM-EVOLUTION-001 claim-transition lane.

The lane replaces the frozen-claim invariant with an explicit rule:
unchanged claims keep existing behavior; a changed claim is accepted only
with an explicit from/to compare-and-replace, well-formed replacement,
complete exact-owner admission, and strictly extended verified_facts
whose new entries carry nonblank evidence.
"""
import copy
import unittest

from handoff.canonical import state_hash
from handoff.core import evaluate, verify_record, EVALUATOR_VERSION


OLD_CLAIM = {
    "claim": "old bounded claim",
    "basis": "old basis",
    "ceiling": "old ceiling",
}
NEW_CLAIM = {
    "claim": "new bounded claim",
    "basis": "new basis with evidence",
    "ceiling": "new ceiling",
}


def make_state(**overrides):
    state = {
        "schema": "openline.handoff-state.v0.1",
        "task_id": "TEST-CLAIM-EVOLUTION",
        "goal": "Test the claim-evolution lane.",
        "authority_owner": "Terrynce White",
        "current_state": "MID_TASK",
        "frozen_invariants": ["frozen"],
        "verified_facts": [{"fact": "f1", "evidence": "e1"}],
        "claims": [copy.deepcopy(OLD_CLAIM)],
        "open_questions": [],
        "failed_or_superseded_paths": [],
        "canonical_terms": {},
        "proposed_state_changes": [],
        "next_permitted_actions": ["act"],
        "stop_conditions": ["stop"],
        "identifiers": {"shas": {}, "paths": {}, "versions": {},
                        "dates": {}, "receipts": {}},
        "roles": {"author": "t", "proposer": "Terrynce White",
                  "verifier": "t", "admitter": "Terrynce White",
                  "executor": "t"},
    }
    state.update(overrides)
    return state


def admit(by="Terrynce White"):
    return {"decision": "admit", "by": by,
            "at": "2026-10-04T05:00:00+00:00", "evidence": "test admission"}


def claim_delta(prior, new_claims, op="from_to"):
    if op == "from_to":
        return {"claims": {"from": copy.deepcopy(prior["claims"]),
                           "to": copy.deepcopy(new_claims)}}
    return {"claims": {"replace": copy.deepcopy(new_claims)}}


def check_result(transition, name):
    return next(c["pass"] for c in transition["validation"]["checks"]
                if c["check"] == name)


class ClaimEvolutionTest(unittest.TestCase):
    def test_evaluator_version(self):
        self.assertEqual(EVALUATOR_VERSION, "0.1.2")

    def test_unchanged_claims_existing_behavior(self):
        prior = make_state()
        delta = {"current_state": {"from": "MID_TASK", "to": "MID_TASK_2"}}
        out = evaluate(prior, delta, admit(), seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "accept")
        self.assertTrue(check_result(out["transition"], "claim exceeds cited experiment"))
        self.assertEqual(out["state"]["claims"], [OLD_CLAIM])

    def test_unadmitted_claim_replacement_no_advance(self):
        prior = make_state()
        delta = claim_delta(prior, [NEW_CLAIM])
        out = evaluate(prior, delta, {}, seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "reject")
        self.assertEqual(out["state"], prior)
        self.assertEqual(state_hash(out["state"]), state_hash(prior))

    def test_wrong_owner_claim_replacement_no_advance(self):
        prior = make_state()
        delta = claim_delta(prior, [NEW_CLAIM])
        out = evaluate(prior, delta, admit(by="Someone Else"), seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "reject")
        self.assertEqual(out["state"], prior)

    def test_exact_owner_supported_bounded_replacement_accept(self):
        prior = make_state()
        new_facts = prior["verified_facts"] + [
            {"fact": "f2", "evidence": "e2 supporting the replacement"}]
        delta = {
            "current_state": {"from": "MID_TASK", "to": "MID_TASK_DONE"},
            "verified_facts": {"from": copy.deepcopy(prior["verified_facts"]),
                               "to": new_facts},
        }
        delta.update(claim_delta(prior, [NEW_CLAIM]))
        out = evaluate(prior, delta, admit(), seq=2)
        t = out["transition"]
        self.assertEqual(t["validation"]["result"], "accept")
        self.assertTrue(check_result(t, "claim exceeds cited experiment"))
        self.assertEqual(out["state"]["claims"], [NEW_CLAIM])
        self.assertEqual(t["resulting_state_hash"], state_hash(out["state"]))

    def test_old_claim_recoverable_in_prior_record(self):
        prior = make_state()
        new_facts = prior["verified_facts"] + [{"fact": "f2", "evidence": "e2"}]
        delta = {"verified_facts": {"from": copy.deepcopy(prior["verified_facts"]),
                                    "to": new_facts}}
        delta.update(claim_delta(prior, [NEW_CLAIM]))
        out = evaluate(prior, delta, admit(), seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "accept")
        # History is immutable: the prior state still carries the old claim.
        self.assertEqual(prior["claims"], [OLD_CLAIM])
        self.assertNotEqual(out["state"]["claims"], prior["claims"])

    def test_replacement_without_evidence_no_advance(self):
        prior = make_state()
        delta = claim_delta(prior, [NEW_CLAIM])
        out = evaluate(prior, delta, admit(), seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "quarantine")
        self.assertFalse(check_result(out["transition"], "claim exceeds cited experiment"))
        self.assertEqual(out["state"], prior)

    def test_malformed_claim_no_advance(self):
        prior = make_state()
        bad = dict(NEW_CLAIM, ceiling="  ")
        new_facts = prior["verified_facts"] + [{"fact": "f2", "evidence": "e2"}]
        delta = {"verified_facts": {"from": copy.deepcopy(prior["verified_facts"]),
                                    "to": new_facts}}
        delta.update(claim_delta(prior, [bad]))
        out = evaluate(prior, delta, admit(), seq=2)
        # Blank ceiling fails schema validation -> reject; either way, no advance.
        self.assertIn(out["transition"]["validation"]["result"], {"reject", "quarantine"})
        self.assertEqual(out["state"], prior)

    def test_claim_deletion_no_advance(self):
        prior = make_state()
        new_facts = prior["verified_facts"] + [{"fact": "f2", "evidence": "e2"}]
        delta = {"verified_facts": {"from": copy.deepcopy(prior["verified_facts"]),
                                    "to": new_facts}}
        delta.update(claim_delta(prior, []))
        out = evaluate(prior, delta, admit(), seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "quarantine")
        self.assertEqual(out["state"], prior)

    def test_smuggled_claim_change_no_advance(self):
        prior = make_state()
        new_facts = prior["verified_facts"] + [{"fact": "f2", "evidence": "e2"}]
        delta = {
            "current_state": {"from": "MID_TASK", "to": "MID_TASK_DONE"},
            "verified_facts": {"from": copy.deepcopy(prior["verified_facts"]),
                               "to": new_facts},
        }
        # "replace" without from/to is not an explicit compare-and-replace.
        delta.update(claim_delta(prior, [NEW_CLAIM], op="replace"))
        out = evaluate(prior, delta, admit(), seq=2)
        self.assertEqual(out["transition"]["validation"]["result"], "quarantine")
        self.assertEqual(out["state"], prior)

    def test_replay_deterministic(self):
        prior = make_state()
        new_facts = prior["verified_facts"] + [{"fact": "f2", "evidence": "e2"}]
        delta = {"verified_facts": {"from": copy.deepcopy(prior["verified_facts"]),
                                    "to": new_facts}}
        delta.update(claim_delta(prior, [NEW_CLAIM]))
        first = evaluate(prior, delta, admit(), seq=2)
        second = evaluate(prior, delta, admit(), seq=2)
        self.assertEqual(first["transition"]["resulting_state_hash"],
                         second["transition"]["resulting_state_hash"])
        self.assertEqual(verify_record(prior, first["transition"]), [])
        self.assertEqual(verify_record(prior, second["transition"]), [])


if __name__ == "__main__":
    unittest.main()
