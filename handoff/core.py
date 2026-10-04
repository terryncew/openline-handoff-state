"""Deterministic Stage-1 transition evaluation. No authority is inferred."""
from copy import deepcopy
from datetime import datetime

from .canonical import canonical_json, state_hash
from .schema import validate_state
from .render import render

GENESIS = "0" * 64
STATE_SCHEMA = "openline.handoff-state.v0.1"
TRANSITION_SCHEMA = "openline.handoff-transition.v0.1"
# Evaluator version. The state/transition schemas are unchanged by
# CLAIM-EVOLUTION-001; only the claim-transition rule in evaluate() changed.
EVALUATOR_VERSION = "0.1.1"
STATE_FIELDS = {
    "schema", "task_id", "goal", "authority_owner", "current_state",
    "frozen_invariants", "verified_facts", "claims", "open_questions",
    "failed_or_superseded_paths", "canonical_terms", "proposed_state_changes",
    "next_permitted_actions", "stop_conditions", "identifiers", "roles",
}
RECORD_FIELDS = {
    "schema", "task_id", "seq", "prior_state_hash", "proposed_delta",
    "validation", "admission", "resulting_state_hash", "rendered_prose",
}
TERMINAL_STATUSES = {
    "UNRESOLVED", "FAILED", "NEGATIVE", "FROZEN", "SUPERSEDED", "INCONCLUSIVE",
}


def same(left, right):
    """JSON equality, including distinctions between true and 1."""
    return canonical_json(left) == canonical_json(right)


def nonblank(value):
    return isinstance(value, str) and bool(value.strip())


def apply_delta(prior, delta):
    """Apply only explicit from/to, replace, or add operations."""
    if not isinstance(delta, dict) or not delta:
        raise ValueError("delta must be a nonempty field-level object")
    canonical_json(delta)
    if prior is None:
        if set(delta) != STATE_FIELDS:
            raise ValueError("genesis must establish every frozen state field")
        if any(not isinstance(op, dict) or set(op) != {"to"}
               for op in delta.values()):
            raise ValueError("genesis fields require exactly a to operation")
        return {field: deepcopy(op["to"]) for field, op in delta.items()}
    result = deepcopy(prior)
    paths = sorted(delta)
    for index, path in enumerate(paths):
        if not isinstance(path, str) or not path or any(
                not part for part in path.split(".")):
            raise ValueError("delta paths must be nonempty field paths")
        if path.split(".")[0] not in STATE_FIELDS:
            raise ValueError("unknown state field: " + path)
        if any(other.startswith(path + ".") for other in paths[index + 1:]):
            raise ValueError("overlapping delta paths: " + path)
    for path in paths:
        parts = path.split(".")
        parent = result
        for part in parts[:-1]:
            if not isinstance(parent, dict) or part not in parent:
                raise ValueError("unknown delta path: " + path)
            parent = parent[part]
        leaf = parts[-1]
        if not isinstance(parent, dict) or leaf not in parent:
            raise ValueError("unknown delta path: " + path)
        old = parent[leaf]
        op = delta[path]
        if not isinstance(op, dict):
            raise ValueError("field operation must be an object: " + path)
        if set(op) == {"from", "to"}:
            if not same(old, op["from"]):
                raise ValueError("from value does not match accepted state: " + path)
            parent[leaf] = deepcopy(op["to"])
        elif set(op) == {"replace"}:
            parent[leaf] = deepcopy(op["replace"])
        elif set(op) == {"add"}:
            added = op["add"]
            if isinstance(old, list) and isinstance(added, list):
                parent[leaf] = old + deepcopy(added)
            elif isinstance(old, dict) and isinstance(added, dict):
                if set(old) & set(added):
                    raise ValueError("add cannot overwrite an existing key: " + path)
                parent[leaf] = dict(old, **deepcopy(added))
            else:
                raise ValueError("add requires matching array/object types: " + path)
        else:
            raise ValueError("unsupported field operation: " + path)
    return result


def _prefix(before, after):
    return isinstance(after, list) and len(after) >= len(before) and same(
        before, after[:len(before)])


def _retains_map(before, after):
    return isinstance(after, dict) and all(
        key in after and same(value, after[key]) for key, value in before.items())


def _decision_admits(value):
    # A narrow invocation contract, not an inference from arbitrary prose.
    return isinstance(value, str) and (value in {
        "admit", "accept", "outreach authorized and executed",
    })


def _admission_complete(admission):
    if not isinstance(admission, dict) or set(admission) != {
            "decision", "by", "at", "evidence"}:
        return False
    if not all(nonblank(value) for value in admission.values()):
        return False
    if not _decision_admits(admission["decision"]):
        return False
    try:
        instant = datetime.fromisoformat(admission["at"].replace("Z", "+00:00"))
    except ValueError:
        return False
    return instant.tzinfo is not None


