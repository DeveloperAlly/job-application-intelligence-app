# CONTROL-001 — Install Persistent Herdr Coordinator Runtime

## Objective

Start a persistent Herdr workspace in this repository and launch a named coordinator agent that can read canonical state and manage downstream work.

## Preconditions

- macOS/Linux development machine.
- repository cloned locally.
- `herdr`, `gh`, `jq`, and one supported coding-agent CLI installed and authenticated.
- GitHub remote points to `DeveloperAlly/job-application-intelligence-app`.

## Inputs

- `CLAUDE.md`
- `STATE.md`
- `who/governance/coordinator.md`
- `how/campaigns/career-os.md`

## Allowed actions

- create Herdr workspace/panes;
- start coordinator agent;
- read repo/GitHub state;
- create/update bounded GitHub issues and repo state;
- dispatch worker agents after gate checks.

## Forbidden actions

- production feature code before build gates;
- destructive Git operations;
- changing product scope without human decision;
- advancing blocked/dependent missions;
- treating agent output as proof without repository verification.

## Acceptance criteria

1. Herdr workspace is created with repository cwd.
2. Named agent `career-coordinator` is detected by Herdr.
3. Agent receives the coordinator bootstrap prompt.
4. Agent reads `STATE.md` and reports current gate accurately.
5. Agent does not dispatch `P0-001` before `CONTROL-002` passes.
6. Evidence of the bootstrap is recorded in GitHub/repo.

## Verification

Run `scripts/bootstrap-herdr-coordinator.sh`, then inspect Herdr agent state and the evidence created by the coordinator.

## Completion evidence

Record in `STATE.md`:
- workspace created;
- coordinator agent detected;
- bootstrap prompt accepted;
- exact next mission selected.
