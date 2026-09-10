> Historical local coordinator experiment. Do not use this as the active bootstrap guide. The [current state](../../STATE.md) and approved hosted architecture supersede the setup instructions below. Existing label/body checks have not proved protected authorization or duplicate-safe dispatch.

# Career OS Herdr Coordinator

Persistent bridge from GitHub/aDNA project state to local Herdr workers.

## Dispatch controls

An issue may run only when it has label `agent-ready` and contains:

```text
DEPENDENCIES_RESOLVED: true
PREFLIGHT: PASS
PHASE_GATE: PASS
```

`PREFLIGHT: N/A` is accepted where no external capability is involved.

Any open `system-blocker` stops all dispatch. WIP defaults to 3.

## One-time bootstrap

Prerequisites: `git`, authenticated `gh`, `herdr`, Python 3, local repo clone.

```bash
mkdir -p .career-os
cp ops/herdr-coordinator/herdr.env.example .career-os/herdr.env
# Set HERDR_DISPATCH_TEMPLATE once to the exact command supported by local Herdr.
bash ops/herdr-coordinator/bootstrap.sh
```

The bridge fails closed rather than guessing Herdr CLI flags.

## Persistent runtime

```bash
set -a; source .career-os/herdr.env; set +a
python3 ops/herdr-coordinator/coordinator.py daemon
```

## State flow

```text
agent-ready
→ gate/dependency/preflight checks
→ isolated agent/issue-N worktree
→ Herdr worker
→ tests/evidence + pushed branch + PR
→ agent-review
```

Workers must create `system-blocker` and stop on foundational failure.

## Acceptance gate

The coordinator is not operational until one real task runs end-to-end without manual shepherding:

```text
eligible issue
→ automatic dispatch
→ worker completion
→ tests/evidence
→ PR
→ review state
→ next eligible task selected
```
