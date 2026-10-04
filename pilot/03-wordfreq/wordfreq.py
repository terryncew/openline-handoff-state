"""wordfreq: text on stdin -> word counts as JSON on stdout. Spec: SPEC.md (frozen).

MID-TASK STATE: basic counting, case folding, and empty input work.
Punctuation-aware tokenization and count-ordered output NOT implemented:
whitespace split only, first-seen key order.
"""
import json
import sys
from collections import Counter


def main():
    text = sys.stdin.read().lower()
    words = [word for word in text.split() if word]
    counts = Counter(words)
    sys.stdout.write(json.dumps(dict(counts)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
