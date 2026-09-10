# Career OS — State

Updated: 2026-09-10. Reconciled pending local work with GitHub main through `5c58e6b`.

## Current direction

The owner approved the reusable PM hosting architecture and requested publication/reconciliation. The system uses aDNA operating records versioned in GitHub, a Sliplane coordinator and private Herdr execution, Cloudflare, and Desktop Commander tools. The reusable PM implementation belongs in `DeveloperAlly/agent-governance`; Career OS is the product trial.

## Authority and source locations

- Product intent and accepted product constraints: `what/context/product-contract.md` and `what/decisions/0001-career-os-product-contract.md`.
- Requirement IDs and acceptance criteria: `pm/03-requirements.md`. Its R-001–R-116 import preserves the older campaign register; the campaign Markdown/HTML are historical views.
- Product design, data/interface contracts, evals and decisions: `pm/03-*`, `pm/05-*`.
- Campaign and phase sequence: `how/campaigns/career-os.md` and `how/programme.json`.
- Proposed implementation task details: `pm/06-tasks.yaml`. These are not a competing runtime task registry; task-to-programme mapping and acceptance reconciliation remain required before dispatch.
- Current status and next action: this file. Other status pages link here.

Explicit owner instructions determine authorization. Versioned decisions record it; tests and runtime observations establish what actually worked. Neither a historical status label nor a chat summary proves execution.

## Current gate and next action

**CONTROL-005 / hosted coordinator acceptance remains unverified.** Architecture approval is recorded in the governance repository; it is not runtime or Career OS product acceptance.

Current task: publish the reconciled repositories. Next: prove bounded hosted Herdr dispatch, independent verification, restart recovery, usage limits and Desktop Commander access boundaries. Keep WIP at one until control acceptance. Product dispatch remains held behind its required phase gates; do not start either historical local coordinator from old bootstrap instructions.

## Preserved implementation and evidence

The repository contains pending work now captured in Git: evidence ingestion, job-ad intake/extraction, PDF rendering, matching tests and PM contracts. Publication preserves this work; it does not retroactively approve its original build sequence or establish a finished product. See `how/publication-reconciliation-2026-09-10.md` for validation and remaining integration gaps.

## Historical local control observations

The following checklist is retained from the earlier local attempt. Its checkmarks are historical assertions, not acceptance of the hosted system.


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
