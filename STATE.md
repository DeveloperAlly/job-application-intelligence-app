# Career OS — State

Updated: 2026-09-08

## Campaign

Open-source, self-hostable career automation platform: job discovery → evidence matching → tailored application generation → approval → tracking → follow-up → learning.

## Current phase

**CONTROL PLANE BOOTSTRAP**

Phase 0 product-definition work is blocked until the persistent coordinator passes its end-to-end bootstrap test.

## Current gate

**Persistent coordinator operational**

Pass criteria:
- Herdr workspace starts in the repository.
- Coordinator agent starts successfully inside Herdr.
- Coordinator reads this state and governance before acting.
- Coordinator selects one eligible GitHub mission without human prompting.
- Coordinator dispatches one bounded worker or performs the bounded control mission itself.
- Completion evidence is written to GitHub/repo.
- Coordinator verifies evidence and updates canonical state.
- No dependent task advances while a systemic blocker is active.

## System blockers

- `BLOCKER-001`: Herdr runtime cannot be launched from ChatGPT's cloud environment. Local runtime bootstrap must be executed on the development machine once; after that the coordinator must own routine progression.

## Active objectives — WIP max 3

1. `CONTROL-001` — Install persistent Herdr coordinator runtime. **READY WHEN local prerequisites pass.**
2. `CONTROL-002` — Prove autonomous coordinator loop end-to-end. **BLOCKED by CONTROL-001.**
3. `P0-001` — Canonical product vision + problem definition. **BLOCKED by coordinator gate.**

## Completed control-plane evidence

- GitHub issue CRUD: PASS.
- GitHub file CRUD: PASS.
- GitHub branch creation: PASS.
- Repository control protocol: installed in `CLAUDE.md`.

## Human decisions required

None currently.

## Next transition

`CONTROL-001 PASS` → run `CONTROL-002` → if PASS, clear `BLOCKER-001`, advance to Phase 0 and dispatch up to three product-definition missions automatically.
