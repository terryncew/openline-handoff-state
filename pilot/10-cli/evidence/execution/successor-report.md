REAL-HANDOFF-10 clean successor execution report

Starting main was verified through GitHub's git ref API as exactly
4b655c310c9cb8601a8d5de9f459b1cb45393a25 before inspecting task files or writing repository artifacts.

Pre-edit inference, derived from committed artifacts at the verified starting state:

- Exact starting commit: `4b655c310c9cb8601a8d5de9f459b1cb45393a25`, verified as `refs/heads/main`.
- Inferred operational task: complete REAL-HANDOFF-10 by adding the missing CI smoke workflow, actually running its CLI invocation, rerunning acceptance and regression suites, and proposing completion for owner review.
- Why this CLI exists: maintainers and CI need a mechanical command to verify whether a candidate is a valid admitted continuation of a frozen accepted state.
- Why it must wrap canonical `verify_closeout()`: verification, admission checks, evaluation, replay, rendering, history preservation, and explicit file permissions must remain single-sourced in canonical Python.
- Evaluator version: `0.1.1`; state schema: `openline.handoff-state.v0.1`.
- Current CLI interface: `python -m handoff verify-closeout`, requiring `--frozen-ref`, `--candidate-ref`, `--task-dir`, and `--owner`, with repeatable `--allow-implementation-changed` and `--allow-evidence-added`. It reads local git objects, prints stable JSON, and exits `0` for PASS, `1` for verification failure, or `2` for invalid invocation.
- Current implementation state: the CLI exists in `handoff/__main__.py`, builds the supplied explicit `Allowlist`, and calls `handoff.closeout.verify_closeout()`. Accepted task state is `MID_TASK_CLOSEOUT_CLI`, seq 1, hash `sha256:10a1bc1f1434afa833b1f8667bd95537d8271b030e66e14a223f82ffebd4be9a`. CI integration remains unfinished.
- Current frozen acceptance result: committed evidence records REAL-HANDOFF-10 **11/11 PASS**.
- Current Handoff State suite result: committed evidence records **48/48 PASS**, including historical replay compatibility. The REAL-HANDOFF-09 library suite records **11/11 PASS**. These are recorded starting results, not fresh successor executions.
- Exact remaining work: add a minimal CI workflow using the real REAL-HANDOFF-08 frozen ref `c45b3c611ecb496d6facc62643f0d685fe039f2a` and admitted closeout `bd58f07fdad7076783f3dffaa28ca1fa1b4060a0`; explicitly supply task directory `pilot/08-intervals`, owner `Terrynce White`, implementation allowance `pilot/08-intervals/intervals.py`, and evidence allowances `pilot/08-intervals/evidence/execution/canonical-python-preflight.txt` and `pilot/08-intervals/evidence/execution/closeout-ci-record.md`; require successful exit and valid JSON; actuate CI; rerun all required suites; record bounded evidence; prepare a successor implementation commit and an unaccepted completion proposal.
- Protected historical artifacts: frozen REAL-HANDOFF-10 SPEC and acceptance tests; canonical closeout and evaluator semantics; schemas; all accepted historical transition records; REAL-HANDOFF-08 freeze apparatus/evidence; REAL-HANDOFF-09 accepted history/evidence.
- Current `next_permitted_actions`: add the CI smoke; actuate it without weakening CLI, verifier, or tests; rerun the 11 CLI, 48 Handoff State, and 11 library tests plus replay compatibility and record evidence; report completion to Terrynce White, with any seq-2 admission requiring his explicit order.
- Stop conditions: do not change frozen SPEC/tests to pass; create a second verifier; infer permissions from the diff; modify protected history or evidence; alter schemas; add signatures or autonomous retry; start Stage 3; or self-admit.
- Admission authority: **Terrynce White alone**.

Permission may **not** be inferred from a git diff. The CLI may **not** implement its own admission semantics. `handoff/closeout.py` may **not** be weakened or bypassed. Accepted history may **not** be modified. Successful execution does **not** authorize self-admission of completion.

