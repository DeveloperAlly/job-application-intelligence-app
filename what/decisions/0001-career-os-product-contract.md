# Decision 0001 — Career OS Product Contract

Status: ACCEPTED
Date: 2026-09-09

## Decision
Career OS is an open-source, self-hostable career automation operating system built around verified career evidence, bounded automation, and human approval at consequential decisions.

The core product proposition is:

**Your career evidence, compiled for every job.**

The core wedge is:

job → evidence → tailored application compiler

The system lifecycle is:

Find jobs automatically → score → generate tailored application kits → user approves → send → track → follow up → infer status from email → learn from outcomes.

## Accepted constraints
- BYOK/BYO infrastructure is foundational.
- No invented claims or metrics.
- Career evidence is durable; generated documents are disposable outputs.
- Human approval is required for consequential external actions.
- Deterministic orchestration handles state, scheduling, dedupe and hard constraints.
- LLMs handle interpretation, evidence relevance, positioning, generation, synthesis and classification.
- Agents are bounded and contract-driven.
- Production code is gated behind product/data contracts, failure modes, acceptance tests and evals.
- The current five-page IA is Today, Jobs, Documents, Career Data, Toolkit.

## Consequences
Phase 0 must produce and verify the product-definition pack before later phases proceed. Downstream design or implementation that contradicts this decision requires an explicit superseding decision record.

## Supersedes
None.
