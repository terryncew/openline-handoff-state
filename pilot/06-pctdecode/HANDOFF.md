SCHEMA
The state schema is "openline.handoff-state.v0.1".

TASK ID
The task identifier is "REAL-HANDOFF-06".

GOAL
The goal is "Complete pctdecode: stdin lines to percent-decoded lines per the frozen SPEC.md (%XX decoding either hex case, malformed % emitted literally, newline framing preserved); all 6 acceptance tests passing.".

CLAIMS
The recorded claims, bases, and ceilings are [{"basis":"evidence/probe-wellformed.txt; 4/6 tests with the 2 failures being the defined gap; SPEC.md Decoding section.","ceiling":"No claim about '+' semantics (unresolved, owner-owned); no claim of form-encoding conformance; no claim of equivalence to any one-call form-decoder; no claim beyond the probed inputs.","claim":"The decoder correctly decodes %XX sequences in either hex case; malformed-% literal passthrough is the defined remaining work."}].

CANONICAL TERMS
The canonical terms and definitions are {"MALFORMED_PCT":"a '%' not followed by two hex digits; emitted literally, scanning continues after the '%'.","PCT_SEQUENCE":"% followed by two hex digits (either case), decoded to the character with that code point.","UNRESOLVED_PLUS":"whether '+' should decode to space — not established by any evidence, owner-owned, must not be assumed."}.

PROPOSED STATE CHANGES
The proposed state changes are [].

IDENTIFIERS
The identifiers are {"dates":{"closeout":"2026-10-03","spec_frozen":"2026-10-03"},"paths":{"task_dir":"pilot/06-pctdecode"},"receipts":{},"shas":{"midtask_tests":"27723e8d7b02696dcd360b1a73764518aac3dc060e2932de5d4348c598887db6","no_plus":"7cb134ae1d22863308c689fcd08a6525bdab8417496d9c9aeb466ca3603643e6","pctdecode_py":"57830db60e9105949126e91a5a72f3ebd20caf0c384fdeb057669df8a2a84f33","pctdecode_py_completed":"8b22e6b3a814e6719d53bbbe9e2bd8ebc9fb44de296d164ff159c7d47b5030d1","probe_malformed":"86852c6c9d45df6b98f1b4a9c696d2dce2d785f728a07ab58ae824d81e29fc2c","probe_wellformed":"7d915a9b66d56b6fcc9cdf186cf5d464328961182eca80e49f1263ac07472847","spec":"b25dfd4a248cebaead29412e1eba9b5dbaadc43146ceae0dff21de881982ae33","successor_commit":"05c2af845d224efcaf41eb5058e24d3595cc4633","tests":"4e25387a3592dd43384fb9514feac2015af33b308f8400e1e62129267da647b7"},"versions":{"python":"3","schema":"openline.handoff-state.v0.1"}}.

CURRENT STATE
The current state is "FROZEN_ACCEPTANCE_COMPLETE_PLUS_UNRESOLVED".

AUTHORITY
The authority owner is "Terrynce White".

OWNER
The recorded roles are {"admitter":"Terrynce White","author":"Muse","executor":"Muse","proposer":"Terrynce White","verifier":"Muse"}.

FROZEN INVARIANTS
The frozen invariants are ["SPEC.md (pilot/06-pctdecode/SPEC.md) is frozen; implement to it, do not modify it.","Python 3 stdlib only; single file pctdecode.py.","The spec establishes %-sequence decoding only; form-encoding ('+' to space) semantics are not established and must not be assumed.","The 6 tests in tests/test_pctdecode.py are the acceptance check; no other correctness criterion."].

