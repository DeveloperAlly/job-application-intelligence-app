# Persistent Coordinator Governance

## Purpose

Provide a project manager that persists independently of any chat session and advances Career OS without requiring the human to babysit state or workers.

## Canonical truth

Explicit owner instructions govern authorization; versioned decisions record the approved scope. GitHub/repository evidence establishes implementation facts. `STATE.md` names current work and links its evidence; campaign and mission documents describe intent and scope. Agent output and chat summaries cannot turn an unverified outcome into acceptance.

The approved hosting direction is Sliplane coordinator/private Herdr execution with Cloudflare and Desktop Commander. Earlier local coordinator scripts remain unaccepted experiments. Herdr lifecycle observations are not an independent writable project-state authority.

## Responsibilities

The coordinator owns:
- state reconciliation;
- dependency checks;
- mission selection;
- WIP enforcement;
- Herdr worker dispatch;
- worker monitoring;
- failure classification;
- verification;
- issue/PR/state updates;
- automatic continuation to the next eligible mission.

The human does **not** own routine project management.

## Human-only authority

Escalate only for:
- material product-direction decisions with legitimate alternatives;
- phase-gate approval;
- destructive or irreversible operations;
- credentials/account actions only the human can perform;
- systemic blockers the coordinator cannot safely resolve.

## No-babysitting rule

The coordinator must not ask the human:
- what task is next when canonical state can determine it;
- whether an agent finished when Herdr/GitHub can determine it;
- to update issue/state metadata;
- to retry a recoverable command;
- to summarize prior project context already in the repository.

## Failure classification

Before retrying a failed dependency, classify it as one of:
- capability absent;
- permission/authentication;
- configuration;
- environment/runtime;
- malformed input;
- transient service failure;
- implementation defect;
- unknown.

For unknown/systemic failures: block dependents, investigate, then prove the fix end-to-end before resuming.

## Completion standard

A mission is complete only when:
- required artifact exists;
- acceptance criteria pass;
- verification evidence is recorded;
- dependent state is reconciled;
- GitHub issue/PR reflects reality;
- `STATE.md` reflects reality.

## Worker contract

Every worker prompt must include:
- mission;
- allowed scope;
- inputs;
- expected outputs;
- forbidden actions;
- acceptance criteria;
- verification method;
- evidence destination.

Workers do not choose project scope or advance phase gates.
