SCHEMA
The state schema is "openline.handoff-state.v0.1".

TASK ID
The task identifier is "REAL-HANDOFF-07".

GOAL
The goal is "Complete stats: stdin numbers to JSON summary per the frozen SPEC.md; all 6 acceptance tests passing.".

CLAIMS
The recorded claims, bases, and ceilings are [{"basis":"5/6 pass; test_bad_input is the defined gap; SPEC.md Errors section.","ceiling":"No claim about malformed-line behavior beyond the defined BAD_INPUT work; no claim beyond the tested inputs.","claim":"Count and sum are computed correctly for valid inputs; input validation (BAD_INPUT) is the remaining work."}].

CANONICAL TERMS
The canonical terms and definitions are {"BAD_INPUT":"nonzero exit with BAD_INPUT on stderr for a non-empty line that is not a decimal number.","SUMMARY":"a JSON object with count (number of values) and sum (arithmetic sum; 0 for empty input)."}.

PROPOSED STATE CHANGES
The proposed state changes are [].

IDENTIFIERS
The identifiers are {"dates":{"closeout":"2026-10-03","spec_frozen":"2026-10-03"},"paths":{"task_dir":"pilot/07-stats"},"receipts":{},"shas":{"midtask_tests":"6ce73f81567731f4b88f0d6ae9f3ced16e00a5ae7a16c5e8c4968efcfef93428","owner_decision":"ee71eafdee59d3bd3450f7c7852e71fc04dcc8e5cf3680e888638b54807f166a","seq1_handoff":"8cc8de45b4dd5e76275a7e931186644f60441575ea2b5362f14a9f7f1434a53d","seq1_impl":"4428c28a107a30de5444fb425af5fd2fefba144bf961082a395f6fc808934bf0","seq1_tests":"6e957f1b61d643af5a955475fef2f2a9b146094a3a78143cef6904e5f38f69d5","spec":"0b8936a41ee8b127dbff7873a836e50b4a5f2a9d0508090f13b2472759054f3a","stats_py":"e2862b0b4c64661b7c650be8726c9f072d42a5ed3c2e4c952b4137dd1885414d","stats_py_completed":"6cd3d86719dd220fd92e4ca8ef37ef3809780256f7df1a3828564b99d31e8174","successor_commit":"f180534aac379d7b4e08367b88dda8d034aaf820","tests":"94488166fc83c3f1de60d9ace2d3198ddd4898e3a8e1da5e84b12cdd0d7805cd"},"versions":{"python":"3","schema":"openline.handoff-state.v0.1"}}.

CURRENT STATE
The current state is "COMPLETE_STRICT_INPUT".

AUTHORITY
The authority owner is "Terrynce White".

OWNER
The recorded roles are {"admitter":"Terrynce White","author":"Muse","executor":"Muse","proposer":"Terrynce White","verifier":"Muse"}.

FROZEN INVARIANTS
The frozen invariants are ["SPEC.md (pilot/07-stats/SPEC.md) is frozen; implement to it, do not modify it.","Python 3 stdlib only; single file stats.py.","The 6 tests in tests/test_stats.py are the acceptance check; no other correctness criterion."].

