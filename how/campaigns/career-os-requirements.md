SUPERSEDED BY pm/03-requirements.md
# Career OS Requirement Register

Compiled 2026-09-09.

**SUPERSEDED 2026-09-09. The canonical requirement authority is pm/03-requirements.md. This file is retained as a view; its rows are traceable there as R-001 to R-116 via the source column.**

Provenance: 147 of 147 user turns read; 1,218 turns indexed; source md5 `aa7085672cf8af992be74633b32d45c8`.

Rendered view of this same content: `how/campaigns/career-os-requirements.html`.

Every requirement Ally stated across 147 turns, the requirements those demands entail but never named, and the ones nobody has asked for yet. Scored against what the control plane actually does today.

## Counts

| Measure | Value |
| --- | --- |
| Requirements, total | 116 |
| Stated by you | 78 of 116 |
| Inferred | 23 of 116 |
| Suggested | 15 of 116 |
| Met today | 6 of 116 |
| Promotion capacity | 0 of 147 issues |

## Act on these two before anything else

**Data loss, live.** 4,600 lines (656-line `orchestrator.py`, `adna_adapter.py`, `programme.json` with 145 tasks, `adna-mapping.json`) exist only as *untracked, uncommitted* files inside `.worktrees/issue-5/`. On no branch. In no PR. One `git worktree remove` destroys them. There is also no `.gitignore` on any branch in the repo.

**Your first demand is credential-blocked.** `gh auth status` scopes: `gist, read:org, repo, workflow`. `read:project` is absent, so `projectsV2` returns `INSUFFICIENT_SCOPES` and classic Projects 404s. The Kanban from turn 957 cannot be built by any agent with this token. This is the one thing in this document only you can fix.

## How to read the status column

- **MET** holds under test today.
- **PARTIAL** exists but fails its own check.
- **UNMET** nothing implements it.
- **VIOLATED** the system actively does the opposite.
- **OPEN** not yet ruled on.

Scored against the three audits run today, not against any document's claim about itself.

---

# Layer 1 · Stated

78 requirements · 147 of 147 turns read · verbatim

Your words, quoted from the extract with turn numbers. Complaints are included as requirements: a complaint about a failure is a requirement that the failure not recur, and 38 of your 147 turns (26%) were delay pressure alone.

## R1 · AUTONOMY — The system runs without you

> "I SHOULD GET PINGED EVERY TIME A TASK COMPLETES / I SHOULD HAVE A KANBAN VISUAL OF ALL TASKS TO COMPLETION / THERE SHOULD BE CONSTANT UPDATES / ANY ITEMS NEEDING approval should ping me. / THIS SHOULD RUN AUTONOMOUSLY - this should not need me looking at it all day - only reviewing human gates" (TURN 983)

> "i dont think this chat can coordinate. it will fail again." (TURN 515)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-01 | Runs autonomously. You review human gates only. | 983 | VIOLATED |
| S-02 | Ping on every task completion. | 983 | UNMET |
| S-03 | Kanban visual of all tasks through to completion. | 983 | UNMET |
| S-04 | Constant updates. | 983 | UNMET |
| S-05 | Anything needing approval pings you. *status:approval label exists on 0 of 147 issues. The human-gate queue is invisible to every label query.* | 983 | UNMET |
| S-06 | No babysitting. | 507, 969 | VIOLATED |
| S-07 | The system pushes to you. You never have to come and check. | 423, 424 | UNMET |
| S-08 | The next task is always named, and it starts by itself. | 659, 664, 676 | VIOLATED |
| S-09 | Execution continues when the chat stops. *Daemon does survive. It has printed the same line 52 times for 75 minutes.* | 664, 883, 515 | PARTIAL |
| S-10 | Automated methodical engineering process. | 916 | UNMET |
| S-11 | Do not stop and chat. Execute. | 654 | UNMET |

## R2 · DEFECT DETECTION — You must not be the thing that catches the failures

