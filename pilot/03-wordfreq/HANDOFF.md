SCHEMA
The state schema is "openline.handoff-state.v0.1".

TASK ID
The task identifier is "REAL-HANDOFF-03".

GOAL
The goal is "Complete wordfreq: a stdin-to-stdout word-frequency counter per the frozen SPEC.md ([a-z0-9] tokenization, count-descending then word-ascending output); all 6 acceptance tests passing.".

CLAIMS
The recorded claims, bases, and ceilings are [{"basis":"The 3 failing tests enumerate the gap; the spec rules are closed.","ceiling":"No --top N flag, no minimum-length filter (open questions); no performance claim.","claim":"The remaining work is [a-z0-9] tokenization and count-descending/word-ascending output per SPEC.md."}].

CANONICAL TERMS
The canonical terms and definitions are {"COUNT_ORDER":"descending count, then ascending word; defines the output key order.","WORD":"a maximal run of [a-z0-9] after lowercasing; every other character is a separator."}.

PROPOSED STATE CHANGES
The proposed state changes are [].

IDENTIFIERS
The identifiers are {"dates":{"spec_frozen":"2026-10-03"},"paths":{"task_dir":"pilot/03-wordfreq"},"receipts":{},"shas":{"midtask_tests":"4133fd40f18e4002c85fab9ad2f4b92f6372a559827f4f0e8beef7b2d973b064","spec":"b80ae92e2972fe1dedf76f564c0d53640eec01bea23ef858713e3874ec56ac48","tests":"ff70821c24d04c8424f4920d74ef05c20917ab69e82884ff7d0c93b118120825","wordfreq_py":"0d000d2ac56e9474167cf7c628fd9d25879646b13d6696b1c9c6aebcdd55f782"},"versions":{"python":"3","schema":"openline.handoff-state.v0.1"}}.

CURRENT STATE
The current state is "MID_TASK_BASIC_COUNT_DONE".

AUTHORITY
The authority owner is "Terrynce White".

OWNER
The recorded roles are {"admitter":"Terrynce White","author":"Muse","executor":"Muse","proposer":"Terrynce White","verifier":"Muse"}.

FROZEN INVARIANTS
The frozen invariants are ["SPEC.md (pilot/03-wordfreq/SPEC.md) is frozen; implement to it, do not modify it.","Python 3 stdlib only; single file wordfreq.py.","Tokenization is exactly maximal [a-z0-9] runs after lowercasing; no stemming, no stop-words, no 'improvements'.","The 6 tests in tests/test_wordfreq.py are the acceptance check; no other correctness criterion."].

VERIFIED EVIDENCE
The verified facts and evidence references are [{"evidence":"pilot/03-wordfreq/SPEC.md sha256:b80ae92e2972fe1dedf76f564c0d53640eec01bea23ef858713e3874ec56ac48","fact":"SPEC.md frozen."},{"evidence":"pilot/03-wordfreq/evidence/midtask-tests.txt sha256:4133fd40f18e4002c85fab9ad2f4b92f6372a559827f4f0e8beef7b2d973b064","fact":"Basic counting, case folding, and empty input work: 3/6 tests pass."},{"evidence":"pilot/03-wordfreq/evidence/midtask-tests.txt sha256:4133fd40f18e4002c85fab9ad2f4b92f6372a559827f4f0e8beef7b2d973b064","fact":"Punctuation-aware tokenization and count-ordered output not implemented: 3/6 tests fail (punctuation separators, sort order, digits order); current code splits on whitespace only with first-seen key order."}].

OPEN QUESTIONS
The open questions and owners are [{"owner":"Terrynce White","question":"Should wordfreq support a --top N flag? Out of scope unless the owner approves; do not implement."},{"owner":"Terrynce White","question":"Should wordfreq support a minimum word-length filter? Out of scope unless the owner approves; do not implement."}].

FAILED / SUPERSEDED PATHS
The failed or superseded paths, classifications, and evidence references are [{"classification":"superseded — spec froze maximal [a-z0-9] runs (\\w includes underscore)","evidence":"pilot/03-wordfreq/SPEC.md (Tokenization section)","path":"regex \\w+ tokenization"}].

NEXT PERMITTED ACTION
The next permitted actions are ["Implement [a-z0-9] tokenization and count-descending/word-ascending output per SPEC.md.","Make all 6 tests pass; do not modify the tests or SPEC.md to do it."].

STOP CONDITIONS
The stop conditions are ["Do not modify the frozen SPEC.md.","Do not add dependencies; stdlib only, single file.","Do not 'improve' tokenization (no stemming, no stop-words); maximal [a-z0-9] runs exactly.","Do not implement --top N or minimum-length filter (open questions for the owner)."].