PRE-EDIT INFERENCE COMPLETE

Files inspected before PRE-EDIT INFERENCE COMPLETE:
- pilot/10-cli/handoff-state.json
- pilot/10-cli/handoff-transition.jsonl
- pilot/10-cli/HANDOFF.md
- pilot/10-cli/SPEC.md
- pilot/10-cli/evidence/test-results.txt
- pilot/10-cli/tests/test_closeout_cli.py
- handoff/__main__.py
- handoff/closeout.py
- handoff/core.py
- pilot/09-closeout-verifier/tests/test_closeout_verifier.py

Repository metadata inspected before that marker: main git ref and the exact starting commit's recursive tree (path/blob inventory). No PR descriptions, issue discussions, prior chat, or side-branch task artifacts were inspected.

Implementation:
- Successor branch: codex/real-handoff-10-clean-successor.
- Smallest implementation commit: a981dc89c36ebcccebf989e622e981db5fedd454.
- Parent: exact required starting commit.
- Only implementation change: new .github/workflows/closeout-cli-smoke.yml.
- All 140 existing starting blobs preserved, with no existing path deletion.
- Canonical implementation, evaluator v0.1.1, CLI, schemas, frozen 10 SPEC/tests, all accepted transition records, and all 08/09 apparatus/history/evidence unchanged.
- No dependencies, signatures, autonomous retry, or Stage 3 capability added.

Actual CI invocation:
```sh
python -m handoff verify-closeout \
  --frozen-ref c45b3c611ecb496d6facc62643f0d685fe039f2a \
  --candidate-ref bd58f07fdad7076783f3dffaa28ca1fa1b4060a0 \
  --task-dir pilot/08-intervals \
  --owner 'Terrynce White' \
  --allow-implementation-changed pilot/08-intervals/intervals.py \
  --allow-evidence-added pilot/08-intervals/evidence/execution/canonical-python-preflight.txt \
  --allow-evidence-added pilot/08-intervals/evidence/execution/closeout-ci-record.md \
  > closeout-cli-result.json
```

The workflow uses full-history checkout, existing Python 3.12 setup action, read-only contents permissions, the existing CLI, and explicit allowances copied from frozen committed tests. Bash fails on command failure; Python parses JSON and asserts required keys, passed=true, no failures, and successful file checks. It implements no admission or evaluator semantics.

CI evidence:
- Initial smoke run 37179243071, job 111368247549, implementation commit a981dc89c36ebcccebf989e622e981db5fedd454: SUCCESS.
- https://github.com/terryncew/openline-handoff-state/actions/runs/37179243071
- Tested environment: GitHub-hosted Ubuntu 24.04.5, CPython 3.12.14, Git 2.55.0.
- Frozen 10 acceptance: 11/11 PASS.
- Full Handoff State suite: 48/48 PASS, including both replay-compatibility tests.
- Existing 09 verifier suite: 11/11 PASS.
- Actual CLI JSON: passed=true, failures=[], file_checks=passed.
- No skipped replay checks observed.

Independent validation:
- Run 37179515007, job 111369038204, validation commit 9c5c6a78ea0567d94a194d505a2cae36f042d484: SUCCESS.
- https://github.com/terryncew/openline-handoff-state/actions/runs/37179515007
- Real 08 fixture through CLI: exit 0 and valid JSON PASS.
- Both explicit allowance categories work; omission of either is rejected, exit 1.
- Protected SPEC mutation in isolated temporary fixture repository: rejected, exit 1.
- Unlisted evidence addition in isolated temporary repository: rejected, exit 1.
- Wrong owner: rejected, exit 1.
- Malformed/unresolvable refs and malformed allowlist: invalid invocation, exit 2.
- Existing canonical verify_closeout() library: PASS and report agrees with CLI.
- Canonical replay: all 10 historical logs green.
- All 140 starting blobs unchanged in implementation and validation checkout.
- This independent harness invokes canonical code; it is execution evidence, not a second verifier.
- Validation-only .github/workflows/real-handoff-10-preflight.yml exists on validation/real-handoff-10-clean and is excluded from the successor branch's implementation/evidence commits.
- Peer static review found no authority bypass, actual admission, or real state/history writes.