> "I SHOULD NOT BE catching issues -you should be. but you are not - how do you intend to MECHANICALLY ENSURE YOU STOP FAILING LIKE THIS" (TURN 1170)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-12 | The system catches its own issues, by mechanism, not by intention. *Nothing detects the deadlock. No clock, no liveness probe, no repair action. updatedAt is not even requested in the gh --json field list.* | 1170 | UNMET |
| S-13 | The PM never invents governance, onboarding or standards per task. Those are permanent reusable assets. | 1031 | UNMET |
| S-14 | On the first failure of a capability, evaluate and propose alternatives immediately. | 295 | UNMET |
| S-15 | You must not have to lose faith to get correct behaviour. | 501, 505 | OPEN |

## R3 · ROOT CAUSE — Never skip the core issue. Never let it recur

> "I FUCKING HATE AI that skips the core issue and then it comes up again and again" (TURN 269)

> "Not ok - you were in charge of the design of this → The next PM system we design must encode these controls into task / there should not be a NEXT" (TURN 329)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-16 | Never skip the core issue. | 269 | UNMET |
| S-17 | Fix the root cause including a bad tool or a stupid workflow, not the instance. | 276 | UNMET |
| S-18 | Mechanically guarantee the same failure cannot recur. | 297 | UNMET |
| S-19 | Controls encoded into the task itself. There is no "next PM system". | 329 | UNMET |
| S-20 | Saying it does not make it so. | 301 | VIOLATED |
| S-21 | A response that changes nothing about the core issue is not management. | 258 | UNMET |

## R4 · CONTROL PANEL — A visual you can open and read without asking anyone

> "I want a fucking PROJECT VISUAL / - overview issue in github that has a thorough and complete task list - every task is an issue - labelled clearly by its phase and then the task number - CAMPAIGN AND MISSIONS IN ADNA - the whole point was a visual AND I DONT HAVE ONE. / I cannot open github issues and see the project overview or status of project or whats waiting on approval or what is running now - THAT IS A FAILURE. / I HAVE ZERO CLUE WHAT AGENTS ARE RUNNING, WHAT IS BEING DONE OR WHAT PARt of the process we are at." (TURN 954)

> "it should be a fucking kanban - with phae groupings and clearly labelled status" (TURN 957)

> "I AM NOT BUILDING A FUCKING WEB APP" (TURN 971)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-22 | Overview issue carrying a thorough, complete task list. *#148 exists as a hand-maintained markdown substitute. It reports 145 tasks against 147 issues, 4 complete against 3 labelled done, 138 backlog against 139.* | 954 | PARTIAL |
| S-23 | Every task is an issue, labelled by phase and task number. *137 issues carry phase labels no code on main reads.* | 954 | PARTIAL |
| S-24 | Campaign and missions live in aDNA. | 954 | PARTIAL |
| S-25 | See overview, status, what awaits approval, and what is running now, at a glance. | 954 | UNMET |
| S-26 | A Kanban, with phase groupings and clearly labelled status. *Token lacks read:project. Unbuildable by anyone until you grant the scope.* | 957 | UNMET |
| S-27 | Not a web app. | 971 | MET |
| S-28 | A diagram of the PM system: where the control panel is, where aDNA fits, what each piece does. ELI5, with visuals. | 1019 | UNMET |
| S-29 | A task list you can check off. | 188, 542 | PARTIAL |

## R5 · CADENCE — Ten minutes

> "it better be constantly checking in with me and proving a clear task status every 10 minutes too" (TURN 925)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-30 | Check in with clear task status every 10 minutes. The only interval you ever named. | 925 | UNMET |

## R6 · GOVERNANCE — Standards, drift prevention, learning, and blind-agent onboarding

> "What is governance? standards? how are you preventing drift, isues or learning from recurring problems? How are you ensuring all agents know the status of the project when coming in blind and how to build correctly and what they must update at the end? / Adna is source of truth i see but I do not want to see tasks getting repeated or ouside agents UNABLE to find what they need immediately. / Why doesnt the repo have a README of the project management and complete system?? WITH VISUALS?" (TURN 1024)