def _literal_conflict(state):
    facts = {entry["fact"] for entry in state["verified_facts"]}
    for fact in facts:
        for marker in ("NOT: ", "NOT "):
            if fact.startswith(marker) and fact[len(marker):] in facts:
                return True
    return False


def _claim_transition_ok(prior, candidate, delta, complete, identity_ok):
    """Explicit claim-evolution lane (CLAIM-EVOLUTION-001).

    Unchanged claims keep existing behavior (pass). A changed claim is
    accepted only when ALL of the following hold:
      - the delta carries an explicit from/to compare-and-replace for
        "claims" whose "from" matches the prior claims exactly;
      - the replacement is a non-empty list of well-formed entries
        (nonblank claim, basis, ceiling);
      - the transition has a complete exact-owner admission;
      - verified_facts strictly extend the prior's (prefix preserved) and
        every newly added fact carries nonblank evidence.
    The evidence rule is the mechanically defined bound: a replacement
    claim must ride with new evidence, and its ceiling must be nonblank
    (an unbounded claim is a broadening). Anything else fails, which maps
    to quarantine via the semantic set — never silent acceptance, and an
    unadmitted or wrong-owner mutation additionally fails the non-semantic
    admission checks, mapping to reject.
    """
    if same(prior["claims"], candidate["claims"]):
        return True
    op = delta.get("claims")
    if not isinstance(op, dict) or set(op) != {"from", "to"}:
        return False
    if not same(op["from"], prior["claims"]):
        return False
    new_claims = op["to"]
    if not same(new_claims, candidate["claims"]):
        return False
    if not isinstance(new_claims, list) or not new_claims:
        return False
    for entry in new_claims:
        if not isinstance(entry, dict):
            return False
        if not nonblank(entry.get("claim")):
            return False
        if not nonblank(entry.get("basis")):
            return False
        if not nonblank(entry.get("ceiling")):
            return False
    if not (complete and identity_ok):
        return False
    prior_facts = prior["verified_facts"]
    candidate_facts = candidate["verified_facts"]
    if not (isinstance(candidate_facts, list)
            and len(candidate_facts) > len(prior_facts)
            and _prefix(prior_facts, candidate_facts)):
        return False
    for item in candidate_facts[len(prior_facts):]:
        if not isinstance(item, dict) or not nonblank(item.get("evidence")):
            return False
    return True


