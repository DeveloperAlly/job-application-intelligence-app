# Persistent Coordinator Governance

## Purpose

Provide a project manager that persists independently of any chat session and advances Career OS without requiring the human to babysit state or workers.

## Canonical truth

Priority order:
1. GitHub/repository evidence
2. `STATE.md`
3. mission/campaign documents
4. agent output
5. chat history

Agent claims never override repository evidence.

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
