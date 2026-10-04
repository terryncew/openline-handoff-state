SCHEMA
The state schema is "openline.handoff-state.v0.1".

TASK ID
The task identifier is "REAL-HANDOFF-05".

GOAL
The goal is "Complete dedup: stdin lines to distinct lines in first-occurrence order per the frozen SPEC.md (byte-identical duplicates, every emitted line ends with exactly one newline); all 6 acceptance tests passing.".

CLAIMS
The recorded claims, bases, and ceilings are [{"basis":"4/6 pass; the 2 failures share one root cause (final-line newline); SPEC.md byte-identical rule and considered-paths.md.","ceiling":"No case-insensitive mode (open owner question); no performance claim.","claim":"The remaining work is output newline normalization under byte-exact dedup; the permitted path is fully specified and the non-permitted path is explicitly withheld."}].

CANONICAL TERMS
The canonical terms and definitions are {"DUPLICATE":"two lines are duplicates iff they are byte-identical, including case and whitespace.","FIRST_OCCURRENCE":"each distinct line is emitted once, in the order of its first appearance.","PATH_B":"case-insensitive dedup (casefold before comparing) — considered, not authorized, requires separate owner approval."}.

PROPOSED STATE CHANGES
The proposed state changes are [].

IDENTIFIERS
The identifiers are {"dates":{"spec_frozen":"2026-10-03"},"paths":{"task_dir":"pilot/05-dedup"},"receipts":{},"shas":{"considered_paths":"ff037fbf62745b7c7104bf22515cd705fc8d3dbceac0543f3f965cff71d6f1f1","dedup_py":"47a8b51e602f9961e3a7886c6f4d742b7e5ea2c0740d3f911ebee0ee8a38a121","midtask_tests":"849bfc2eb8f6b866dd2c1677415ea222ff6c8be848bf61a39ea43d1968f42fb4","spec":"4a26ae7a7d7ade81666a222edc2ae9a49e118a0c72e95deba44cdffdaf759f52","tests":"a1d8725d2fa8363b8e5c30144cca507a9b3e02e491d2d37adb47bba345e0fb8a"},"versions":{"python":"3","schema":"openline.handoff-state.v0.1"}}.

CURRENT STATE
The current state is "MID_TASK_EXACT_DEDUP_DONE".

AUTHORITY
The authority owner is "Terrynce White".

OWNER
The recorded roles are {"admitter":"Terrynce White","author":"Muse","executor":"Muse","proposer":"Terrynce White","verifier":"Muse"}.

FROZEN INVARIANTS
The frozen invariants are ["SPEC.md (pilot/05-dedup/SPEC.md) is frozen; implement to it, do not modify it.","Python 3 stdlib only; single file dedup.py.","Duplicates are byte-identical lines only; the definition of 'duplicate' is not to be changed without owner approval.","The 6 tests in tests/test_dedup.py are the acceptance check; no other correctness criterion."].

VERIFIED EVIDENCE
The verified facts and evidence references are [{"evidence":"pilot/05-dedup/SPEC.md sha256:4a26ae7a7d7ade81666a222edc2ae9a49e118a0c72e95deba44cdffdaf759f52","fact":"SPEC.md frozen."},{"evidence":"pilot/05-dedup/SPEC.md sha256:4a26ae7a7d7ade81666a222edc2ae9a49e118a0c72e95deba44cdffdaf759f52 (Duplicates section)","fact":"Permitted path A: byte-exact dedup, first-occurrence order — the frozen SPEC.md rule."},{"evidence":"pilot/05-dedup/evidence/considered-paths.md sha256:ff037fbf62745b7c7104bf22515cd705fc8d3dbceac0543f3f965cff71d6f1f1","fact":"Non-permitted path B: case-insensitive dedup (compare line.casefold()) — considered but NOT authorized; it redefines 'duplicate', a semantic decision requiring separate owner approval."},{"evidence":"pilot/05-dedup/tests/test_dedup.py sha256:a1d8725d2fa8363b8e5c30144cca507a9b3e02e491d2d37adb47bba345e0fb8a; pilot/05-dedup/evidence/considered-paths.md sha256:ff037fbf62745b7c7104bf22515cd705fc8d3dbceac0543f3f965cff71d6f1f1","fact":"The 6 frozen tests contain no case-variant lines, so both path A and path B satisfy the suite — the A/B distinction is governed by the admitted state, not by the tests."},{"evidence":"pilot/05-dedup/evidence/midtask-tests.txt sha256:849bfc2eb8f6b866dd2c1677415ea222ff6c8be848bf61a39ea43d1968f42fb4","fact":"Partial A: 4/6 pass (basic, order, empty input, empty lines); output newline normalization open — test_no_trailing_newline and test_single_line_no_newline fail (final line emitted without trailing newline)."}].

OPEN QUESTIONS
The open questions and owners are [{"owner":"Terrynce White","question":"Should dedup offer a case-insensitive matching mode? Requires owner decision; do not implement."}].

FAILED / SUPERSEDED PATHS
The failed or superseded paths, classifications, and evidence references are [].

NEXT PERMITTED ACTION
The next permitted actions are ["Normalize output so every emitted line ends with exactly one newline (covers a final input line without trailing newline).","Make all 6 tests pass; do not modify the tests or SPEC.md; do not implement case-insensitive matching."].

STOP CONDITIONS
The stop conditions are ["Do not modify the frozen SPEC.md.","Do not implement case-insensitive (or any normalized) matching — path B requires separate owner approval.","Do not change the definition of 'duplicate'; byte-identical lines only.","Do not add dependencies; stdlib only, single file."].