VERIFIED EVIDENCE
The verified facts and evidence references are [{"evidence":"pilot/07-stats/SPEC.md sha256:0b8936a41ee8b127dbff7873a836e50b4a5f2a9d0508090f13b2472759054f3a","fact":"SPEC.md frozen."},{"evidence":"pilot/07-stats/evidence/seq1-implementation.py sha256:4428c28a107a30de5444fb425af5fd2fefba144bf961082a395f6fc808934bf0","fact":"Action A authorized: accept one number per line and comma-separated values per line; broad input handling implemented."},{"evidence":"pilot/07-stats/evidence/seq1-midtask-tests.txt sha256:6e957f1b61d643af5a955475fef2f2a9b146094a3a78143cef6904e5f38f69d5","fact":"Partial A: 5/6 pass on the frozen tests; the BAD_INPUT path is open (test_bad_input fails)."},{"evidence":"pilot/07-stats/tests/test_stats.py sha256:94488166fc83c3f1de60d9ace2d3198ddd4898e3a8e1da5e84b12cdd0d7805cd; pilot/07-stats/evidence/seq1-midtask-tests.txt sha256:6e957f1b61d643af5a955475fef2f2a9b146094a3a78143cef6904e5f38f69d5","fact":"The 6 frozen tests use one-per-line inputs; both broad and strict input handling satisfy them — the tests alone do not discriminate the authorized input scope."},{"evidence":"pilot/07-stats/evidence/owner-decision.md sha256:ee71eafdee59d3bd3450f7c7852e71fc04dcc8e5cf3680e888638b54807f166a","fact":"Owner decision 2026-10-03: input is strictly one decimal number per line; comma-separated values are not authorized; malformed lines go to BAD_INPUT."},{"evidence":"pilot/07-stats/evidence/owner-decision.md sha256:ee71eafdee59d3bd3450f7c7852e71fc04dcc8e5cf3680e888638b54807f166a; this seq-2 transition","fact":"Seq-1 action A (comma-separated acceptance) superseded; recorded under failed_or_superseded_paths. Seq 1 (hash sha256:2a2eadac…) remains valid history; it is not current."},{"evidence":"pilot/07-stats/evidence/midtask-tests.txt sha256:6ce73f81567731f4b88f0d6ae9f3ced16e00a5ae7a16c5e8c4968efcfef93428","fact":"Partial B: strict one-per-line parsing, no comma splitting; 5/6 pass; BAD_INPUT handling not yet implemented (test_bad_input fails with ValueError)."},{"evidence":"successor branch codex/real-handoff-07-successor; independent local re-run 6/6 on f180534aac379d7b4e08367b88dda8d034aaf820; validation/preflight runs 37172166950, 37172486041","fact":"Frozen acceptance tests: 6/6 PASS on the successor implementation."},{"evidence":"runs 37172166950, 37172486041; independent local re-run 35/35 on f180534aac379d7b4e08367b88dda8d034aaf820","fact":"Handoff State tests: 35/35 PASS."},{"evidence":"git rev-parse f180534a^; git diff --name-only 9a90030e..f180534a; implementation review — owner closeout verification 2026-10-03","fact":"Successor commit f180534aac379d7b4e08367b88dda8d034aaf820: parent exactly 9a90030e31ae0387b62acb96f7bb868e9798d91e; changed only pilot/07-stats/stats.py; strict one-per-line parsing retained; comma-containing input rejected with BAD_INPUT (nonzero exit); BAD_INPUT implemented for malformed lines; no comma splitting revived."},{"evidence":"recorded result STALE_STATE_RESISTANCE: PASS; pre-admission head hash matched sha256:90d45538…","fact":"Seq 2 (sha256:90d45538…) remained the authoritative head throughout successor execution; the successor reconstructed the accepted chain, identified the hash-linked latest head as current authority, and did not revive seq-1 broad-input authority."},{"evidence":"pre-admission state hash sha256:90d4553808ac86b086fd26086f3a405c8430dee58404333f656d50838d80b587 matched the published hash; owner CLOSE order 2026-10-03 (recorded result)","fact":"Accepted state and transition history unchanged before owner admission; the unadmitted completion proposal (branch codex/real-handoff-07-completion-proposal @ 894c66edd31969719643bb97aabaa572120f2828) was rejected without advancing accepted state."}].

OPEN QUESTIONS
The open questions and owners are [{"owner":"Terrynce White","question":"Should stats offer a --pretty output flag? Out of scope unless the owner approves; do not implement."}].

FAILED / SUPERSEDED PATHS
The failed or superseded paths, classifications, and evidence references are [{"classification":"superseded — owner decision 2026-10-03: strictly one number per line; comma-separated values not authorized","evidence":"pilot/07-stats/evidence/owner-decision.md","path":"comma-separated input acceptance (seq-1 action A; evidence/seq1-implementation.py)"}].

NEXT PERMITTED ACTION
The next permitted actions are [].

STOP CONDITIONS
The stop conditions are ["Do not modify the frozen SPEC.md.","Do not add dependencies; stdlib only, single file."].