> "Whats wrong with it and how do you intend to ensure you havent missed any other parts of it" (TURN 1035)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-31 | Defined governance and standards. | 1024 | PARTIAL |
| S-32 | Drift prevention. *13 doc-vs-code contradictions counted today. 3 of 12 ticked STATE.md items fail under test.* | 1024 | VIOLATED |
| S-33 | Learning from recurring problems. *A 14-class taxonomy is documented at who/governance/coordinator.md:52-64 and appears in no code.* | 1024 | UNMET |
| S-34 | Blind-agent onboarding: an agent arriving cold knows project status, how to build correctly, and what it must update at the end. | 1024 | UNMET |
| S-35 | aDNA is the source of truth. *Truth is currently split across 8 stores that disagree.* | 1024 | VIOLATED |
| S-36 | No repeated tasks. *Two full issue generations exist over one repo, #1-#11 and #12-#148.* | 1024 | VIOLATED |
| S-37 | Outside agents find what they need immediately. | 1024 | UNMET |
| S-38 | A README of the project management system, with visuals. *ops/README.md exists and documents a mechanism deleted in commit 363aaab.* | 1024 | VIOLATED |
| S-39 | A method for proving nothing was missed, not a longer list. | 1035 | UNMET |

## R7 · EFFICIENCY — Build repeatable things once

> "If its repeatable it better not be getting built more than once and wasting fucking tokens. STREAMLINE / 3 & 6 do not explain AT ALL how you are going to implement it" (TURN 1029)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-40 | Anything repeatable is built once and reused. *Two coordinators tracked on main. A third uncommitted in a worktree.* | 1029 | VIOLATED |
| S-41 | A defined agent starter pack and skill set. | 1029 | UNMET |
| S-42 | Explain how it will be implemented, not just what it is. | 1029 | OPEN |
| S-43 | A bad tool or workflow that burns 100x tokens is itself the defect. | 276 | UNMET |

## R8 · DOCUMENT HYGIENE — No drift, no bloat

> "you already ran one - so this better not create documentation drift or bloat" (TURN 1136)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-44 | No documentation drift or bloat. | 1136 | VIOLATED |
| S-45 | Review the docs already written rather than adding more. *6 files describe mechanisms that do not exist. 7 orphans. PM_STATUS.md and STATE.md name different current phases.* | 671 | VIOLATED |

## R9 · PLATFORM — aDNA and Herdr, connected to GitHub

> "i expressly said to use adna and herdr. You have done ZERO actual thinkig" (TURN 358)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-46 | Use aDNA and Herdr. | 358, 141 | MET |
| S-47 | aDNA connected to GitHub. *adna_adapter.py and adna-mapping.json exist only as untracked files in a worktree.* | 167 | PARTIAL |
| S-48 | No Zeiko. | 597 | MET |

## R10 · SEQUENCE — The setup order you specified, twice

> "The sequence should be: / 1. Create the GitHub repo + Project first / 2. Create/connect the Adna mission/campaign to that repo / 3. Set up this chat as coordinator / 4. Add Herdr only once there are approved implementation tasks to execute" (TURNS 197 & 201)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-49 | GitHub repo AND Project created first. *Step 1 of 4 was never completed. Every later step inherits a missing control panel.* | 197/201 | VIOLATED |
| S-50 | aDNA mission and campaign connected to the repo, second. | 197/201 | PARTIAL |
| S-51 | Coordinator set up third. | 197/201 | PARTIAL |
| S-52 | Herdr added only once approved implementation tasks exist. | 197/201 | VIOLATED |
| S-53 | Never re-ask for state you already hold. *Four consecutive turns spent making it re-read the repo name it had already written to.* | 638, 647, 670, 674 | UNMET |

## R11 · OUTPUT FORMAT — Clear next steps and a complete checklist, every time

> "do not come back with messages without CLEAR NEXT STEPS IN THEM AGAIN - and i want a complete checklist opn every response from now on - if you have stopped it better be because you need a clear step run by me AND NO OTHER REASON - and it better be detailed out" (TURN 701)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-54 | Clear next steps in every message. | 662, 701 | OPEN |
| S-55 | A complete checklist on every response. | 662, 701 | OPEN |
| S-56 | Stop only for a step you must personally run, spelled out in detail. No other reason. | 701 | OPEN |
| S-57 | Never refuse for missing context that can be obtained. Provide what is needed, or do it. | 666, 1010 | OPEN |

## R12 · TRUTHFULNESS — A COMPLETED block must be true

