# P0-003 — Scope, non-goals, success metrics, principles and glossary

## State
BLOCKED until persistent coordinator gate passes.

## Outcome
Define the remaining Phase 0 product contract.

## Deliverables
- `docs/product/scope.md`
- `docs/product/non-goals.md`
- `docs/product/success-metrics.md`
- `docs/product/product-principles.md`
- `docs/product/glossary.md`

## Controls
DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: BLOCKED_BY_CONTROL_PLANE

## Constraints
- Product definition only.
- No implementation.

## Acceptance
- v1 scope and later scope are separated.
- Non-goals prevent resume-builder/ATS/spam-product drift.
- Metrics include unsupported-claim rate, time-to-ready, accepted-job rate and application outcomes.
- Principles include evidence before generation, explainability, human approval for consequential external actions, and BYOK/self-hosting.
- Independent reviewer verifies against campaign and source material.
