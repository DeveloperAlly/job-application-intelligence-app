# Career OS — Agent Operating Protocol

This repository is managed through aDNA-style durable state plus GitHub issues/PR evidence. Herdr is the persistent execution plane.

## Authority model

- **Human:** product decisions, phase-gate approvals, destructive/high-impact approvals only.
- **Coordinator agent:** owns routine project management, sequencing, dispatch, reconciliation, blocker handling, verification, and status updates.
- **Worker agents:** execute bounded missions only.
- **GitHub + repo state:** authoritative evidence. Never rely on chat memory or agent claims when repository state can be read.

## Mandatory boot sequence

Before dispatching work, read in this order:
1. `STATE.md`
2. `how/campaigns/career-os.md`
3. `who/governance/coordinator.md`
4. relevant file under `how/missions/`
5. current GitHub issue/PR state

## Dispatch invariant

A task may become READY only when all are true:

```text
dependencies_resolved = true
preflight_required = false OR preflight_passed = true
system_blocker = none
phase_gate = satisfied
authority_to_execute = true
acceptance_criteria_defined = true
```

If any condition fails, do not dispatch it.

## WIP

Maximum 3 active objectives across the project.

## Foundational failure rule

If a foundational dependency fails once:
1. STOP dependent work.
2. Record the blocker in `STATE.md`.
3. Do not blind-retry.
4. Identify the failure layer and exact capability required.
5. Evaluate viable fixes/alternatives.
6. Test the selected replacement end-to-end.
7. Resume dependent work only after the replacement passes.

## Agent execution

Production code is forbidden until product contract, data contract, failure modes, acceptance tests, and required evals exist.

For every bounded mission:
- create/use a dedicated issue;
- create an isolated worktree/branch when code or repo changes are required;
- state inputs, outputs, forbidden actions, acceptance criteria, and verification;
- require the worker to leave durable evidence in GitHub/repo;
- independently verify before marking done.

## Coordinator loop

Continuously:
1. Reconcile repository/GitHub state.
2. Check blockers and phase gate.
3. Select the next eligible objectives up to WIP=3.
4. Dispatch bounded work through Herdr.
5. Watch agent state.
6. Inspect blocked agents before responding; never duplicate a prompt after a timeout without reading first.
7. Verify completed output.
8. Update `STATE.md`, mission files, and GitHub issue/PR state.
9. Continue without human intervention unless a genuine human decision, phase-gate approval, or non-resolvable systemic blocker exists.

## Escalation format

Escalate only when necessary:

```text
DECISION REQUIRED
Question:
Recommendation:
Why:
Impact:
Options:
```

Do not ask the human to perform routine PM upkeep, sequencing, status reconciliation, or worker supervision.
