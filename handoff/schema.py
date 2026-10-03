"""Structural validation of the exact frozen handoff state fields."""
from .canonical import json_errors

STATE_SCHEMA = "openline.handoff-state.v0.1"
STATE_FIELDS = (
    "schema", "task_id", "goal", "authority_owner", "current_state",
    "frozen_invariants", "verified_facts", "claims", "open_questions",
    "failed_or_superseded_paths", "canonical_terms", "proposed_state_changes",
    "next_permitted_actions", "stop_conditions", "identifiers", "roles",
)
ROLE_FIELDS = ("author", "proposer", "verifier", "admitter", "executor")
IDENTIFIER_FIELDS = ("shas", "paths", "versions", "dates", "receipts")
RECORD_FIELDS = {
    "verified_facts": ("fact", "evidence"),
    "claims": ("claim", "basis", "ceiling"),
    "open_questions": ("question", "owner"),
    "failed_or_superseded_paths": ("path", "classification", "evidence"),
}


def _object(value, path, fields, errors):
    if not isinstance(value, dict):
        errors.append(path + ": expected object")
        return False
    for field in fields:
        if field not in value:
            errors.append(path + "." + field + ": missing required field")
    for field in sorted((key for key in value if key not in fields), key=repr):
        errors.append(path + ": unknown field " + repr(field))
    return True


def _string(value, path, errors):
    if not isinstance(value, str) or not value.strip():
        errors.append(path + ": expected nonblank string")


def validate_state(state):
    """Shape only; historical roles are not reinterpreted as authority."""
    errors = json_errors(state)
    if not _object(state, "$", STATE_FIELDS, errors):
        return errors
    if state.get("schema") != STATE_SCHEMA:
        errors.append("$.schema: unknown state schema")
    for field in ("task_id", "goal", "authority_owner", "current_state"):
        if field in state:
            _string(state[field], "$." + field, errors)
    for field in ("frozen_invariants", "next_permitted_actions", "stop_conditions"):
        if field in state:
            values = state[field]
            if not isinstance(values, list):
                errors.append("$." + field + ": expected array")
            else:
                for index, item in enumerate(values):
                    _string(item, "$." + field + "[" + str(index) + "]", errors)
    for field, fields in RECORD_FIELDS.items():
        if field not in state:
            continue
        if not isinstance(state[field], list):
            errors.append("$." + field + ": expected array")
            continue
        for index, item in enumerate(state[field]):
            path = "$." + field + "[" + str(index) + "]"
            if _object(item, path, fields, errors):
                for key in fields:
                    if key in item:
                        _string(item[key], path + "." + key, errors)
    if "canonical_terms" in state:
        if not isinstance(state["canonical_terms"], dict):
            errors.append("$.canonical_terms: expected object")
        else:
            for term, definition in sorted(state["canonical_terms"].items(),
                                           key=lambda item: repr(item[0])):
                _string(term, "$.canonical_terms key", errors)
                _string(definition, "$.canonical_terms[" + repr(term) + "]", errors)
    if "proposed_state_changes" in state:
        proposals = state["proposed_state_changes"]
        if not isinstance(proposals, list) or any(
                not isinstance(item, dict) for item in proposals):
            errors.append("$.proposed_state_changes: expected object array")
    if "identifiers" in state and _object(state["identifiers"], "$.identifiers",
                                           IDENTIFIER_FIELDS, errors):
        for key in IDENTIFIER_FIELDS:
            if key in state["identifiers"] and not isinstance(
                    state["identifiers"][key], dict):
                errors.append("$.identifiers." + key + ": expected object")
    if "roles" in state and _object(state["roles"], "$.roles", ROLE_FIELDS, errors):
        for key in ROLE_FIELDS:
            if key in state["roles"]:
                _string(state["roles"][key], "$.roles." + key, errors)
    return errors
