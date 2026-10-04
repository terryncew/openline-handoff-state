# REAL-HANDOFF-10 — operational CLI for the closeout verifier (frozen spec, 2026-10-04)

## Problem
REAL-HANDOFF-09 produced reusable canonical Python tooling
(`handoff/closeout.py`, `verify_closeout()`) that answers "is this candidate
state a valid admitted continuation of the frozen accepted state?" It is
currently a library interface. A maintainer or CI job has no mechanical way
to invoke it. The accepted REAL-HANDOFF-09 state retains the owner-owned
open question of a CLI entry point; the owner approved resolving it YES.

## Task
Build a small, reusable command-line interface around the canonical Python
v0.1.1 closeout verifier. Do not create a second verifier: the CLI must call
the existing `verify_closeout()` implementation. Keep scope narrow. No new
dependencies.

## Interface
`python -m handoff verify-closeout` (subcommand of the existing
`handoff/__main__.py` CLI surface), with:

- `--frozen-ref` (required): git ref of the frozen starting state
- `--candidate-ref` (required): git ref of the candidate closeout
- `--task-dir` (required): repository-relative task directory
  (e.g. `pilot/08-intervals`)
- `--owner` (required): exact authority owner (e.g. `Terrynce White`)
- `--allow-implementation-changed` (repeatable): repo-relative paths of
  retained files the closeout legitimately changed
- `--allow-evidence-added` (repeatable): repo-relative paths of new
  evidence files the closeout legitimately added

## Required behavior
1. Load from the two refs, using only local git object reads (no network):
   frozen/candidate `handoff-transition.jsonl` text,
   frozen/candidate `handoff-state.json` (parsed),
   and the complete file trees under `--task-dir` at each ref
   (repo-relative path -> bytes).
2. Build the explicit `Allowlist` exactly as supplied — distinguishing
   `implementation_changed` from `evidence_added` — and pass it unchanged
   to `verify_closeout()`. Permission is never inferred from the diff.
3. Invoke canonical `verify_closeout()`; do not duplicate admission,
   evaluation, replay, or rendering semantics.
4. Print stable machine-readable JSON to stdout with at least:
   `passed`, `failures` (check names + details), `checks_run`,
   `file_checks`, `frozen_ref`, `candidate_ref`, `task_dir`,
   `authority_owner`.
5. Exit codes: `0` = verification PASS; `1` = verification ran and failed;
   `2` = invalid invocation (bad arguments, unresolvable ref, unreadable
   inputs, malformed allowlist usage).
6. Must verify the real REAL-HANDOFF-08 fixture:
   frozen `c45b3c611ecb496d6facc62643f0d685fe039f2a`,
   legitimate closeout `bd58f07fdad7076783f3dffaa28ca1fa1b4060a0`.
7. Must reject representative unauthorized cases: protected-file mutation,
   unlisted added file, wrong authority owner, invalid admitted
   continuation.

## Non-goals / prohibitions
- No special-case logic for REAL-HANDOFF-08; the fixture is data, not code.
- No admission authority: the CLI verifies; it never admits, appends, or
  modifies accepted state/history.
- No inferred allowances; no schema changes; no signatures; no retry.
- Do not modify `handoff/closeout.py` semantics, evaluator v0.1.1
  semantics, historical transition records, the 08 freeze apparatus, or
  the 09 accepted history/evidence.

## Acceptance (frozen, `pilot/10-cli/tests/test_closeout_cli.py`)
POSITIVE:
- legitimate 08 frozen start -> admitted closeout: PASS, exit 0
- explicit `implementation_changed` allowance works
- explicit `evidence_added` allowance works
- output is valid machine-readable JSON with the required keys
NEGATIVE:
- protected-file mutation rejected (nonzero, passed=false)
- unlisted new file rejected
- incorrect authority owner rejected
- malformed/nonexistent ref rejected cleanly (exit 2)
- malformed allowlist usage rejected cleanly (exit 2)
- verification failure exits nonzero (exit 1)
REGRESSION:
- full Handoff State suite green
- existing `verify_closeout()` library behavior green
- repository-wide historical replay compatibility green
