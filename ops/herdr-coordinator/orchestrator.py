#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path

import coordinator as core

ROOT = Path(__file__).resolve().parents[2]
POLL_SECONDS = int(os.getenv("CAREER_OS_POLL_SECONDS", "60"))
REVIEW_AGENT = os.getenv("CAREER_OS_REVIEW_AGENT", "codex")
REVIEW_RUNNING = "review-running"
VERIFIED = "verified"

SEED = [
    {"key":"P0-001","title":"P0-001 — Canonical product vision and problem statement","body":"""DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS
CONTROL_ACCEPTANCE: true

## Outcome
Create the canonical Phase 0 product vision and problem statement for Career OS.

## Deliverables
- docs/product/vision.md
- docs/product/problem-statement.md
"""},
    {"key":"P0-002","title":"P0-002 — Personas and jobs-to-be-done","body":"""DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS
AFTER_CONTROL_ACCEPTANCE: true

## Deliverables
- docs/product/personas.md
- docs/product/jobs-to-be-done.md
"""},
    {"key":"P0-003","title":"P0-003 — Scope, non-goals, success metrics and principles","body":"""DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS
AFTER_CONTROL_ACCEPTANCE: true

## Deliverables
- docs/product/scope.md
- docs/product/non-goals.md
- docs/product/success-metrics.md
- docs/product/product-principles.md
- docs/product/glossary.md
"""},
]

def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)

def ensure_extra_labels() -> None:
    for name, colour, desc in [
        (REVIEW_RUNNING,"FBCA04","Independent reviewer dispatched"),
        (VERIFIED,"0E8A16","Independent verification passed"),
    ]:
        run(["gh","label","create",name,"--color",colour,"--description",desc,"--force"])

def all_issues() -> list[dict]:
    data = core.gh_json(["issue","list","--state","all","--limit","200","--json","number,title,body,state,labels,url"])
    assert isinstance(data,list)
    return data

def issue_labels(issue: dict) -> set[str]:
    return {x["name"] for x in issue.get("labels",[])}

def seed_backlog() -> None:
    existing={i["title"] for i in all_issues()}
    for spec in SEED:
        if spec["title"] not in existing:
            run(["gh","issue","create","--title",spec["title"],"--body",spec["body"]])

def control_acceptance_passed(issues:list[dict])->bool:
    for issue in issues:
        if re.search(r"(?im)^CONTROL_ACCEPTANCE:\s*true\s*$",issue.get("body") or "") and issue.get("state")=="CLOSED" and VERIFIED in issue_labels(issue):
            return True
    return False

def promote_ready()->None:
    issues=all_issues(); control_ok=control_acceptance_passed(issues)
    for issue in issues:
        if issue.get("state")!="OPEN": continue
        body=issue.get("body") or ""; current=issue_labels(issue)
        guarded={core.LABELS["ready"],core.LABELS["running"],core.LABELS["review"],REVIEW_RUNNING,core.LABELS["blocker"],core.LABELS["decision"]}
        if current & guarded: continue
        gated=bool(re.search(r"(?im)^AFTER_CONTROL_ACCEPTANCE:\s*true\s*$",body))
        is_control=bool(re.search(r"(?im)^CONTROL_ACCEPTANCE:\s*true\s*$",body))
        ok,_=core.controls_pass(body)
        if ok and (is_control or (gated and control_ok)):
            core.add_labels(int(issue["number"]),core.LABELS["ready"])

def dispatch_review(issue:dict)->None:
    number=int(issue["number"]); worktree=ROOT/".worktrees"/f"issue-{number}"
    if not worktree.exists():
        core.add_labels(number,core.LABELS["blocker"]); raise RuntimeError(f"review worktree missing for #{number}")
    packet=worktree/".career-os"/"REVIEW.md"; packet.parent.mkdir(exist_ok=True)
    packet.write_text(f"""# Independent review — GitHub #{number}
Review strictly against the issue, CLAUDE.md, STATE.md, linked specs and tests.
If PASS: comment VERIFIED: PASS, add label verified, remove agent-review/review-running, close completed.
If FAIL: comment VERIFIED: FAIL with exact failures; remove review labels; add agent-ready for repair unless systemic, then system-blocker.
Do not implement fixes during review.
""",encoding="utf-8")
    core.add_labels(number,REVIEW_RUNNING)
    try:
        core.dispatch_agent(worktree,REVIEW_AGENT,packet,number)
    except Exception:
        core.remove_label(number,REVIEW_RUNNING); core.add_labels(number,core.LABELS["blocker"]); raise

def review_cycle()->None:
    for issue in core.issue_list(core.LABELS["review"]):
        if REVIEW_RUNNING not in issue_labels(issue): dispatch_review(issue)

def cycle()->None:
    core.preflight(); ensure_extra_labels(); seed_backlog(); review_cycle()
    if core.has_system_blocker():
        print("BLOCKED: system-blocker open"); return
    promote_ready(); control_ok=control_acceptance_passed(all_issues()); core.WIP_LIMIT=3 if control_ok else 1; core.once()

def daemon()->None:
    while True:
        try: cycle()
        except KeyboardInterrupt: raise
        except Exception as exc: print(f"ORCHESTRATOR ERROR: {exc}")
        time.sleep(POLL_SECONDS)

def main()->None:
    import argparse
    parser=argparse.ArgumentParser(); parser.add_argument("command",choices=["once","daemon"]); args=parser.parse_args()
    cycle() if args.command=="once" else daemon()

if __name__=="__main__": main()