> "So this was a complete fabrication?? COMPLETED / - Persistent Herdr coordinator bridge built under `ops/herdr-coordinator/` … ## DECISION REQUIRED / None." (TURN 657)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-58 | No fabricated COMPLETED claims. *STATE.md's ticked list over-reports by at least 3 of 12 under test today.* | 657 | VIOLATED |
| S-59 | Every claim carries evidence that can be re-run. | 1172, 301 | UNMET |
| S-60 | A capability is validated before a coordination role is claimed on the back of it. | 278, 280, 286 | UNMET |

## R13 · HONESTY ABOUT UNDERSTANDING — Do not retroactively claim you already knew

> "stop saying exxactly when you missed the fucking point until i said it" (TURN 509)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-61 | Never imply you already understood a point you had to be told. | 509, 511, 293 | OPEN |

## R14 · DELEGATION — Send agents. Report only

> "doing it yourself would be the absolute worst answer and if you jump to that you are a failure" (TURN 1132)

> "you remain AVAILABLE IN CHAT - send agents cunt and REPORT ONLY" (TURN 578)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-62 | The coordinator never does the work itself. *Now enforced by your PM hook, which blocked main-session reads today.* | 1132 | MET |
| S-63 | Dispatch agents, stay available in chat, report. | 578 | MET |

## R15 · ACCEPTANCE — The test you said you would run

> "im then going to open a new chat with zero context on this and ask it to tell me what it does if it will actually achieve my goals and critically look at it - this chat better not find a single issue with its implementation, design or runtime as an automous high standard PM system." (TURN 1065)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-64 | A zero-context reviewer finds no issue with implementation, design or runtime. *This is the acceptance test for the whole rebuild. Three zero-context audits ran today and returned 13 absent controls, 9 cross-system disagreements and 12 tech-debt items.* | 1065 | VIOLATED |

## R16 · PROCESS — Design before build, with measurable outcomes

> "the main problem I have with agents is they build before designing properly - then it goes wrong as there is no way to measure outcomes are correct / success" (TURN 85)

> "HOW ARE WE going to have this list ACTUALLY BE SYSEMATICALLY COMPLETED - not fucking you going la la la and doing whatever the fuck you remember IF YOU EVEN DO" (TURN 901)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-65 | Design properly before building, with a way to measure that outcomes are correct. | 85 | UNMET |
| S-66 | A phase table: each phase and exactly what it produces. | 98 | PARTIAL |
| S-67 | Per phase, the best product, process or AI type, plus its data pack and prompt needs. | 100 | UNMET |
| S-68 | The complete phased development list. | 899 | PARTIAL |
| S-69 | That list is systematically completed by mechanism, not from memory. *Promotion capacity is 0 of 147. Nothing on the list can advance.* | 901 | VIOLATED |
| S-70 | Redesign it properly from scratch. | 1037 | OPEN |

## R17 · SPEED — Delay is itself the defect

> "how are you going to build this in the next 10 minutes - youve wasted hours with poor design and i havent even been able to start the actual project - YOU ARE A BLOCKER CURRENTLY" (TURN 1094)

> "I WANT THE FUCKING PRODUCT BUILT" (TURN 973)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-71 | Time to first real product work is a first-class metric. | 38 turns, 26% of everything you said | VIOLATED |
| S-72 | The product gets built. PM setup consuming the whole session is the failure. *PR #10, two documents, is the only product artifact produced in 12+ hours.* | 973, 1094 | VIOLATED |

## R18 · NO MANUAL STEPS — Fix the capability, not the instance

> "what about the next time we want to edit github you stupid fuck" (TURN 261)

> "omg youve done the same thing 20 times" (TURN 498)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-73 | Manual steps are a defect, counted and driven to zero. *STATE.md still lists three manual commands you ran 75 minutes ago.* | 256 | VIOLATED |
| S-74 | Fix the capability so the next occurrence cannot happen, not just this one. | 261, 427 | UNMET |
| S-75 | Never retry a failing approach repeatedly. *52 identical no-op cycles logged in the daemon pane.* | 498 | VIOLATED |

## R19 · THE PRODUCT — What you are actually building

