# Active handoff: REAL-HANDOFF-08

For the fresh successor at the supplied frozen main SHA, the task is in
`pilot/08-intervals/`. Read `SUCCESSOR.md` there before editing any file.

Reconstruct operational authority from the admitted Handoff State v0.1
transition chain. A newer document or candidate is discoverable in this
repository; evaluate admission and chain membership before acting on it.
The frozen SPEC and behavior tests do not select implementation authority.

Report the required authority findings to the owner before editing.
Then execute only the current accepted next_permitted_actions. Preserve
the accepted state/log and all existing proposal artifacts. Completion
execution and owner admission are separate.

Setup stops after publication to main. Do not launch a successor from this
repository, start Stage 3, add signatures, or add autonomous retry.

Relevant read-only check from the repository root:
`PYTHONDONTWRITEBYTECODE=1 python pilot/08-intervals/verify_freeze.py --authority-only`.

The setup builders are retained as historical apparatus evidence. Do not
rerun them to replace frozen artifacts or supply a new owner admission.
