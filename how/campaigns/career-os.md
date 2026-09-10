# Campaign — Career OS: Build and Open-Source

## Outcome

Deliver an open-source, self-hostable career automation platform where a user can bring their own infrastructure/model providers and move through the full job-search/application lifecycle with human approval at consequential decisions.

## Requirements

Canonical requirement authority: `pm/03-requirements.md`. It preserves R-001–R-116 from the campaign register and adds product requirements. The older campaign Markdown and HTML are historical views. Product intent remains in `what/context/product-contract.md`; every task and phase gate must name the requirements and evidence it addresses.

## Product proposition

**Your career evidence, compiled for every job.**

Durable asset: verified career evidence. Documents are disposable outputs derived from that evidence.

## Lifecycle

Find jobs automatically → score → generate tailored application kits → user approves → send → track → follow up → infer status from email → learn from outcomes.

## Phase sequence

0. Product Definition
1. User Journey & IA
2. UX/UI Design
3. Domain/Data Design
4. System Architecture
5. Agent Design
6. Eval Design
7. Technical Planning
8. Foundation Build
9. Vertical Slice 1
10. Expand Intelligence
11. Automation
12. Application Workflow
13. Learning Loop
14. Hardening/Release
15. Ongoing Product Ops

## Build gate

No production code until product contract, data contract, failure modes, acceptance tests, and required evals exist.

## OSS release gate

A clean checkout with a new Supabase project and user-supplied AI key must support configure → migrate → import → analyze a job → generate → save without source edits or manual SQL.

## Architecture principles

- Database = facts and durable derived knowledge.
- Intelligence = explainable decisions over facts.
- Application layer = actions and workflows.
- Facts are immutable inputs; documents are disposable outputs.
- Deterministic orchestration for state, scheduling, dedupe, hard constraints and lifecycle control.
- LLMs for interpretation, evidence relevance, positioning, generation, synthesis and classification.
- Bounded agents only; no unconstrained agent loops.
- Human approval at material decisions, not routine PM operations.
