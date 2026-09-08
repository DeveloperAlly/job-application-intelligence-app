# CTRL-002 — Persistent Herdr Coordinator

## Outcome
Career OS project execution continues without this chat or the human manually shepherding workers.

## Architecture
- aDNA + GitHub: durable truth
- Herdr coordinator: persistent dispatch, recovery, verification
- worker agents: bounded implementation/product tasks
- reviewer agent: independent verification
- human: genuine product/architecture decisions and phase gates only

## Runtime
Canonical implementation: `ops/herdr-coordinator/`.

The orchestrator:
1. fails closed on missing dependencies or Herdr dispatch configuration;
2. seeds the first Phase 0 backlog;
3. enforces dependency/preflight/phase controls;
4. enforces WIP=1 until the first end-to-end control acceptance task is independently verified;
5. dispatches eligible work into Herdr-isolated worktrees;
6. dispatches independent review;
7. stops all downstream work on `system-blocker`;
8. raises WIP to 3 only after control acceptance passes;
9. then promotes the remaining Phase 0 work automatically.

## Acceptance gate
Not operational until P0-001 automatically progresses:

`eligible → Herdr worker → tests/evidence → PR → independent review → verified/closed → P0-002/P0-003 automatically ready/dispatched`.

## Current blocker
The repository-side bridge is built. The local Herdr installation must supply its exact agent-launch command once via `HERDR_DISPATCH_TEMPLATE`; the bridge deliberately does not guess unsupported CLI flags.
