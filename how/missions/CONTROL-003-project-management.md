# CONTROL-003 — Canonical project management installed

## State
IMPLEMENTED — verification pending persistent coordinator runtime.

## Outcome
Make project status, phase sequence, gates, dependencies, WIP and next work durable and machine-readable so neither chat nor human memory is the project manager.

## Deliverables
- `STATE.md`
- `CLAUDE.md`
- `how/campaigns/career-os.md`
- `how/campaigns/career-os-checklist.md`
- `who/governance/coordinator.md`
- bounded mission files under `how/missions/`
- corresponding GitHub issues

## Controls
DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS

## Acceptance
- Current phase and gate are explicit.
- Full programme checklist exists.
- Current and next tasks are explicit.
- WIP and dependency rules are explicit.
- Human is not responsible for routine PM upkeep.
- Persistent coordinator can consume the state without chat context.