> "I should mention that I'd like to realease this product as an open source repo that people can just put their own AI / supabase etc keys in on the ui and it will run for them … I've been using adna.network as a campaign and mission organiser.. then I also want a visual and like an agent that keeps track of full progress. I have adhd - I need like a github board of whats getting done where and status etc - a mission control." (TURN 121)

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| S-76 | Open source, bring-your-own-keys, runs for anyone. | 121 | OPEN |
| S-77 | The mission control visual is an accessibility requirement, not a preference. You named ADHD as the reason. *This reclassifies S-26. A missing Kanban is an accessibility failure, not a missing nice-to-have.* | 121 | VIOLATED |
| S-78 | The pipeline: jobs found daily, resumes and cover letters tailored, approve-to-send, tracker, automatic follow-ups, application status derived from email. Five surfaces. Supabase. Composer kept as the advanced editor. | 71, 35, 83 | OPEN |

---

# Layer 2 · Inferred

23 requirements · entailed, never stated

These follow logically from what you demanded but appear nowhere in your words. They are the ones that dangle, because nobody writes down what they assume. Nine of my original inferences were promoted into Layer 1 once your verbatim turns arrived, which is the correct outcome: your words beat my derivation.

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| I-01 | A heartbeat must carry what advanced since the last beat, not just proof of life. *From S-30. A ten-minute ping that says "running" 52 times is what you have now.* | derived | UNMET |
| I-02 | The check-in is generated from observed state, never from the coordinator's belief about state. *From S-30 + S-58. Otherwise it reports its own hallucination on a timer.* | derived | UNMET |
| I-03 | Every number in every report carries its denominator. *From S-58. "4 complete" hid that #148 counts 145 tasks against 147 issues.* | derived | UNMET |
| I-04 | A failure stops dependent work only. Blast radius is bounded. *From S-01. One stale label currently halts all 147 issues.* | derived | VIOLATED |
| I-05 | Every blocker has a named owner and a visible age. *system-blocker is on 0 of 147 issues while the system is deadlocked.* | derived | UNMET |
| I-06 | No agent may verify its own work, and no agent may write its own status. *The single root cause of the #5 deadlock. The worker was asked to apply the label that judges it.* | derived | VIOLATED |
| I-07 | Status is derived from observable ground truth: branch, PR, declared files present in the diff, reviewer verdict. Never from a message anyone sends. *Three of the four artifacts the packet demands are unreadable by the code demanding them.* | derived | UNMET |
| I-08 | No gate is trusted until it has been seen RED against a real defect. *herdr_dispatch.sh:32 reads .result.agent.state, a key Herdr 0.9.0 does not emit. The blocked branch has never fired and cannot.* | derived | VIOLATED |
| I-09 | A health field that cannot go non-empty is a lie. Health must be computed, never hardcoded. *The uncommitted rewrite hardcodes stalled_tasks = [] at line 324 and filters for a STALLED event that is never emitted.* | derived | VIOLATED |
| I-10 | Every claim in a document is an executable check, or it is deleted. *From S-44. 15 narrative claims in STATE.md; 8 fail under test.* | derived | UNMET |
| I-11 | One authoritative writer per data domain. Drift is what two writers produce. *From S-35. Coordinator and worker both write the same labels, unarbitrated.* | derived | VIOLATED |
| I-12 | Deterministic task identity by fingerprint, so re-seeding cannot create a duplicate. *From S-36. Current identity is title-string match, and three seed titles contain em dashes.* | derived | UNMET |
| I-13 | An execution lease per task, with expiry, so a dead agent cannot hold a slot forever. *This is precisely the #5 bug. 75 minutes and counting.* | derived | UNMET |
| I-14 | OWNS sets computed disjoint before parallel dispatch, mechanically. *From S-01. Required before WIP can safely exceed 1.* | derived | UNMET |
| I-15 | WIP is a real concurrency limit, not a stall detector. *#148 reports 3 running against a limit of 1.* | derived | VIOLATED |
| I-16 | An agent may not modify the control plane. Product lanes get product scope only. *The #5 worker was briefed to write two documents and instead rewrote the orchestrator and created 137 GitHub issues.* | derived | VIOLATED |
| I-17 | Nothing an agent produces may exist only as untracked files. Work is committed or it does not exist. *4,600 lines currently one command from permanent loss.* | derived | VIOLATED |
| I-18 | Cross-system reconciliation on every cycle: GitHub, git, worktrees, Herdr, canonical state. *9 cross-cutting disagreements found today; none is detected by any code.* | derived | UNMET |
| I-19 | Blind-agent onboarding needs a machine-readable context bundle with a freshness stamp. A stale bundle is worse than none. *From S-34.* | derived | UNMET |
| I-20 | Context freshness contract: work built against a superseded spec version is invalidated, not merged. *From S-32.* | derived | UNMET |
| I-21 | The zero-context review is run as a gate before you run it, not after. *From S-64. Otherwise your acceptance test is a coin flip.* | derived | UNMET |
| I-22 | Chaos tests run on a schedule. A chaos test that exists but never runs is documentation. *0 tests and 0 CI workflows exist in 31 tracked files.* | derived | UNMET |
| I-23 | Known-open edge cases are enumerated with a count. Never an implied zero. *From S-39. You get handled-count and open-count, or you get a guess.* | derived | UNMET |

