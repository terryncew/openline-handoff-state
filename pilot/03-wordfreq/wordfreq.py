"""wordfreq: text on stdin -> word counts as JSON on stdout. Spec: SPEC.md (frozen)."""
import json
import re
import sys
from collections import Counter


def main():
    text = sys.stdin.read().lower()
    words = re.findall(r"[a-z0-9]+", text)
    counts = Counter(words)
    ordered = dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))
    sys.stdout.write(json.dumps(ordered))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
