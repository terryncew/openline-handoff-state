"""SEQ-1 HISTORICAL IMPLEMENTATION — broad input handling.

This is the implementation built under the seq-1 accepted state, which
authorized both one-number-per-line and comma-separated values per line.

It is preserved as historical evidence. It is NOT current: the seq-2
accepted state (owner decision 2026-10-03) revoked comma-separated input.
Do not treat this file as the deliverable; the deliverable is stats.py.
"""
import json
import sys


def main():
    nums = []
    for raw in sys.stdin:
        for part in raw.strip().split(","):
            part = part.strip()
            if not part:
                continue
            nums.append(float(part))
    sys.stdout.write(json.dumps({"count": len(nums), "sum": sum(nums)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