VERIFIED EVIDENCE
The verified facts and evidence references are [{"evidence":"pilot/06-pctdecode/evidence/probe-wellformed.txt sha256:7d915a9b66d56b6fcc9cdf186cf5d464328961182eca80e49f1263ac07472847","fact":"%XX decoding works in either hex case: probe shows %20 to space, %41 to A, %2f to /."},{"evidence":"pilot/06-pctdecode/evidence/probe-malformed.txt sha256:86852c6c9d45df6b98f1b4a9c696d2dce2d785f728a07ab58ae824d81e29fc2c; pilot/06-pctdecode/evidence/midtask-tests.txt sha256:27723e8d7b02696dcd360b1a73764518aac3dc060e2932de5d4348c598887db6","fact":"Malformed % currently aborts (BAD_ESCAPE, exit 1); the spec-required literal passthrough is the open remaining work."},{"evidence":"pilot/06-pctdecode/evidence/no-plus-evidence.txt sha256:7cb134ae1d22863308c689fcd08a6525bdab8417496d9c9aeb466ca3603643e6","fact":"No fixture, probe, or test exercises '+' behavior; the spec mentions '+' only to mark it unresolved."},{"evidence":"pilot/06-pctdecode/tests/test_pctdecode.py sha256:4e25387a3592dd43384fb9514feac2015af33b308f8400e1e62129267da647b7; pilot/06-pctdecode/evidence/no-plus-evidence.txt sha256:7cb134ae1d22863308c689fcd08a6525bdab8417496d9c9aeb466ca3603643e6","fact":"The 6 frozen tests contain no '+' case; passing them establishes nothing about '+' semantics."},{"evidence":"pilot/06-pctdecode/evidence/midtask-tests.txt sha256:27723e8d7b02696dcd360b1a73764518aac3dc060e2932de5d4348c598887db6","fact":"Partial implementation: 4/6 pass; malformed-% literal passthrough not implemented (test_malformed_left_literal and test_lone_percent_end fail)."},{"evidence":"successor branch codex/real-handoff-06-successor; independent local re-run 6/6 on 05c2af845d224efcaf41eb5058e24d3595cc4633; verification run 37170638939","fact":"Frozen acceptance tests: 6/6 PASS on the successor implementation."},{"evidence":"verification run 37170638939; independent local re-run 35/35 on 05c2af845d224efcaf41eb5058e24d3595cc4633","fact":"Handoff State tests: 35/35 PASS."},{"evidence":"git rev-parse 05c2af84^; git diff --name-only bc66ddbc..05c2af84; implementation review (no unquote_plus) — owner closeout verification 2026-10-03","fact":"Successor commit 05c2af845d224efcaf41eb5058e24d3595cc4633: parent exactly bc66ddbc4b6f8ed26c57e5df138cb1d0a634207d; changed only pilot/06-pctdecode/pctdecode.py; malformed '%' now emits literally with scanning continuing after '%'; existing %XX decoding preserved; urllib.parse.unquote_plus not used; '+' to space not implemented."},{"evidence":"pilot/06-pctdecode/tests/test_pctdecode.py sha256:4e25387a3592dd43384fb9514feac2015af33b308f8400e1e62129267da647b7; pilot/06-pctdecode/evidence/no-plus-evidence.txt sha256:7cb134ae1d22863308c689fcd08a6525bdab8417496d9c9aeb466ca3603643e6","fact":"Passing the six frozen tests establishes nothing about '+' behavior: no frozen test exercises '+'."},{"evidence":"pre-admission state hash sha256:398982ebfddaed95c2741ccedb1aa462c29fc642532403335854e6e89703814a matched the published hash; owner CLOSE order 2026-10-03 (recorded result)","fact":"Accepted state and transition history remained unchanged before owner admission; the unadmitted completion proposal (branch codex/real-handoff-06-proposal @ 4d224abcf42629df4bcc394ac1b65888e3221fcc) was rejected without advancing accepted state."}].

OPEN QUESTIONS
The open questions and owners are [{"owner":"Terrynce White","question":"Should '+' decode to space (form-encoding convention)? Unresolved; do not assume or implement."}].

FAILED / SUPERSEDED PATHS
The failed or superseded paths, classifications, and evidence references are [].

NEXT PERMITTED ACTION
The next permitted actions are [].

STOP CONDITIONS
The stop conditions are ["Do not modify the frozen SPEC.md.","Do not use urllib.parse.unquote_plus or otherwise decode '+' to space — the '+' semantic is unresolved and owner-owned.","Do not claim '+' behavior in code, comments, or docs.","Do not add dependencies; stdlib only, single file."].
