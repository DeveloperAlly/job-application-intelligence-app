# Career OS Autonomous Project Management

This document specifies the target PM operating contract. The hosted control plane is not yet accepted; current evidence and next action live in [STATE.md](STATE.md). Explicit owner directions in chat can authorize work; the coordinator must record those decisions against their scope. Conversation is not a substitute for durable runtime evidence.

## Control architecture

- **aDNA** — durable institutional memory: product intent, decisions, standards, missions, governance, runbooks, patterns, agent roles.
- **Programme Registry** — executable task graph: phases, stable task IDs, dependencies, gates, acceptance, evidence, scope.
- **Coordinator with Herdr execution** — target persistent runtime: reconcile, dedupe, build context contracts, dispatch workers/reviewers, monitor, recover, update state, notify, unlock next work.
- **GitHub Issues / PRs / CI** — durable task evidence and audit trail.
- **GitHub Project: Career OS — Mission Control** — human control surface only; a projection of canonical state.

## Truth ownership

| Truth | Authority |
|---|---|
| Product intent | aDNA what/ |
| Decisions | aDNA decision registry |
| Standards / governance | aDNA how/ |
| Agent roles / authority | aDNA who/ |
| Campaigns / missions | aDNA |
| Full work graph | Programme Registry |
| Runtime task state | GitHub records written through the coordinator; Herdr supplies execution observations |
| Code | Git |
| Evidence | GitHub issue / PR / CI |
| Human approval | Gate record |
| Visual status | Required control panel and chat; GitHub Project can be an additional projection |
| Failures / learning | Failure Registry |

## Task state machine

`BACKLOG -> READY -> RUNNING -> REVIEW -> APPROVAL -> DONE`

Exception states: `BLOCKED`, internal `STALLED`.

No actor may invent transitions. The coordinator is the only PM-state writer.

## Phase state machine

`LOCKED -> ACTIVE -> GATE_READY -> COMPLETE`

The next phase cannot become ACTIVE until the previous human gate is approved where required.

## Dispatch invariants

A task may become READY only if all are true:

- dependencies are complete
- active phase permits the task
- required context exists
- acceptance criteria exist
- authority is valid
- no systemic blocker exists
- duplicate/equivalent work does not already exist

A task may become RUNNING only if:

- an execution lease is available
- context is current
- agent capability matches task type
- allowed/forbidden scope is explicit

A task may become DONE only if:

- deliverables exist
- acceptance checks pass
- required tests/evals pass
- evidence is recorded
- independent reviewer passes
- canonical state is reconciled

## Reusable knowledge rule

Reusable instructions are created once and referenced forever. Do not duplicate standards, architecture, governance, runbooks, skills, or role contracts into task prompts.

## Context Compiler

Every worker/reviewer receives a minimal Task Execution Contract containing only:

- task ID / issue
- role
- current phase / gate
- programme/context versions
- required canonical references
- required reusable skills
- allowed / forbidden scope
- acceptance reference
- required return schema

Agents do not rely on chat history.

## Duplicate-work prevention

Before dispatch the coordinator must check:

1. stable task ID registry
2. equivalent outcome fingerprint
3. open issues
4. active branches / PRs
5. existing deliverables
6. existing patterns / runbooks

Allowed outcomes: `CREATE`, `CONTINUE`, `REUSE`, `WAIT`, `REJECT_DUPLICATE`.

## Execution leases and concurrency

Only one active lease may exist per task. WIP is dependency-aware, not random parallelism.

Before parallel dispatch, check:

- overlapping files/domains
- shared unresolved decisions
- schema conflicts
- context-changing dependencies

Allowed concurrency results: `SAFE_PARALLEL`, `SERIALISE`, `WAIT_FOR_DECISION`.

## Drift controls

Review must reject work that violates:

- task scope
- canonical decisions
- architecture contracts
- current phase restrictions
- approved dependency model

## Context freshness

Every execution records:

- programme version
- context version
- decision-set hash
- standards version
- generated timestamp

If relevant canonical context changes before review, the task must be revalidated or rebased before completion.

## Failure and learning loop

Every non-trivial failure is classified and persisted. Minimum taxonomy:

`SPEC_GAP`, `CONTEXT_MISS`, `DEPENDENCY_ERROR`, `DUPLICATE_WORK`, `SCOPE_DRIFT`, `IMPLEMENTATION_DEFECT`, `TEST_GAP`, `EVAL_FAILURE`, `REVIEW_FAILURE`, `TOOL_FAILURE`, `ENVIRONMENT_FAILURE`, `STATE_DIVERGENCE`, `NOTIFICATION_FAILURE`, `COST_OVERRUN`.

Flow:

`failure -> classify -> root cause -> search known pattern/runbook -> reuse or fix -> detect recurrence -> promote to pattern/runbook/standard/skill/invariant`

Recurring problems must not be rediscovered by future agents.

## Reconciliation and recovery

Every reconciliation cycle compares programme state, GitHub issues, PRs, Git, CI, Herdr agents, leases, review state and evidence.

Examples:

- issue RUNNING + no live/recoverable agent -> STALLED
- issue DONE + no reviewer PASS -> restore REVIEW
- PR merged + task RUNNING -> verification reconciliation
- agent without lease -> orphan process
- lease without agent -> orphan task

Coordinator restart must reconstruct durable state and resume idempotently without duplicate dispatch.

## Human notifications

Notify the human only for significant events:

- task VERIFIED
- approval required
- stalled task
- blocker
- reviewer rejection
- phase gate ready
- system failure

Routine state is visible in the control panel. The approved experience also requires proactive chat updates and a scheduled daily briefing; the hosted scheduler generates these independently of client sessions.

## Human role

Human intervention is limited to:

1. phase gates
2. genuine product/architecture decisions
3. destructive/security-sensitive approvals
4. unrecoverable blockers
5. optional reprioritisation

The human does not manually dispatch agents, reconcile state, chase reviewers, or maintain PM state.

## Efficiency controls

- reference canonical docs instead of repeating them
- cache unchanged context by hash
- reuse prior analysis and known patterns
- route models by task class
- enforce retry ceilings
- record retries/context size/cost where available
- do not spawn agents for deterministic work

## Required runtime components

- Programme Engine
- Task Registry
- Context Registry
- Decision Registry
- Standards Registry
- Pattern / Runbook Registry
- Failure Registry
- Dependency Engine
- Gate Engine
- Dedupe Engine
- Context Compiler
- Lease / Conflict Manager
- Herdr Dispatcher
- Agent State Monitor
- Reviewer Dispatcher
- Drift Detector
- Definition-of-Done Engine
- Evidence Validator
- Failure / Recurrence Engine
- State Reconciler
- GitHub Project Sync
- Notification Manager
- Heartbeat Publisher
- Recovery Engine

## Acceptance

This control plane is NOT accepted until `PM_ACCEPTANCE.md` passes end-to-end, including cold-agent, duplicate-work, stale-context, restart, divergence, notification, gate, recurrence-learning and chaos tests.
