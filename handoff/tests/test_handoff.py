"""Stage 1 invariants only; no real handoff or provider pilot is simulated."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import threading
import unittest

from handoff.canonical import canonical_json, loads
from handoff.core import evaluate, apply_delta, verify_record, RECORD_FIELDS
from handoff.render import render, parse_rendered
from handoff.schema import validate_state
from handoff.store import append, replay

ROOT = Path(__file__).resolve().parents[2]


def independent_hash(state):
    raw = json.dumps(state, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.fixture = loads((ROOT / "test-fixture-valid.json").read_text(encoding="utf-8"))
        self.state = deepcopy(self.fixture["resulting_state"])
        self.admission = {"decision": "admit", "by": "Terrynce White",
                          "at": "2026-10-03T22:00:00Z", "evidence": "owner-order.txt"}

    def fact_delta(self, fact="Bounded check completed."):
        return {"verified_facts": {"add": [{"fact": fact, "evidence": "result.txt"}]}}

    def genesis(self):
        return {key: {"to": deepcopy(value)} for key, value in self.state.items()}

    def assert_unchanged(self, receipt, prior=None, result="reject"):
        prior = self.state if prior is None else prior
        self.assertEqual(receipt["transition"]["validation"]["result"], result)
        self.assertEqual(receipt["state"], prior)
        self.assertEqual(receipt["transition"]["resulting_state_hash"],
                         independent_hash(prior))
        self.assertEqual(parse_rendered(receipt["transition"]["rendered_prose"]), prior)

    def assert_failed(self, receipt, name):
        checks = {item["check"]: item["pass"]
                  for item in receipt["transition"]["validation"]["checks"]}
        self.assertIn(name, checks)
        self.assertIs(checks[name], False)

    def test_frozen_schema_unchanged(self):
        actual = hashlib.sha256((ROOT / "HANDOFF_STATE_SCHEMA_v0.1.md").read_bytes()).hexdigest()
        self.assertEqual(actual, "246d2332a9fd2ee88ca52867b70e525205a3627f9bb5aa2f369913ab64968d95")

    def test_valid_fixture_delta_is_accepted_with_real_hashes(self):
        source = self.fixture["transition"]
        prior = self.fixture["prior_state"]
        self.assertEqual(validate_state(prior), [])
        candidate = apply_delta(prior, source["proposed_delta"])
        self.assertEqual(candidate, self.fixture["resulting_state"])
        self.assertEqual(source["prior_state_hash"], independent_hash(prior))
        self.assertEqual(source["resulting_state_hash"], independent_hash(candidate))
        receipt = evaluate(prior, source["proposed_delta"], source["admission"], seq=5)
        self.assertEqual(receipt["transition"]["validation"]["result"], "accept")
        self.assertEqual(receipt["state"], candidate)
        self.assertEqual(receipt["transition"]["resulting_state_hash"], source["resulting_state_hash"])
        self.assertEqual(verify_record(prior, receipt["transition"]), [])

    def test_open_to_fact_without_evidence_rejected(self):
        prior = deepcopy(self.state)
        prior["current_state"] = "OPEN"
        receipt = evaluate(prior, {"current_state": {"from": "OPEN", "to": "FACT"}}, self.admission)
        self.assert_unchanged(receipt, prior)
        self.assert_failed(receipt, "OPEN→FACT without evidence")

    def test_frozen_modification_rejected(self):
        changed = deepcopy(self.state["frozen_invariants"])
        changed[0] = "Executor may authorize consequential actions."
        receipt = evaluate(self.state, {"frozen_invariants": {"replace": changed}}, self.admission)
        self.assert_unchanged(receipt)
        self.assert_failed(receipt, "FROZEN invariant modified")

    def test_unauthorized_term_rename_and_definition_change_rejected(self):
        key = next(iter(self.state["canonical_terms"]))
        for rename in (True, False):
            with self.subTest(rename=rename):
                terms = deepcopy(self.state["canonical_terms"])
                if rename:
                    terms["NEW_NAME"] = terms.pop(key)
                else:
                    terms[key] = "Different meaning."
                receipt = evaluate(self.state, {"canonical_terms": {"replace": terms}}, self.admission)
                self.assert_unchanged(receipt)
                self.assert_failed(receipt, "renamed canonical concept")

    def test_new_term_without_admission_rejected_and_retained(self):
        delta = {"canonical_terms": {"add": {"BOUNDED_CHECK": "One completed check."}}}
        admission = dict(self.admission)
        del admission["by"]
        receipt = evaluate(self.state, delta, admission)
        self.assert_unchanged(receipt)
        self.assert_failed(receipt, "new canonical term without admission")
        self.assertEqual(receipt["transition"]["proposed_delta"], delta)

    def test_new_term_with_explicit_owner_admission_accepted(self):
        receipt = evaluate(self.state, {"canonical_terms": {"add": {
            "BOUNDED_CHECK": "One completed check."}}}, self.admission)
        self.assertEqual(receipt["transition"]["validation"]["result"], "accept")
        self.assertEqual(receipt["state"]["canonical_terms"]["BOUNDED_CHECK"], "One completed check.")

    def test_missing_admitter_cannot_default_to_agent(self):
        for admission in ({}, {key: value for key, value in self.admission.items() if key != "by"}):
            receipt = evaluate(self.state, self.fact_delta(), admission)
            self.assert_unchanged(receipt)
            self.assert_failed(receipt, "explicit admitter")
            self.assertEqual(receipt["transition"]["admission"], admission)
        roles = dict(self.state["roles"])
        del roles["admitter"]
        receipt = evaluate(self.state, {"roles": {"replace": roles}}, self.admission)
        self.assert_unchanged(receipt)
        self.assert_failed(receipt, "explicit admitter")

    def test_principal_matching_is_exact_and_worker_cannot_self_admit(self):
        for by in ("Muse", "Terrynce White ", "terrynce white", "Terrynce White (user)"):
            with self.subTest(by=by):
                delta = self.fact_delta()
                delta["roles"] = {"replace": dict(self.state["roles"], proposer=by, admitter=by)}
                receipt = evaluate(self.state, delta, dict(self.admission, by=by))
                self.assert_unchanged(receipt)
                self.assert_failed(receipt, "admitter matches authority_owner (exact)")

    def test_candidate_cannot_appoint_its_own_authority(self):
        delta = {"authority_owner": {"from": "Terrynce White", "to": "Codex"},
                 "roles": {"replace": dict(self.state["roles"], admitter="Codex")}}
        receipt = evaluate(self.state, delta, dict(self.admission, by="Codex"))
        self.assert_unchanged(receipt)

    def test_contradiction_quarantined_without_reconciliation(self):
        delta = self.fact_delta("NOT: " + self.state["verified_facts"][0]["fact"])
        receipt = evaluate(self.state, delta, self.admission)
        self.assert_unchanged(receipt, result="quarantine")
        self.assert_failed(receipt, "semantic conflict")
        self.assertEqual(receipt["transition"]["proposed_delta"], delta)

    def test_reported_semantic_conflict_can_only_force_quarantine(self):
        receipt = evaluate(self.state, self.fact_delta(), self.admission, semantic_conflict=True)
        self.assert_unchanged(receipt, result="quarantine")
        self.assert_failed(receipt, "semantic conflict")
        self.assertEqual(verify_record(self.state, receipt["transition"]), [])

    def test_negative_result_and_uncertainty_survive_unrelated_delta(self):
        prior = deepcopy(self.state)
        prior["current_state"] = "NEGATIVE"
        prior["verified_facts"].append({"fact": "No compatible response was observed.",
                                        "evidence": "negative-result.txt"})
        receipt = evaluate(prior, self.fact_delta(), self.admission)
        self.assertEqual(receipt["transition"]["validation"]["result"], "accept")
        recovered = parse_rendered(receipt["transition"]["rendered_prose"])
        for field in ("current_state", "failed_or_superseded_paths", "claims",
                      "open_questions", "frozen_invariants", "authority_owner"):
            self.assertEqual(recovered[field], prior[field])
        self.assertEqual(recovered["verified_facts"][:-1], prior["verified_facts"])

    def test_exact_sha_path_status_round_trip_and_determinism(self):
        state = deepcopy(self.state)
        state["identifiers"]["shas"]["exact"] = "sha256:" + "a" * 64
        state["identifiers"]["paths"]["exact"] = "a b/$literal/" + chr(96) + "literal" + chr(96) + "/µ.txt"
        state["current_state"] = "OPEN_NEGATIVE_FROZEN_SUPERSEDED"
        state["goal"] += '\nExact "µ" text.'
        prose = render(state)
        self.assertEqual(parse_rendered(prose), state)
        self.assertIn("sha256:" + "a" * 64, prose)
        self.assertEqual(render(dict(reversed(list(state.items())))), prose)
        headings = ("CURRENT STATE", "AUTHORITY", "OWNER", "FROZEN INVARIANTS",
                    "VERIFIED EVIDENCE", "OPEN QUESTIONS", "FAILED / SUPERSEDED PATHS",
                    "NEXT PERMITTED ACTION", "STOP CONDITIONS")
        positions = [prose.index("\n\n" + heading + "\n") for heading in headings]
        self.assertEqual(positions, sorted(positions))

    def test_other_named_validator_checks(self):
        claims = deepcopy(self.state["claims"])
        claims[0]["ceiling"] = "Native support established."
        identifiers = deepcopy(self.state["identifiers"]["shas"])
        identifiers["fork_commit"] = "invented-sha"
        cases = [
            ({"identifiers.shas": {"replace": identifiers}}, self.admission,
             "SHA/path/status changed", "reject"),
            ({"claims": {"replace": claims}}, self.admission,
             "claim exceeds cited experiment", "quarantine"),
            ({"failed_or_superseded_paths": {"replace": []}}, self.admission,
             "omitted negative result", "reject"),
            ({"goal": {"from": self.state["goal"], "to": "Publish a different task."}},
             self.admission, "action outside mandate", "reject"),
            (self.fact_delta(), dict(self.admission, evidence=""),
             "state change without evidence", "reject"),
            ({"open_questions": {"replace": []}}, self.admission,
             "accepted evidence and questions preserved", "reject"),
            ({"current_state": {"from": "invented-prior", "to": "FACT"}},
             self.admission, "delta valid", "reject"),
        ]
        for delta, admission, check, result in cases:
            with self.subTest(check=check):
                receipt = evaluate(self.state, delta, admission)
                self.assert_unchanged(receipt, result=result)
                self.assert_failed(receipt, check)

    def test_required_evidence_ceiling_owner_and_unknown_fields(self):
        for field, item in (("verified_facts", {"fact": "Unevidenced fact."}),
                            ("claims", {"claim": "Claim.", "basis": "Basis."}),
                            ("open_questions", {"question": "Unowned question?"})):
            receipt = evaluate(self.state, {field: {"add": [item]}}, self.admission)
            self.assert_unchanged(receipt)
            self.assert_failed(receipt, "schema valid")
        changed = deepcopy(self.state)
        changed["expected_evidence"] = ["future.txt"]
        self.assertTrue(validate_state(changed))

    def test_terminal_statuses_cannot_be_promoted(self):
        for status in ("UNRESOLVED", "FAILED", "NEGATIVE", "FROZEN", "SUPERSEDED", "INCONCLUSIVE"):
            prior = deepcopy(self.state)
            prior["current_state"] = status
            delta = self.fact_delta()
            delta["current_state"] = {"from": status, "to": "FACT"}
            receipt = evaluate(prior, delta, self.admission)
            self.assert_unchanged(receipt, prior)
            self.assert_failed(receipt, "SHA/path/status changed")

    def test_two_transitions_chain_and_reject_quarantine_attempts_remain_proposed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.jsonl"
            first = append(path, None, self.genesis(), self.admission)
            self.assertEqual(first["transition"]["prior_state_hash"], "0" * 64)
            prefix = path.read_bytes()
            second = append(path, first["state"], self.fact_delta(), self.admission)
            self.assertEqual(second["transition"]["prior_state_hash"],
                             first["transition"]["resulting_state_hash"])
            self.assertTrue(path.read_bytes().startswith(prefix))
            for result, admission, conflict in (
                    ("reject", {}, False), ("quarantine", self.admission, True)):
                previous = second
                second = append(path, previous["state"], self.fact_delta("Attempt " + result),
                                admission, semantic_conflict=conflict)
                self.assert_unchanged(second, previous["state"], result)
                self.assertEqual(second["transition"]["seq"], previous["transition"]["seq"] + 1)
                self.assertEqual(replay(path), second)
            records = [loads(line) for line in path.read_text(encoding="utf-8").split("\n")[:-1]]
            self.assertEqual(len(records), 4)
            for record in records:
                self.assertEqual(set(record), RECORD_FIELDS)

    def test_rejected_genesis_is_diagnostic_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.jsonl"
            receipt = append(path, None, self.genesis(), {})
            self.assertEqual(receipt["transition"]["validation"]["result"], "reject")
            self.assertIsNone(receipt["state"])
            self.assertEqual(path.read_bytes(), b"")
            self.assertIsNone(replay(path))

    def test_stale_and_concurrent_writers_cannot_both_advance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.jsonl"
            first = append(path, None, self.genesis(), self.admission)
            barrier = threading.Barrier(2)

            def contender(label):
                barrier.wait(timeout=10)
                try:
                    return append(path, first["state"], self.fact_delta(label), self.admission)
                except ValueError:
                    return None

            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(contender, label) for label in ("A", "B")]
                results = [future.result(timeout=15) for future in futures]
            winners = [result for result in results if result is not None]
            self.assertEqual(len(winners), 1)
            self.assertEqual(replay(path), winners[0])
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "stale"):
                append(path, first["state"], self.fact_delta("Stale"), self.admission)
            self.assertEqual(path.read_bytes(), before)

    def test_tampered_records_and_incomplete_tail_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.jsonl"
            first = append(path, None, self.genesis(), self.admission)
            second = append(path, first["state"], self.fact_delta(), self.admission)
            original = [first["transition"], second["transition"]]
            changes = {
                "prior_state_hash": "0" * 64,
                "resulting_state_hash": "sha256:" + "f" * 64,
                "rendered_prose": "Invented accepted fact.",
                "task_id": "DIFFERENT-TASK",
                "seq": 1,
                "admission": dict(self.admission, by="Muse"),
                "validation": {"result": "accept", "checks": []},
            }
            for field, value in changes.items():
                with self.subTest(field=field):
                    records = deepcopy(original)
                    records[1][field] = value
                    path.write_text("".join(canonical_json(record) + "\n" for record in records),
                                    encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "quarantine"):
                        replay(path)
            path.write_bytes(b'{"schema":')
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "incomplete"):
                append(path, second["state"], self.fact_delta(), self.admission)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
