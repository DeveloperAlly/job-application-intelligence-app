# Career OS: Problem Statement

## The problem

Job searching is a high-volume, high-effort process where the work does not compound. Every application requires the same steps: read the job description, identify relevant experience, rewrite a resume to emphasize the right things, draft a cover letter, submit, track, follow up. Each cycle starts from scratch. Nothing learned from one application systematically improves the next.

This creates three concrete failures:

1. **Quality collapses at volume.** Tailoring an application properly takes significant time. Most people either apply to many roles with generic materials (low hit rate) or carefully tailor a few applications (low volume). Both strategies underperform.

2. **Career evidence is trapped in documents.** A person's real career evidence (projects completed, outcomes achieved, skills demonstrated) exists only as prose scattered across old resumes, LinkedIn profiles, and memory. There is no structured, queryable, verified record. Every new application requires the person to re-excavate and re-articulate the same facts.

3. **The process is opaque and unmanaged.** Most job seekers have no systematic view of where their applications stand, what follow-up is due, which strategies produce results, or how their materials perform. Tracking happens in spreadsheets or not at all. There is no feedback loop.

## Who has this problem

Technical professionals in active job search: software engineers, data scientists, product managers, designers, and similar roles where job descriptions vary enough that generic applications underperform, and where the applicant's evidence base (projects, technologies, outcomes) is rich enough to benefit from structured matching.

The acute version of this problem hits when someone is searching actively (applying to 10 or more roles per week) and the cognitive load of tailoring, tracking, and following up becomes unsustainable.

## Why existing tools fail

**Resume builders** (Teal, Resumake, various editors) help format documents but do not maintain a structured evidence base, do not match evidence to job requirements, and do not automate the application lifecycle.

**AI writing assistants** (ChatGPT, Claude, generic copilots) can draft text but have no persistent model of the user's career, no verification that generated claims are factually grounded, and no lifecycle management. Every conversation starts cold.

**Job boards and aggregators** (LinkedIn, Indeed, Glassdoor) handle discovery but not the application preparation, tailoring, or tracking workflow.

**ATS and CRM tools** (Huntr, Trakstar, spreadsheets) track submissions but do not help generate or tailor materials.

No existing tool connects the full loop: evidence management, job analysis, intelligent matching, document generation, verification, approval, submission support, tracking, follow-up, and learning. Career OS does.

## What a solution requires

1. A structured, verified evidence base that persists across applications and grows over time.
2. Per-application intelligence that analyzes job requirements and matches them against the evidence base.
3. Document generation that produces tailored, factually grounded materials traceable to source evidence.
4. Human approval before any consequential action (sending an application, making a claim).
5. Lifecycle tracking from discovery through outcome.
6. A feedback loop where outcomes improve future scoring, matching, and generation.
7. Self-hostable, open-source, BYOK architecture so the user owns their data and chooses their providers.

## v1 scope

v1 validates requirements 1 through 4: evidence base, job analysis, evidence matching, resume generation with fact verification, and human review. Requirements 5 through 6 (lifecycle tracking and learning) are post-v1. Requirement 7 (self-hostable BYOK) applies from the start.