def evaluate(prior, delta, admission, *, seq=1, semantic_conflict=False):
    """Return {state, transition}; failures never advance canonical state.

    Supplying a complete admission is a declaration of admission by the named
    principal, not authentication of that principal. Missing authority stays
    proposed. semantic_conflict can only force quarantine, never acceptance.
    """
    if type(seq) is not int or seq < 1:
        raise ValueError("seq must be a positive integer")
    if type(semantic_conflict) is not bool:
        raise ValueError("semantic_conflict must be a boolean")
    if prior is not None and validate_state(prior):
        raise ValueError("invalid prior state: " + "; ".join(validate_state(prior)))
    if not isinstance(delta, dict) or not isinstance(admission, dict):
        raise ValueError("proposed_delta and admission must be JSON objects")
    # Reject non-JSON inputs rather than serialize ambiguous evidence.
    canonical_json(delta)
    canonical_json(admission)
    candidate = None
    try:
        candidate = apply_delta(prior, delta)
    except ValueError:
        pass
    shape_ok = candidate is not None and not validate_state(candidate)
    base = candidate if prior is None and shape_ok else prior
    complete = _admission_complete(admission)
    explicit = isinstance(admission, dict) and nonblank(admission.get("by"))
    role_admitter = (candidate["roles"].get("admitter")
                     if isinstance(candidate, dict)
                     and isinstance(candidate.get("roles"), dict) else None)
    owner = base.get("authority_owner") if base is not None else None
    identity_ok = (shape_ok and explicit and owner == admission["by"]
                   and role_admitter == admission["by"]
                   and candidate["authority_owner"] == owner)
    checks = []

    def check(name, passed):
        checks.append({"check": name, "pass": bool(passed)})

    check("schema valid", shape_ok)
    check("delta valid", candidate is not None)
    check("explicit admitter", explicit and nonblank(role_admitter))
    check("explicit admission decision", isinstance(admission, dict)
          and _decision_admits(admission.get("decision")))
    check("admitter matches authority_owner (exact)", identity_ok)
    facts_have_evidence = (isinstance(candidate, dict)
        and isinstance(candidate.get("verified_facts"), list)
        and all(isinstance(item, dict) and nonblank(item.get("evidence"))
                for item in candidate["verified_facts"]))
    if not shape_ok:
        check("OPEN→FACT without evidence", facts_have_evidence)
        check("state change without evidence", complete)
    else:
        check("OPEN→FACT without evidence",
              not (prior is not None and prior["current_state"] == "OPEN"
                   and candidate["current_state"] == "FACT")
              or (len(candidate["verified_facts"]) > len(prior["verified_facts"])
                  and _prefix(prior["verified_facts"], candidate["verified_facts"])))
        check("FROZEN invariant modified",
              prior is None or same(prior["frozen_invariants"],
                                    candidate["frozen_invariants"]))
        identifiers_ok = prior is None or all(
            _retains_map(prior["identifiers"][group],
                         candidate["identifiers"][group])
            for group in prior["identifiers"])
        status_ok = (prior is None or prior["current_state"] not in TERMINAL_STATUSES
                     or prior["current_state"] == candidate["current_state"])
        task_ok = prior is None or prior["task_id"] == candidate["task_id"]
        check("SHA/path/status changed", identifiers_ok and status_ok and task_ok)
        terms_ok = prior is None or _retains_map(
            prior["canonical_terms"], candidate["canonical_terms"])
        check("renamed canonical concept", terms_ok)
        new_terms = prior is None and bool(candidate["canonical_terms"]) or (
            prior is not None and bool(set(candidate["canonical_terms"])
                                      - set(prior["canonical_terms"])))
        check("new canonical term without admission",
              not new_terms or (complete and identity_ok))
        check("claim exceeds cited experiment",
              prior is None or _claim_transition_ok(
                  prior, candidate, delta, complete, identity_ok))
        check("omitted negative result",
              prior is None or _prefix(prior["failed_or_superseded_paths"],
                                       candidate["failed_or_superseded_paths"]))
        mandate_ok = (prior is None or (
            same(prior["goal"], candidate["goal"])
            and same(prior["stop_conditions"], candidate["stop_conditions"])))
        check("action outside mandate", complete and identity_ok and mandate_ok)
        check("state change without evidence", complete)
        check("semantic conflict", not semantic_conflict
              and not _literal_conflict(candidate))
        check("accepted evidence and questions preserved",
              prior is None or (
                  _prefix(prior["verified_facts"], candidate["verified_facts"])
                  and _prefix(prior["open_questions"], candidate["open_questions"])))
    failed = {item["check"] for item in checks if not item["pass"]}
    semantic = {"semantic conflict", "claim exceeds cited experiment"}
    disposition = ("reject" if failed - semantic else
                   "quarantine" if failed else "accept")
    accepted = candidate if disposition == "accept" else prior
    record = {
        "schema": TRANSITION_SCHEMA,
        "task_id": (accepted or candidate or {}).get("task_id", ""),
        "seq": seq,
        "prior_state_hash": GENESIS if prior is None else state_hash(prior),
        "proposed_delta": deepcopy(delta),
        "validation": {"result": disposition, "checks": checks},
        "admission": deepcopy(admission),
        "resulting_state_hash": GENESIS if accepted is None else state_hash(accepted),
        "rendered_prose": "" if accepted is None else render(accepted),
    }
    return {"state": deepcopy(accepted), "transition": record}


def verify_record(prior, record):
    """Independently check a stored record; never trust its acceptance flag."""
    errors = []
    if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
        return ["transition fields do not match frozen schema"]
    if record["schema"] != TRANSITION_SCHEMA:
        errors.append("unknown transition schema")
    validation = record["validation"]
    if (not isinstance(validation, dict) or set(validation) != {"result", "checks"}
            or not isinstance(validation["result"], str)
            or validation["result"] not in {"accept", "reject", "quarantine"}
            or not isinstance(validation["checks"], list)
            or any(not isinstance(item, dict) or set(item) != {"check", "pass"}
                   or not nonblank(item.get("check")) or type(item.get("pass")) is not bool
                   for item in validation["checks"])):
        return errors + ["malformed validation"]
    # A recorded conflict is a quarantine signal only. It cannot waive checks.
    reported_conflict = any(item == {"check": "semantic conflict", "pass": False}
                            for item in validation["checks"])
    try:
        expected = evaluate(prior, record["proposed_delta"], record["admission"],
                            seq=record["seq"], semantic_conflict=reported_conflict)
    except (ValueError, TypeError, KeyError) as exc:
        return errors + ["cannot evaluate transition: " + str(exc)]
    for field in RECORD_FIELDS:
        if not same(expected["transition"][field], record[field]):
            errors.append("transition mismatch: " + field)
    return sorted(errors)
