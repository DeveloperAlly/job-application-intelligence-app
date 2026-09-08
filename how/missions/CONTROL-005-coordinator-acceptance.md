# CONTROL-005 — Persistent coordinator acceptance test

## State
BLOCKED by CONTROL-004.

## Outcome
Prove the PM system runs itself without chat or human shepherding.

## Acceptance flow

```text
coordinator daemon starts
→ reads STATE/governance
→ seeds/reconciles backlog
→ selects P0-001
→ creates isolated worktree
→ dispatches Herdr worker
→ worker produces deliverables + tests/evidence + PR
→ independent reviewer runs
→ issue verified/closed
→ canonical state reconciles
→ P0-002/P0-003 become eligible
→ next work dispatches automatically
```

## Pass criteria
- No human selects the next task.
- No human checks whether the worker finished.
- No human updates task state.
- System blocker stops dependents.
- WIP is 1 before acceptance and 3 after acceptance.
- GitHub/aDNA evidence reflects reality.

## Failure rule
Any failure creates a systemic blocker and the acceptance test remains failed until root cause is resolved and the entire flow is re-proven.
