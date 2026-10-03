"""Strict JSON and CLI checks; no provider-replacement simulation."""
from copy import deepcopy
from pathlib import Path
import json
import tempfile
import unittest
import subprocess
import sys

from handoff.canonical import canonical_json, loads
from handoff.core import apply_delta, evaluate
from handoff.render import parse_rendered, render
from handoff.schema import validate_state
from handoff.store import append, replay

ROOT = Path(__file__).resolve().parents[2]


class StrictInputs(unittest.TestCase):
    def setUp(self):
        self.fixture = loads((ROOT / "test-fixture-valid.json").read_text(encoding="utf-8"))
        self.state = deepcopy(self.fixture["resulting_state"])
        self.admission = {"decision": "admit", "by": "Terrynce White",
                          "at": "2026-10-03T22:00:00Z", "evidence": "order.txt"}

    def test_duplicate_keys_nonfinite_and_unpaired_surrogates_rejected(self):
        for text in ('{"by":"Terrynce White","by":"Muse"}', '[NaN]',
                     '[Infinity]', '[1e999]', '"\\ud800"'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                loads(text)
        for value in (float("nan"), float("inf"), {"bad": "\ud800"}, {1: "value"}):
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                canonical_json(value)

    def test_nonobject_transition_inputs_are_clear_reject_errors(self):
        for delta, admission in (([], self.admission), ({}, []), ({}, None)):
            with self.subTest(delta=delta, admission=admission):
                with self.assertRaisesRegex(ValueError, "JSON objects"):
                    evaluate(self.state, delta, admission)

    def test_conditional_admission_cannot_accept(self):
        delta = {"verified_facts": {"add": [{
            "fact": "Bounded check completed.", "evidence": "result.txt"}]}}
        for decision in ("admit after owner confirmation", "admit nothing",
                         "admit TERM_A only", "pending owner confirmation",
                         "admission denied by owner", "do not admit this delta"):
            with self.subTest(decision=decision):
                receipt = evaluate(self.state, delta,
                                   dict(self.admission, decision=decision))
                self.assertEqual(receipt["transition"]["validation"]["result"], "reject")
                self.assertEqual(receipt["state"], self.state)

    def test_cycles_are_clear_errors(self):
        cyclic = []
        cyclic.append(cyclic)
        with self.assertRaisesRegex(ValueError, "cyclic"):
            canonical_json(cyclic)

    def test_json_boolean_is_not_integer_in_from_guard(self):
        state = deepcopy(self.state)
        state["identifiers"]["dates"]["guard"] = True
        with self.assertRaises(ValueError):
            apply_delta(state, {"identifiers.dates.guard": {"from": 1, "to": False}})

    def test_parent_child_delta_overlap_is_rejected(self):
        delta = {
            "roles": {"replace": self.state["roles"]},
            "roles.admitter": {"from": "Terrynce White", "to": "Terrynce White"},
        }
        with self.assertRaisesRegex(ValueError, "overlapping"):
            apply_delta(self.state, delta)

    def test_add_cannot_disguise_a_definition_rewrite(self):
        key = next(iter(self.state["canonical_terms"]))
        with self.assertRaisesRegex(ValueError, "overwrite"):
            apply_delta(self.state, {"canonical_terms": {"add": {key: "new meaning"}}})

    def test_json_schema_field_set_matches_frozen_state(self):
        machine = loads((ROOT / "handoff/state.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(set(machine["required"]), set(self.state))
        self.assertEqual(set(machine["properties"]), set(self.state))

    def test_template_drift_and_added_prose_rejected(self):
        prose = render(self.state)
        for changed in (prose + "Invented fact.\n", prose.replace(
                "The current state is ", "The current state appears to be ", 1),
                prose.replace('"Terrynce White"', '"Muse"', 1)):
            # The last is valid template but changed authority: parser does not
            # authenticate it; therefore only first two must reject.
            if '"Muse"' in changed and changed == prose.replace(
                    '"Terrynce White"', '"Muse"', 1):
                recovered = parse_rendered(changed)
                self.assertNotEqual(recovered, self.state)
            else:
                with self.assertRaises(ValueError):
                    parse_rendered(changed)

    def test_unicode_line_separators_remain_data_in_jsonl(self):
        state = deepcopy(self.state)
        state["goal"] += "\u2028Exact line separator.\u2029Exact paragraph separator."
        self.assertEqual(validate_state(state), [])
        self.assertEqual(parse_rendered(render(state)), state)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.jsonl"
            receipt = append(path, None, {k: {"to": v} for k, v in state.items()},
                             self.admission)
            self.assertEqual(replay(path), receipt)
            self.assertEqual(path.read_bytes().count(b"\n"), 1)

    def test_malformed_validation_is_a_clear_verification_error(self):
        from handoff.core import verify_record
        source = self.fixture["transition"]
        receipt = evaluate(self.fixture["prior_state"], source["proposed_delta"],
                           source["admission"], seq=source["seq"])
        for bad in ([], {}, True, None):
            record = deepcopy(receipt["transition"])
            record["validation"]["result"] = bad
            self.assertIn("malformed validation",
                          verify_record(self.fixture["prior_state"], record))

    def test_corrupt_utf8_log_is_quarantined_without_append(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.jsonl"
            path.write_bytes(b"\xff\n")
            with self.assertRaisesRegex(ValueError, "quarantine: invalid UTF-8"):
                replay(path)
            with self.assertRaisesRegex(ValueError, "quarantine: invalid UTF-8"):
                append(path, self.state, {}, self.admission)
            self.assertEqual(path.read_bytes(), b"\xff\n")

    def test_cli_accept_reject_and_quarantine_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "proposal.json"
            delta = {"verified_facts": {"add": [{
                "fact": "Bounded CLI result.", "evidence": "result.txt"}]}}
            request = {"prior_state": self.state, "proposed_delta": delta,
                       "admission": self.admission}
            for expected, missing_by, conflict in ((0, False, False),
                                                   (2, True, False),
                                                   (3, False, True)):
                request["admission"] = dict(self.admission)
                if missing_by:
                    del request["admission"]["by"]
                path.write_text(canonical_json(request), encoding="utf-8")
                command = [sys.executable, "-m", "handoff", "validate", str(path)]
                if conflict:
                    command.append("--semantic-conflict")
                completed = subprocess.run(command, cwd=ROOT, text=True,
                                           capture_output=True, timeout=15)
                self.assertEqual(completed.returncode, expected, completed.stderr)
                receipt = loads(completed.stdout)
                self.assertEqual(receipt["transition"]["validation"]["result"],
                                 {0: "accept", 2: "reject", 3: "quarantine"}[expected])

    def test_raw_seed_is_not_trusted_as_generated_prose(self):
        from handoff.core import verify_record
        source = self.fixture["transition"]
        errors = verify_record(self.fixture["prior_state"], source)
        self.assertIn("transition mismatch: rendered_prose", errors)
        receipt = evaluate(self.fixture["prior_state"], source["proposed_delta"],
                           source["admission"], seq=source["seq"])
        self.assertEqual(receipt["transition"]["validation"]["result"], "accept")


if __name__ == "__main__":
    unittest.main()
