"""Lossless controlled-English templates, version-locked to schema v0.1."""
from .canonical import canonical_json, loads
from .schema import STATE_SCHEMA, validate_state

RENDERER_VERSION = STATE_SCHEMA
_SECTIONS = (
    ("SCHEMA", "The state schema is ", "schema"),
    ("TASK ID", "The task identifier is ", "task_id"),
    ("GOAL", "The goal is ", "goal"),
    ("CLAIMS", "The recorded claims, bases, and ceilings are ", "claims"),
    ("CANONICAL TERMS", "The canonical terms and definitions are ", "canonical_terms"),
    ("PROPOSED STATE CHANGES", "The proposed state changes are ", "proposed_state_changes"),
    ("IDENTIFIERS", "The identifiers are ", "identifiers"),
    ("CURRENT STATE", "The current state is ", "current_state"),
    ("AUTHORITY", "The authority owner is ", "authority_owner"),
    ("OWNER", "The recorded roles are ", "roles"),
    ("FROZEN INVARIANTS", "The frozen invariants are ", "frozen_invariants"),
    ("VERIFIED EVIDENCE", "The verified facts and evidence references are ", "verified_facts"),
    ("OPEN QUESTIONS", "The open questions and owners are ", "open_questions"),
    ("FAILED / SUPERSEDED PATHS",
     "The failed or superseded paths, classifications, and evidence references are ",
     "failed_or_superseded_paths"),
    ("NEXT PERMITTED ACTION", "The next permitted actions are ", "next_permitted_actions"),
    ("STOP CONDITIONS", "The stop conditions are ", "stop_conditions"),
)


def render(state):
    errors = validate_state(state)
    if errors:
        raise ValueError("Invalid handoff state: " + "; ".join(errors))
    blocks = [heading + "\n" + sentence + canonical_json(state[field]) + "."
              for heading, sentence, field in _SECTIONS]
    return "\n\n".join(blocks) + "\n"


def parse_rendered(text):
    if not isinstance(text, str) or not text.endswith("\n"):
        raise ValueError("Rendered handoff must end with the template newline")
    blocks = text[:-1].split("\n\n")
    if len(blocks) != len(_SECTIONS):
        raise ValueError("Invalid rendering section count")
    state = {}
    for block, (heading, sentence, field) in zip(blocks, _SECTIONS):
        prefix = heading + "\n" + sentence
        if not block.startswith(prefix) or not block.endswith("."):
            raise ValueError("Invalid rendering template in section " + heading)
        state[field] = loads(block[len(prefix):-1])
    if render(state) != text:
        raise ValueError("Rendering is not the exact canonical v0.1 template")
    return state
