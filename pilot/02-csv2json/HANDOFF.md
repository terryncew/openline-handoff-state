SCHEMA
The state schema is "openline.handoff-state.v0.1".

TASK ID
The task identifier is "REAL-HANDOFF-02".

GOAL
The goal is "Complete csv2json: a stdin-to-stdout CSV-to-JSON converter per the frozen SPEC.md, with malformed rows preserved in an errors array; all 8 acceptance tests passing.".

CLAIMS
The recorded claims, bases, and ceilings are [{"basis":"The 3 failing tests enumerate the gap; the spec rules are closed.","ceiling":"Does not cover CLI file arguments or TSV input (open questions); no performance claim.","claim":"The remaining work is exactly the malformed-row error handling per SPEC.md: errors array with row, raw line, and reason."}].

CANONICAL TERMS
The canonical terms and definitions are {"DATA_ROW_NUMBER":"1-based index over data rows only; the header is not counted.","ERROR_ROW":"a data row that cannot be parsed per the spec; preserved in the errors array with row number, raw line, and reason; never dropped."}.

PROPOSED STATE CHANGES
The proposed state changes are [].

IDENTIFIERS
The identifiers are {"dates":{"spec_frozen":"2026-10-03"},"paths":{"task_dir":"pilot/02-csv2json"},"receipts":{},"shas":{"csv2json_py":"603ccb6f7c790382fef807816283f4f4cb7f5a8b3a94769f3f2f926329d67c1b","expected_json":"834f7a32856186c812eb531de060166bdb93fdc1f39e6f6f8f5889c2db291082","input_csv":"a1fb28845b5323c227ddbe02c782a0bfb410de68d36a2dd6732be1dfa8259244","midtask_tests":"49deae75a3a35b3d7de1ed19ab9cef76b0f96f72d545c35a1673cb73a4e8065b","spec":"2b954ea36239bf6e861ec357063399926b57df992281d11cddd5ef043e8a567a","tests":"2f5d22f148da600b7777c78e93bdb3685b382f7e62fe07dd079758ba3b50fa48"},"versions":{"python":"3","schema":"openline.handoff-state.v0.1"}}.

CURRENT STATE
The current state is "MID_TASK_HAPPY_PATH_DONE".

AUTHORITY
The authority owner is "Terrynce White".

OWNER
The recorded roles are {"admitter":"Terrynce White","author":"Muse","executor":"Muse","proposer":"Terrynce White","verifier":"Muse"}.

FROZEN INVARIANTS
The frozen invariants are ["SPEC.md (pilot/02-csv2json/SPEC.md) is frozen; implement to it, do not modify it.","Python 3 stdlib only; single file csv2json.py.","Malformed rows are never silently dropped; they go to the errors array.","The 8 tests in tests/test_csv2json.py are the acceptance check; no other correctness criterion."].

VERIFIED EVIDENCE
The verified facts and evidence references are [{"evidence":"pilot/02-csv2json/SPEC.md sha256:2b954ea36239bf6e861ec357063399926b57df992281d11cddd5ef043e8a567a","fact":"SPEC.md frozen."},{"evidence":"pilot/02-csv2json/fixtures/input.csv sha256:a1fb28845b5323c227ddbe02c782a0bfb410de68d36a2dd6732be1dfa8259244; pilot/02-csv2json/fixtures/expected.json sha256:834f7a32856186c812eb531de060166bdb93fdc1f39e6f6f8f5889c2db291082","fact":"Fixtures input.csv and expected.json frozen."},{"evidence":"pilot/02-csv2json/evidence/midtask-tests.txt sha256:49deae75a3a35b3d7de1ed19ab9cef76b0f96f72d545c35a1673cb73a4e8065b","fact":"Happy path implemented: 5/8 tests pass (valid rows, empty age as null, empty input, sorted keys, bad header)."},{"evidence":"pilot/02-csv2json/evidence/midtask-tests.txt sha256:49deae75a3a35b3d7de1ed19ab9cef76b0f96f72d545c35a1673cb73a4e8065b","fact":"Malformed-row handling not implemented: 3/8 tests fail (bad age, wrong column counts, fixture end-to-end); current code raises ValueError on dirty rows."}].

OPEN QUESTIONS
The open questions and owners are [{"owner":"Terrynce White","question":"Should csv2json also accept TSV input? Out of scope unless the owner approves; do not implement."},{"owner":"Terrynce White","question":"Should csv2json accept a file path argument, or stay stdin-only? Currently stdin-only per spec; do not add."}].

FAILED / SUPERSEDED PATHS
The failed or superseded paths, classifications, and evidence references are [{"classification":"superseded — spec froze stdin/stdout","evidence":"pilot/02-csv2json/SPEC.md (Input section)","path":"argparse CLI with file-path arguments"}].

NEXT PERMITTED ACTION
The next permitted actions are ["Implement malformed-row handling per SPEC.md (errors array with row/raw/reason).","Make all 8 tests pass; do not modify the tests or SPEC.md to do it."].

STOP CONDITIONS
The stop conditions are ["Do not modify the frozen SPEC.md.","Do not silently drop malformed rows.","Do not add dependencies; stdlib only, single file.","Do not implement TSV input or file-path arguments (open questions for the owner)."].
