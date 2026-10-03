"""A local append-only JSONL store. POSIX locking; no background work."""
from copy import deepcopy
import fcntl
import os
from pathlib import Path

from .canonical import canonical_json, loads
from .core import evaluate, same, verify_record


def _read_log(stream):
    try:
        return stream.read()
    except UnicodeDecodeError as exc:
        raise ValueError("quarantine: invalid UTF-8 JSONL") from exc


def _replay_text(text):
    if text and not text.endswith("\n"):
        raise ValueError("quarantine: incomplete JSONL tail; manual recovery required")
    latest = None
    state = None
    for number, line in enumerate(text.split("\n")[:-1], 1):
        if not line:
            raise ValueError("quarantine: blank JSONL record at line " + str(number))
        try:
            record = loads(line)
        except ValueError as exc:
            raise ValueError("quarantine: invalid JSONL at line " + str(number)) from exc
        if not isinstance(record, dict) or record.get("seq") != number:
            raise ValueError("quarantine: sequence mismatch at line " + str(number))
        errors = verify_record(state, record)
        if errors:
            raise ValueError("quarantine: invalid record at line "
                             + str(number) + ": " + "; ".join(errors))
        reported_conflict = any(
            item == {"check": "semantic conflict", "pass": False}
            for item in record["validation"]["checks"])
        latest = evaluate(state, record["proposed_delta"], record["admission"],
                          seq=number, semantic_conflict=reported_conflict)
        if number == 1 and latest["transition"]["validation"]["result"] != "accept":
            raise ValueError("quarantine: log has no admitted genesis")
        state = latest["state"]
    return latest


def replay(path):
    """Verify the entire chain and return the latest receipt, or None."""
    try:
        stream = open(path, "r", encoding="utf-8", newline="")
    except FileNotFoundError:
        return None
    with stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
        try:
            return _replay_text(_read_log(stream))
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def append(path, prior, delta, admission, *, semantic_conflict=False):
    """Validate under lock and append exactly one transition.

    Rejected/quarantined attempts are retained without advancing accepted
    state. A rejected genesis is returned but cannot seed a state log.
    The caller supplies its exact accepted prior state; stale writers fail.
    """
    target = Path(path)
    # The caller chooses an explicit path. No implicit coordination directory.
    fd = os.open(target, os.O_RDWR | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "r+", encoding="utf-8", newline="") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            latest = _replay_text(_read_log(stream))
            current = latest["state"] if latest is not None else None
            if not same(prior, current):
                raise ValueError("reject: stale prior state; read the accepted head")
            seq = latest["transition"]["seq"] + 1 if latest is not None else 1
            receipt = evaluate(current, delta, admission, seq=seq,
                               semantic_conflict=semantic_conflict)
            if current is None and receipt["state"] is None:
                return receipt
            line = (canonical_json(receipt["transition"]) + "\n").encode("utf-8")
            stream.seek(0, os.SEEK_END)
            # One append syscall under the file lock. A crash/short write leaves
            # a detectable tail; no automatic truncation or reconciliation.
            written = os.write(stream.fileno(), line)
            if written != len(line):
                raise ValueError("quarantine: incomplete append; inspect JSONL tail")
            os.fsync(stream.fileno())
            return deepcopy(receipt)
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
