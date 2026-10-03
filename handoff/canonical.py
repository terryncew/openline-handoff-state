"""Strict canonical UTF-8 JSON and hashes for HANDOFF STATE v0.1."""
import hashlib
import json
import math


def json_errors(value, path="$"):
    errors, active = [], set()
    stack = [(False, value, path)]
    while stack:
        leaving, node, location = stack.pop()
        if leaving:
            active.remove(id(node))
            continue
        if node is None or isinstance(node, bool):
            continue
        if isinstance(node, str):
            try:
                node.encode("utf-8")
            except UnicodeEncodeError:
                errors.append(location + ": string is not valid UTF-8")
        elif isinstance(node, int):
            continue
        elif isinstance(node, float):
            if not math.isfinite(node):
                errors.append(location + ": number must be finite")
        elif isinstance(node, (dict, list)):
            if id(node) in active:
                errors.append(location + ": cyclic JSON value")
                continue
            active.add(id(node))
            stack.append((True, node, location))
            if isinstance(node, dict):
                items = sorted(node.items(), key=lambda item: repr(item[0]))
                for key, child in reversed(items):
                    if not isinstance(key, str):
                        errors.append(location + ": object keys must be strings")
                    else:
                        try:
                            key.encode("utf-8")
                        except UnicodeEncodeError:
                            errors.append(location + ": object key is not valid UTF-8")
                    stack.append((False, child, location + "[" + repr(key) + "]"))
            else:
                for index in range(len(node) - 1, -1, -1):
                    stack.append((False, node[index], location + "[" + str(index) + "]"))
        else:
            errors.append(location + ": not a JSON value: " + type(node).__name__)
    return errors


def canonical_json(value):
    errors = json_errors(value)
    if errors:
        raise ValueError("Invalid canonical JSON: " + "; ".join(errors))
    try:
        result = json.dumps(value, sort_keys=True, separators=(",", ":"),
                            ensure_ascii=False, allow_nan=False)
        result.encode("utf-8")
        return result
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise ValueError("Cannot serialize canonical JSON: " + str(exc)) from exc


def state_hash(state):
    """Frozen v0.1 state objects have no self-hash field."""
    return "sha256:" + hashlib.sha256(canonical_json(state).encode("utf-8")).hexdigest()


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON object key: " + repr(key))
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("Nonfinite JSON constant: " + value)


def loads(text):
    if not isinstance(text, str):
        raise ValueError("JSON input must be a string")
    try:
        value = json.loads(text, object_pairs_hook=_unique_object,
                           parse_constant=_reject_constant)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Invalid JSON: " + str(exc)) from exc
    errors = json_errors(value)
    if errors:
        raise ValueError("Invalid JSON: " + "; ".join(errors))
    return value
