"""csv2json: CSV on stdin -> JSON on stdout. Spec: SPEC.md (frozen)."""
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
    errors = []
    row_number = 0
    for raw in lines[1:]:
        if not raw.strip():
            continue
        row_number += 1
        fields = next(csv.reader([raw]))
        if len(fields) != 3:
            errors.append({
                "row": row_number, "raw": raw, "reason": "wrong column count",
            })
            continue
        name, age_text, city = fields
        try:
            age = int(age_text) if age_text != "" else None
        except ValueError:
            errors.append({"row": row_number, "raw": raw, "reason": "bad age"})
            continue
        rows.append({"name": name, "age": age, "city": city})
    sys.stdout.write(json.dumps({"rows": rows, "errors": errors}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