---

# Layer 3 · Suggested

15 requirements · my judgement, not yours

You have not asked for any of these. Reject them individually. G-15 is the one I most expect you to reject and most think you need.

| ID | Requirement | Source | Status |
| --- | --- | --- | --- |
| G-01 | Cost ceiling per task and per day, with a hard stop. *Continuously running parallel agents spend money while you sleep. No governor exists anywhere in the design.* | judgement | OPEN |
| G-02 | Reversibility classification on every autonomous action. One-way doors stop and ask; everything else proceeds. *This is the single mechanism that makes autonomy safe rather than frightening, and it is what lets the coordinator stop asking you Type 2 questions.* | judgement | OPEN |
| G-03 | A "what it did while you slept" digest, separate from the heartbeat: decisions taken on your behalf, with reasoning. *Lets you audit delegated judgement without reading everything.* | judgement | OPEN |
| G-04 | A one-command kill switch that halts everything without corrupting state. *Stopping it currently means finding a PID.* | judgement | OPEN |
| G-05 | Two-way requirement traceability: every task names the requirement it closes, every requirement names its test. *The 137 orphan issues are exactly this failure, already present and already costing you.* | judgement | OPEN |
| G-06 | Definition of Done owned by the requirement, not by the task. *Stops acceptance criteria drifting to whatever the task happened to achieve.* | judgement | OPEN |
| G-07 | Time-box per task with escalation on overrun. *A lease covers the crash case. A time-box covers the quietly-wrong case, which is what #5 actually was.* | judgement | OPEN |
| G-08 | Human gates batched and presented once, not trickled. *Six interruptions cost more than one decision session.* | judgement | OPEN |
| G-09 | The system explains itself on demand. "Why is task X blocked" answerable by one command. *Without it, every anomaly costs you a forensic session. Today cost three.* | judgement | OPEN |
| G-10 | Graceful degradation. If Herdr dies, the queue survives in GitHub and resumes. *Your execution plane is currently a single point of failure with no fallback.* | judgement | OPEN |
| G-11 | Every phase ships something you can look at, not only documents. *Twelve hours has produced two markdown files and a deadlock.* | judgement | OPEN |
| G-12 | A single credential preflight that fails loudly at startup on a missing scope. *read:project has been missing all along and nothing told you.* | judgement | OPEN |
| G-13 | One task registry, one label taxonomy, enforced. A second one is rejected at write time. *Two generations of issues and two label vocabularies exist over one repo today.* | judgement | OPEN |
| G-14 | Any agent-created GitHub object carries its originating task ID, so mass creation is attributable and reversible. *137 issues appeared in a 5-minute burst and nothing records which task made them or why.* | judgement | OPEN |
| G-15 | **A hard cap on control-plane investment before product work resumes.** Name the number: hours, or "when the reconciler passes chaos test 3". Then coordinator work stops whether it is beautiful or not. *Your own turns 973, 1094 and 38 delay-pressure turns say this louder than I can. The PM system is not the deliverable. A control plane that is 80% right and running beats one that is 100% designed and not.* | judgement | OPEN |

