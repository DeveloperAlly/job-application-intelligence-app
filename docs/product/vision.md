# Career OS: Product Vision

## One-line vision

Your career evidence, compiled for every job, automatically.

## What Career OS is

Career OS is an open-source, self-hostable operating system for job search and application. It treats verified career evidence as the durable asset and treats resumes, cover letters, and other application documents as disposable outputs derived from that evidence, tailored to each opportunity.

The system automates the full application lifecycle: discovering relevant jobs, scoring them against your profile, generating tailored application materials, routing them for your approval, tracking submissions, following up, inferring status from signals like email, and learning from outcomes to improve over time.

## Core proposition

Job seekers today perform the same high-effort work for every application: reading job descriptions, matching their experience, rewriting documents, tracking submissions, following up. This work is repetitive, cognitively expensive, and produces artifacts that are immediately stale. Career OS inverts this. You invest once in building a verified evidence base of your career. The system handles the per-application work.

## Foundational commitments

**Open-source, self-hostable, BYOK.** Users bring their own infrastructure and model providers. No vendor lock-in. A clean checkout with a new database and user-supplied AI key must work without source edits or manual setup scripts.

**Evidence integrity.** The system's core data layer is facts: verified career evidence, not generated text. Generated documents are always traceable to the evidence they claim. Facts are immutable inputs. Documents are disposable outputs.

**Human authority at consequential decisions.** The system automates routine work. It does not send applications, commit to claims, or take irreversible actions without explicit human approval. Automation handles discovery, analysis, generation, and tracking. Humans approve what goes out.

**Bounded intelligence.** LLMs handle interpretation, relevance scoring, positioning, generation, synthesis, and classification. Deterministic orchestration handles state, scheduling, deduplication, hard constraints, and lifecycle control. No unconstrained agent loops.

## End-to-end product outcome

A user configures Career OS with their career evidence and job search preferences. The system continuously discovers relevant opportunities, scores and ranks them, and generates complete application kits (tailored resume, cover letter, positioning notes) for the top candidates. The user reviews and approves. The system tracks each application through its lifecycle, infers status from incoming signals, suggests follow-up actions, and feeds outcome data back into its scoring and generation models.

The result: higher application volume at higher quality, with less manual effort per application, and a compounding data advantage as the system learns what works.

## v1 boundary

v1 delivers the core loop: manual job description input, job analysis, evidence matching, resume generation, fact verification, and human review. Automated job discovery, cover letters, submission support, email-based status inference, follow-up automation, and learning loops are post-v1.

v1 proves the thesis that a structured evidence base plus bounded AI agents can produce application materials that are factually grounded, well-positioned, and ready for human review, without the user rewriting from scratch each time.
