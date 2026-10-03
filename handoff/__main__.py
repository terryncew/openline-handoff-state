"""Explicit local commands; no current-agent or authority defaults."""
import argparse
from pathlib import Path
import sys

from .canonical import canonical_json, loads
from .core import evaluate, verify_record
from .render import render, parse_rendered
from .store import append, replay


def read_json(path):
    return loads(Path(path).read_text(encoding="utf-8"))


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
    args = parser.parse_args(argv)
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
