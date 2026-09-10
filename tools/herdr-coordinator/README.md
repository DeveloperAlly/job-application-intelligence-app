> Historical local coordinator experiment. Do not use this as the active bootstrap guide. The [current state](../../STATE.md) and approved hosted architecture supersede the setup instructions below. Existing label/body checks have not proved protected authorization or duplicate-safe dispatch.

# Career OS Herdr Coordinator

Persistent execution bridge between aDNA/GitHub project state and local Herdr workers.

## State model

GitHub/aDNA are authoritative. The coordinator only dispatches issues carrying `agent-ready` **and** these body controls:

```text
DEPENDENCIES_RESOLVED: true
PREFLIGHT: PASS
PHASE_GATE: PASS
```

`PREFLIGHT: N/A` is accepted where no external/tool preflight is required.

A single open `system-blocker` stops all further dispatch.

## Labels

- `agent-ready` — eligible for dispatch
- `agent-running` — worker launched
- `agent-review` — worker completed and supplied evidence/PR
- `system-blocker` — foundational failure; dispatch stops
- `decision-required` — human product/architecture decision

WIP defaults to 3.

## One-time local bootstrap

Prerequisites: `git`, authenticated `gh`, `herdr`, Python 3, repo clone.

```bash
cp tools/herdr-coordinator/herdr.env.example .career-os/herdr.env
# Set HERDR_DISPATCH_TEMPLATE once to the exact command supported by the local Herdr CLI.
bash tools/herdr-coordinator/bootstrap.sh
```

The bridge intentionally does not guess Herdr CLI flags. If the local dispatch command is missing or invalid, bootstrap fails closed before project work is dispatched.

## Run persistently

```bash
set -a; source .career-os/herdr.env; set +a
python3 tools/herdr-coordinator/coordinator.py daemon
```

Commands:

```bash
python3 tools/herdr-coordinator/coordinator.py status
python3 tools/herdr-coordinator/coordinator.py once
python3 tools/herdr-coordinator/coordinator.py daemon
```

## Worker contract

For each eligible issue the coordinator:

1. checks systemic blockers and WIP;
2. verifies dependency/preflight/phase controls;
3. creates an isolated `agent/issue-N` git worktree;
4. creates `.career-os/TASK.md` containing the bounded issue packet;
5. changes `agent-ready` → `agent-running`;
6. invokes the configured Herdr dispatch command.

Workers are instructed to stop on foundational failure and create `system-blocker`. Successful workers must push the branch, create a PR, post test/evidence results, remove `agent-running`, and add `agent-review`.

## Acceptance test

The coordinator is operational only after one real issue passes:

```text
agent-ready
→ control checks PASS
→ Herdr worker launched
→ branch/worktree created
→ bounded task completed
→ tests/evidence recorded
→ PR created
→ agent-review
→ next eligible work dispatched
```

No agent self-report alone counts as Done.
