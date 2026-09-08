# Career OS — State

Updated: 2026-09-08

## Campaign

Open-source, self-hostable career automation platform: job discovery → evidence matching → tailored application generation → approval → tracking → follow-up → learning.

## Current phase

**CONTROL PLANE BOOTSTRAP**

Phase 0 product-definition work is queued but blocked until the persistent coordinator passes its end-to-end acceptance test.

## Current gate

**Persistent coordinator operational**

Pass criteria:
- local Herdr runtime identified and supported dispatch syntax confirmed;
- coordinator daemon starts in the correct repository;
- coordinator reads `STATE.md`, campaign and governance before acting;
- coordinator selects `P0-001` without human prompting;
- coordinator dispatches a bounded worker;
- worker produces durable deliverables/evidence/PR;
- independent reviewer verifies the result;
- canonical state is updated automatically;
- `P0-002` / `P0-003` become eligible and the next work dispatches automatically;
- no dependent task advances while a systemic blocker is active.

## System blocker

`BLOCKER-001` — ChatGPT cannot inspect or execute the user's local Herdr binary. The exact local CLI syntax must be captured once from the development machine. This is the only current human-only runtime step.

## Active objectives — WIP = 1 until acceptance

1. **CONTROL-004 / GitHub #3 — Herdr local preflight — HUMAN-ONLY LOCAL STEP REQUIRED NOW.**
2. **CONTROL-005 / GitHub #4 — Persistent coordinator acceptance — BLOCKED by CONTROL-004.**

## Queued Phase 0 backlog

- **P0-001 / GitHub #5** — Canonical product vision + problem statement — queued as control-acceptance mission.
- **P0-002 / GitHub #6** — Personas + JTBD — blocked until control acceptance.
- **P0-003 / GitHub #7** — Scope + non-goals + metrics + principles + glossary — blocked until control acceptance.
- **P0-GATE** — product-definition phase approval — blocked until P0-001/002/003 are independently verified.

## Project-management artifacts installed

- [x] `CLAUDE.md` — coordinator operating protocol
- [x] `who/governance/coordinator.md` — persistent PM governance
- [x] `how/campaigns/career-os.md` — campaign/outcome/phase sequence
- [x] `how/campaigns/career-os-checklist.md` — complete gated programme checklist
- [x] `how/PM_STATUS.md` — concise PM status entrypoint
- [x] `how/REPORT_TEMPLATE.md` — mandatory coordinator report format
- [x] bounded mission files under `how/missions/`
- [x] GitHub issues for current control work and Phase 0 backlog
- [x] `ops/herdr-coordinator/` bridge implementation
- [ ] exact local Herdr dispatch syntax wired into bridge
- [ ] persistent coordinator daemon running
- [ ] autonomous end-to-end acceptance passed

## Human action required now

From the root of the local clone of `DeveloperAlly/job-application-intelligence-app`, run exactly:

```bash
printf '\n=== HERDR VERSION ===\n'
herdr --version || true
printf '\n=== HERDR AGENT START HELP ===\n'
herdr agent start --help || true
printf '\n=== HERDR AGENT PROMPT HELP ===\n'
herdr agent prompt --help || true
printf '\n=== HERDR PANE RUN HELP ===\n'
herdr pane run --help || true
printf '\n=== GH AUTH ===\n'
gh auth status
printf '\n=== REPO ===\n'
gh repo view --json nameWithOwner --jq .nameWithOwner
```

Paste the complete output into the coordinator chat.

## Next automatic transition

After that output is supplied:
1. update the bridge to the exact local Herdr CLI syntax;
2. remove the placeholder dispatch-template requirement;
3. provide one final local bootstrap command;
4. start the persistent coordinator;
5. run CONTROL-005 end-to-end;
6. if PASS, clear `BLOCKER-001`, set WIP=3, advance to Phase 0, and dispatch P0-001/002/003 automatically.

## Human decisions required

None.
