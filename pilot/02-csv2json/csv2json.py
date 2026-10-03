"""csv2json: CSV on stdin -> JSON on stdout. Spec: SPEC.md (frozen).

MID-TASK STATE: happy path implemented (valid rows, empty age -> null,
empty input, sorted keys, bad header). Malformed-row handling NOT
implemented: dirty rows raise ValueError instead of going to errors.
"""
import csv
import json
import sys


def main():
    data = sys.stdin.read()
    if not data.strip():
        sys.stdout.write(json.dumps({"rows": [], "errors": []}, sort_keys=True))
        return 0
    lines = data.splitlines()
    if lines[0] != "name,age,city":
        sys.stderr.write("bad header\n")
        return 1
    rows = []
    for fields in csv.reader(lines[1:]):
        if not fields or all(field == "" for field in fields):
            continue
        name, age_text, city = fields
        age = int(age_text) if age_text.strip() else None
        rows.append({"name": name, "age": age, "city": city})
    sys.stdout.write(json.dumps({"rows": rows, "errors": []}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