---

# The dispatch-bridge brief, scored

satisfies 2 of 116

The design ChatGPT proposed, measured against this register rather than against itself.

| Part of the brief | Verdict | Against |
| --- | --- | --- |
| Requirement 5, idempotency: seven test cases | KEEP VERBATIM | Closes I-12. The strongest thing in the document and better than anything in your control plane today |
| Requirement 6, user exclusion | KEEP VERBATIM | Restates S-01, S-06, S-73. Testable |
| Requirement 8, HUMAN ACTION REQUIRED format | KEEP | Correct shape for S-56 |
| Durable queue surviving restart | LATER | Partially closes I-13. Correct idea, wrong order |
| `.career-os/control.db` as a new store | REJECT | Violates I-11 and S-35. Adds a ninth source of truth to eight that already disagree, while the brief itself forbids duplicate state stores |
| `RETURN ONLY / COMPLETED / TEST RESULTS` | REJECT | Violates I-06 and S-58. This is self-certification, the exact defect that deadlocked #5, and turn 657 is you catching a fabricated COMPLETED block |
| Eight acceptance criteria | REJECT | Not one tests that work was done correctly. No reviewer anywhere. Violates I-06, I-21, S-64 |
| MCP surface with `source: "chatgpt"` | REJECT | Re-admits the model turn 515 rejected and turn 1216 revoked. A GitHub issue with a label is already a durable, idempotent, restart-surviving queue you can write to from your phone |
| "Do not redesign the whole PM system" | CONTRADICTS | Directly opposes S-70, turn 1037: "Redseign it properly from scratch" |

**Net.** It fixes the entrance while the exit is welded shut. Your pipeline is not dead because intent could not get in; it is dead because a worker finished, opened a mergeable PR, and nothing noticed for 75 minutes. Salvage requirements 5, 6 and 8. Build the bridge at step 8, behind the reconciler, never in front of it.

---

# Evidence behind the scores

three read-only audits · 2026-09-09

| Finding | Measure | Source |
| --- | --- | --- |
| Architectural controls implemented | 0 of 13 | State machine, truth ownership, schema versioning, stale-context protection, concurrency control, task identity, reconciliation, crash recovery, cost governance, capability boundaries, observability, supersession, PM tests. All ABSENT |
| Tests and CI | 0 of 31 files | `git ls-files \| grep -Ei 'test\|spec\|conftest\|pytest\|workflows'` exits 1 |
| Promotion capacity | 0 of 147 | 144 lack acceptance markers; the other 3 are gated behind `control_acceptance_passed()`, whose passing set is empty |
| Orphan issues no code references | 137 of 147 | #12-#148, created by PAT in a 5-minute burst, carrying a `phase:*`/`status:*` taxonomy nothing on main reads |
| Issue comments repo-wide | 0 | The mandated worker evidence trail has never produced a single artifact. VACUOUS, not passing |
| Deadlock duration at audit | 52 cycles / 75 min | `RUNNING: WIP limit reached (1)`, printed into an unlogged pane |
| STATE.md ticked items failing under test | 3 of 12 | T2 content, T6 wrong Herdr key, T10 claims a mechanism removed that survives in 9 places across 6 files |
| STATE.md narrative claims failing | 8 of 15 | Including "canonical state updates automatically" and "Human decisions required: None" |
| Cross-system disagreements | 9 | Two label taxonomies, two orchestrators, two tracked coordinators, a missing env file, an unreachable gate, zero comments, no gitignore, missing token scope, silent 200-issue truncation |
| Control planes over one repo | 2 | Generation A (#1-#11, ChatGPT Codex Connector) and Generation B (#12-#148, PAT). Only A runs, and it cannot see B's backlog |

---

Compiled from three independent read-only audits and a verbatim extraction of 147 of 147 user turns from a 1,218-turn source, md5 `aa7085672cf8af992be74633b32d45c8`. Nothing in the repository, GitHub or the running daemon was modified to produce this document. Issue #5 and PR #10 held frozen as the reproduction case.

Scores reflect the system as measured on 2026-09-09, not as described by any document within it.
