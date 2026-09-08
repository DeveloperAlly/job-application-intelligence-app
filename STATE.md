# Career OS — State

Updated: 2026-09-09

## Campaign

Open-source, self-hostable career automation platform: job discovery → evidence matching → tailored application generation → approval → tracking → follow-up → learning.

## Current phase

**CONTROL PLANE ACCEPTANCE**

## Current gate

**CONTROL-005 — Persistent coordinator acceptance**

Pass criteria:
- coordinator starts inside a Herdr-managed pane;
- reads `STATE.md`, campaign and governance;
- selects `P0-001` without human task selection;
- creates isolated worktree;
- dispatches bounded worker through native Herdr control;
- worker produces durable deliverables/evidence/PR;
- independent reviewer verifies;
- canonical state updates automatically;
- `P0-002` / `P0-003` become eligible and next work dispatches automatically;
- WIP is 1 before acceptance and 3 after acceptance;
- system blockers stop dependent work.

## System blockers

None in repository configuration.

## Active objective — WIP = 1 until acceptance

1. **CONTROL-005 / GitHub #4 — Persistent coordinator acceptance — READY FOR LOCAL RUN.**

## Completed control-plane work

- [x] Correct repo verified: `DeveloperAlly/job-application-intelligence-app`
- [x] PM state/campaign/governance/checklists installed
- [x] Phase 0 backlog + gate installed
- [x] Herdr 0.9.0 verified
- [x] GitHub CLI authenticated
- [x] Native Herdr control syntax captured
- [x] `ops/herdr-coordinator/herdr_dispatch.sh` added
- [x] coordinator patched to native Herdr dispatch
- [x] reviewer dispatch patched to native Herdr dispatch
- [x] obsolete `HERDR_DISPATCH_TEMPLATE` removed
- [x] `start.sh` simplified to native Herdr runtime
- [x] CONTROL-004 PASS / GitHub #3 closed

## Queued Phase 0 backlog

- **P0-001 / GitHub #5** — Canonical product vision + problem statement — first automatic mission.
- **P0-002 / GitHub #6** — Personas + JTBD — after control acceptance.
- **P0-003 / GitHub #7** — Scope + non-goals + metrics + principles + glossary — after control acceptance.
- **P0-GATE / GitHub #9** — human phase-gate approval after P0 missions verify.

## Human action required now

From the verified local repo:
1. `git pull`
2. start/attach Herdr with `herdr`
3. in a Herdr-managed shell pane at the repo root run `bash ops/herdr-coordinator/start.sh`

After that, routine PM progression must be autonomous.

## Human decisions required

None until a genuine product phase gate or non-resolvable blocker occurs.
