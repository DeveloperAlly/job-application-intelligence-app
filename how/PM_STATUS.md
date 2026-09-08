# Career OS — PM Status

## Current phase
CONTROL PLANE BOOTSTRAP

## Current gate
Persistent coordinator operational.

## Active WIP
1. CONTROL-004 — Herdr local preflight — HUMAN-ONLY LOCAL STEP REQUIRED
2. CONTROL-005 — Coordinator acceptance — BLOCKED by CONTROL-004

## Ready after gate
- P0-001 — Vision + problem
- P0-002 — Personas + JTBD
- P0-003 — Scope + non-goals + metrics + principles + glossary

## Human-only step
From the local repo root, run the command in `how/missions/CONTROL-004-herdr-local-preflight.md` and paste the complete output into the coordinator chat.

## Automatic continuation after that
The coordinator bridge is updated to the exact local Herdr CLI syntax, then the persistent daemon is started and CONTROL-005 runs end-to-end. If it passes, WIP becomes 3 and Phase 0 dispatch begins automatically.
