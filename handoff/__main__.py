"""Explicit local commands; no current-agent or authority defaults."""
import argparse
import subprocess
from pathlib import Path
import sys

from .canonical import canonical_json, loads
from .closeout import Allowlist, verify_closeout
from .core import evaluate, verify_record
from .render import render, parse_rendered
from .store import append, replay


def read_json(path):
    return loads(Path(path).read_text(encoding="utf-8"))


def _git_bytes(args):
    """Run git; raise ValueError with a short message on failure."""
    result = subprocess.run(["git", *args], capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip().split("\n")[0]
        raise ValueError(f"git {' '.join(args)} failed: {detail[:200]}")
    return result.stdout


def _looks_repo_relative(path):
    return (isinstance(path, str) and bool(path)
            and not path.startswith("/") and "\\" not in path
            and all(part not in {"", ".", ".."} for part in path.split("/")))


def _load_closeout_inputs(frozen_ref, candidate_ref, task_dir):
    """Load verifier inputs from two local git refs. No network access."""
    loaded = {}
    for label, ref in (("frozen", frozen_ref), ("candidate", candidate_ref)):
        _git_bytes(["rev-parse", "--verify", "--quiet", ref + "^{commit}"])
        try:
            loaded[label + "_log"] = _git_bytes(
                ["show", f"{ref}:{task_dir}/handoff-transition.jsonl"]).decode("utf-8")
            loaded[label + "_state"] = loads(_git_bytes(
                ["show", f"{ref}:{task_dir}/handoff-state.json"]).decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"{label} ref {ref}: cannot read task inputs: {exc}")
        names = _git_bytes(
            ["ls-tree", "-r", "--name-only", ref, "--", task_dir + "/"]
        ).decode("utf-8").split()
        loaded[label + "_files"] = {
            name: _git_bytes(["show", f"{ref}:{name}"]) for name in names}
    return loaded


def verify_closeout_command(args):
    """CLI wrapper around the canonical verify_closeout(). Verifies only."""
    supplied = (args.allow_implementation_changed or []) + (args.allow_evidence_added or [])
    for path in supplied:
        if not _looks_repo_relative(path):
            print(f"error: allowlist path is not repository-relative: {path!r}",
                  file=sys.stderr)
            return 2
    try:
        inputs = _load_closeout_inputs(args.frozen_ref, args.candidate_ref, args.task_dir)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = verify_closeout(
        frozen_log_text=inputs["frozen_log"],
        candidate_log_text=inputs["candidate_log"],
        frozen_head_state=inputs["frozen_state"],
        candidate_state=inputs["candidate_state"],
        frozen_files=inputs["frozen_files"],
        candidate_files=inputs["candidate_files"],
        allowlist=allowlist_for(args),
        authority_owner=args.owner,
        task_dir=args.task_dir,
    )
    report = {
        "passed": result.passed,
        "failures": [{"check": f.check, "detail": f.detail} for f in result.failures],
        "checks_run": list(result.checks_run),
        "file_checks": result.file_checks,
        "frozen_ref": args.frozen_ref,
        "candidate_ref": args.candidate_ref,
        "task_dir": args.task_dir,
        "authority_owner": args.owner,
    }
    print(canonical_json(report))
    return 0 if result.passed else 1


def allowlist_for(args):
    return Allowlist(
        implementation_changed=list(args.allow_implementation_changed or []),
        evidence_added=list(args.allow_evidence_added or []))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("validate", "append"):
        item = sub.add_parser(command)
        item.add_argument("proposal", help="JSON with prior_state, proposed_delta, admission")
        if command == "append":
            item.add_argument("--log", required=True)
        item.add_argument("--semantic-conflict", action="store_true",
                          help="force quarantine; cannot grant acceptance")
    item = sub.add_parser("replay")
    item.add_argument("--log", required=True)
    item = sub.add_parser("render")
    item.add_argument("state")
    item = sub.add_parser("parse-rendered")
    item.add_argument("prose")
    item = sub.add_parser("verify")
    item.add_argument("fixture", help="JSON with prior_state and transition")
    item = sub.add_parser("verify-closeout",
                          help="verify a candidate closeout against a frozen start")
    item.add_argument("--frozen-ref", required=True, help="git ref of the frozen starting state")
    item.add_argument("--candidate-ref", required=True, help="git ref of the candidate closeout")
    item.add_argument("--task-dir", required=True, help="repository-relative task directory")
    item.add_argument("--owner", required=True, help="exact authority owner")
    item.add_argument("--allow-implementation-changed", action="append", default=[],
                      help="repo-relative path of a legitimately changed file (repeatable)")
    item.add_argument("--allow-evidence-added", action="append", default=[],
                      help="repo-relative path of a legitimately added evidence file (repeatable)")
    args = parser.parse_args(argv)
    if args.command == "verify-closeout":
        return verify_closeout_command(args)
    try:
        if args.command in {"validate", "append"}:
            request = read_json(args.proposal)
            if not isinstance(request, dict) or set(request) != {
                    "prior_state", "proposed_delta", "admission"}:
                raise ValueError("proposal requires prior_state, proposed_delta, admission")
            operation = append if args.command == "append" else evaluate
            positional = [args.log] if args.command == "append" else []
            result = operation(*positional, request["prior_state"],
                               request["proposed_delta"], request["admission"],
                               semantic_conflict=args.semantic_conflict)
            print(canonical_json(result))
            disposition = result["transition"]["validation"]["result"]
            return {"accept": 0, "reject": 2, "quarantine": 3}[disposition]
        if args.command == "replay":
            print(canonical_json(replay(args.log)))
        elif args.command == "render":
            print(render(read_json(args.state)), end="")
        elif args.command == "parse-rendered":
            print(canonical_json(parse_rendered(
                Path(args.prose).read_text(encoding="utf-8"))))
        elif args.command == "verify":
            fixture = read_json(args.fixture)
            errors = verify_record(fixture["prior_state"], fixture["transition"])
            print(canonical_json(errors))
            return 2 if errors else 0
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print("reject/quarantine: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
