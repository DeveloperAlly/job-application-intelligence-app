# Career OS — Project Management Checklist

This is the durable project checklist. `STATE.md` controls what is active; this file defines the full gated programme.

## Control plane — must pass before Phase 0

- [x] Repository write/read path proven
- [x] aDNA campaign created
- [x] Coordinator governance installed
- [x] Persistent coordinator code committed
- [ ] Local Herdr runtime preflight passes
- [ ] Persistent coordinator daemon starts
- [ ] One real mission dispatches without human prompting
- [ ] Worker output is independently verified
- [ ] Canonical state updates automatically
- [ ] Next eligible mission dispatches automatically

**Gate:** Persistent coordinator operational.

## Phase 0 — Product Definition

- [ ] P0-001 — Vision
- [ ] P0-001 — Problem statement
- [ ] P0-002 — Personas
- [ ] P0-002 — Jobs-to-be-done
- [ ] P0-003 — Scope
- [ ] P0-003 — Non-goals
- [ ] P0-003 — Success metrics
- [ ] P0-003 — Product principles
- [ ] P0-003 — Glossary
- [ ] P0-GATE — Product definition approved

## Phase 1 — User Journey & IA

- [ ] Onboarding journey
- [ ] Job discovery journey
- [ ] Job review journey
- [ ] Application generation journey
- [ ] Approval journey
- [ ] Submission journey
- [ ] Tracking journey
- [ ] Follow-up journey
- [ ] Interview journey
- [ ] Outcome journey
- [ ] Career-data maintenance journey
- [ ] Navigation map
- [ ] Page inventory
- [ ] Application state machine
- [ ] Automation state machine
- [ ] Phase 1 gate

## Phase 2 — UX/UI Design

- [ ] Today
- [ ] Jobs
- [ ] Application workspace
- [ ] Documents
- [ ] Composer
- [ ] Career Data
- [ ] Toolkit
- [ ] Setup Wizard
- [ ] Connections/System Health
- [ ] Empty/loading/error/stale/uncertainty states
- [ ] Clickable core journey
- [ ] Phase 2 gate

## Phase 3 — Domain/Data Design

- [ ] Domain model
- [ ] ERD
- [ ] Entity lifecycle definitions
- [ ] Provenance model
- [ ] Versioning model
- [ ] RLS/security model
- [ ] Migration plan
- [ ] Reasoning-layer entities
- [ ] Installation/provider entities
- [ ] Phase 3 gate

## Phase 4 — System Architecture

- [ ] System overview
- [ ] Service boundaries
- [ ] Data flow
- [ ] Event model
- [ ] Agent orchestration
- [ ] Integrations
- [ ] Provider abstraction
- [ ] Security
- [ ] Observability
- [ ] Failure recovery
- [ ] ADRs
- [ ] Phase 4 gate

## Phase 5 — Agent Contracts

- [ ] Job analysis
- [ ] Requirement matching
- [ ] Positioning
- [ ] Resume writer
- [ ] Cover-letter writer
- [ ] Voice rewriter
- [ ] Verifier
- [ ] Email classifier
- [ ] Company research
- [ ] Phase 5 gate

## Phase 6 — Evals

- [ ] JD-analysis golden dataset
- [ ] Evidence-match dataset
- [ ] Resume-generation dataset
- [ ] Cover-letter dataset
- [ ] Email-status dataset
- [ ] Voice dataset
- [ ] Thresholds
- [ ] Regression policy
- [ ] Phase 6 gate

## Phase 7 — Technical Planning

- [ ] Epics
- [ ] Bounded tickets
- [ ] Dependency map
- [ ] Risk register
- [ ] Migration sequence
- [ ] Release plan
- [ ] Phase 7 gate

## Phase 8 — Foundation Build

- [ ] Auth
- [ ] Reproducible migrations
- [ ] RLS
- [ ] API layer
- [ ] Audit/run lineage
- [ ] Document versioning
- [ ] State/event engine
- [ ] Queue/worker
- [ ] Provider registry
- [ ] Connections framework
- [ ] Test harness
- [ ] Phase 8 gate

## Phase 9 — Vertical Slice 1

- [ ] Manual JD input
- [ ] JD analysis
- [ ] Evidence match
- [ ] Resume generation
- [ ] Fact verification
- [ ] Review
- [ ] E2E acceptance

## Phase 10 — Expand Intelligence

- [ ] Cover letters
- [ ] Company research
- [ ] Positioning
- [ ] Voice/copy lint
- [ ] Evidence gaps
- [ ] Recruiter scan

## Phase 11 — Automation

- [ ] Job discovery
- [ ] Ranking
- [ ] Daily queue
- [ ] Notifications
- [ ] Automation activity/trust UI

## Phase 12 — Application Workflow

- [ ] Approvals
- [ ] Submission support
- [ ] Tracker
- [ ] Email sync
- [ ] Status inference
- [ ] Follow-up engine
- [ ] Interview mode
- [ ] Recruiter CRM

## Phase 13 — Learning Loop

- [ ] Edit-diff learning
- [ ] Outcome analytics
- [ ] Search-title learning
- [ ] Evidence-performance analytics
- [ ] Strategy-performance analytics

## Phase 14 — Hardening / Release

- [ ] Security review
- [ ] Load/failure tests
- [ ] Backup/restore
- [ ] Monitoring/alerts
- [ ] Privacy/data export/delete
- [ ] Rollback
- [ ] Clean-room installation
- [ ] OSS release gate

## Phase 15 — Ongoing Product Ops

- [ ] Change-control process
- [ ] Prompt versioning
- [ ] Eval regression suite
- [ ] ADR governance
- [ ] Schema governance
- [ ] Data-health audit

## Execution rules

- Maximum WIP is 1 until the control-plane acceptance test passes; then 3.
- No downstream task becomes ready while an open `system-blocker` exists.
- No production code before required product/data/failure/acceptance/eval contracts exist.
- A task is not complete until durable evidence is independently verified.
- Human involvement is exception-only: product decision, phase gate, destructive action, credential/account action, or non-resolvable systemic blocker.