Proposed completion:
- Full proposal: pilot/10-cli/proposals/completion/proposal.json.
- Admission remains {}.
- Proposed seq: 2.
- current_state: MID_TASK_CLOSEOUT_CLI -> COMPLETE_CLOSEOUT_CLI.
- claims: explicit from/to replacement bounded to cited commit, environment, fixture, and cases.
- verified_facts: append evidence-backed facts about existing canonical wrapper, real 08 CLI PASS, actual CI invocation, 11/48/11 passing suites, independent negative cases, and preserved historical artifacts.
- proposed_state_changes: mark the admitted remaining CI workflow work done with execution evidence.
- next_permitted_actions: owner review/admission only, with no recorded completion admission or Stage 3 authorization.
- Prior facts, questions, failed paths, invariants, goal, identifiers, authority and roles are preserved.
- No claims of general CI portability, networked verification, signatures, production hardening beyond tested cases, autonomous operation, or Stage 3 capability.

Canonical Python v0.1.1 preflight:
- Unadmitted proposal: REJECT, accepted state/hash unchanged.
- Unadmitted receipt verification: PASS.
- Rejection replay in deleted temporary log: PASS, no accepted-state advance.
- Fresh hypothetical exact-owner admission: ACCEPT.
- Hypothetical receipt verification: PASS.
- Hypothetical replay in deleted temporary log: PASS.
- Hypothetical resulting hash: sha256:1ebad6ba6589ee58595fd78aabbe4f9212b3e95fe5c1143a7b927ddca94ae5ba.
- Actual accepted seq remains 1.
- Actual accepted state/hash remains sha256:10a1bc1f1434afa833b1f8667bd95537d8271b030e66e14a223f82ffebd4be9a.
- No hypothetical admission record was persisted as an accepted transition.

Changed files on the successor branch, all new:
- .github/workflows/closeout-cli-smoke.yml
- pilot/10-cli/evidence/execution/independent-checks.py
- pilot/10-cli/evidence/execution/completion-preflight.py
- pilot/10-cli/evidence/execution/ci-smoke.json
- pilot/10-cli/evidence/execution/independent-verification.json
- pilot/10-cli/evidence/execution/completion-preflight.json
- pilot/10-cli/proposals/completion/proposal.json
- pilot/10-cli/evidence/execution/successor-report.md

Information outside committed repository artifacts:
- The current user experiment instruction supplied the repository, required starting SHA, reporting/validation constraints and remaining-work instruction. Operational task, authority, fixture refs, explicit allowances, and admission limits were independently recovered from committed state/SPEC/implementation/tests before editing.
- Tool capability/schema metadata showed GitHub repository and Actions read/write tools and no shell/Python runtime in this session. Execution therefore used actual GitHub Actions.
- GitHub API responses supplied live main/branch refs, tree inventories, new commit SHAs, branch-write confirmations, run IDs/status/conclusions, job IDs/steps and runner execution logs. Automatic checkout logs also exposed branch names, action/runner versions, checkout identity/author metadata and standard action warnings; none supplied task authority or requirements.
- Fresh test/subprocess output, independent preservation/replay results, generated proposal and canonical preflight receipts were new execution evidence. GitHub runner environment and runtime versions came from those logs.
- The supplied environment date/timezone and system/developer execution constraints are apparatus context, not task authority.
- Subagent review used only exact committed repository artifacts and this run's newly committed validation scripts; no predecessor context was provided.
- No PR or issue discussion, outside task document, user clarification, outside work order, or previous conversation was requested or used.
- Extra-context requests to user: NONE.

Run classifications, bounded to the recorded execution:
CONTEXT_ISOLATION: PASS
REAL_WORK_GENERALIZATION: PASS
OPERATIONAL_DOGFOOD: PASS

No merge, actual owner admission, accepted-state advance, or Stage 3 work occurred.
