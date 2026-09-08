#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import shlex
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
    {
        "key": "P0-001",
        "title": "P0-001 — Canonical product vision and problem statement",
        "control_acceptance": True,
        "after_control": False,
        "body": """DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS
CONTROL_ACCEPTANCE: true

## Outcome
Create the canonical Phase 0 product vision and problem statement for Career OS from the approved repository/project source material.

## Deliverables
- docs/product/vision.md
- docs/product/problem-statement.md

## Constraints
- Product definition only. No UI, schema, architecture, or implementation.
- Open-source/self-hostable BYOK is foundational.
- Evidence integrity and human-controlled consequential actions are foundational.
- Career OS is an autonomous job-search/application operating system, not a generic resume editor.

## Acceptance
- Clear target user and buyer problem.
- End-to-end product outcome stated in one page or less per document.
- v1 boundary is explicit.
- No unsupported implementation decisions.
""",
    },
    {
        "key": "P0-002",
        "title": "P0-002 — Personas and jobs-to-be-done",
        "control_acceptance": False,
        "after_control": True,
        "body": """DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS
AFTER_CONTROL_ACCEPTANCE: true

## Outcome
Define primary/secondary personas and jobs-to-be-done for Career OS.

## Deliverables
- docs/product/personas.md
- docs/product/jobs-to-be-done.md

## Constraints
- Product definition only.
- Do not design screens, database tables, or implementation.

## Acceptance
- Primary persona is explicit.
- Each JTBD maps to a measurable user outcome.
- Adjacent personas are separated from v1 scope.
""",
    },
    {
        "key": "P0-003",
        "title": "P0-003 — Scope, non-goals, success metrics and principles",
        "control_acceptance": False,
        "after_control": True,
        "body": """DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS
AFTER_CONTROL_ACCEPTANCE: true

## Outcome
Define the remaining Phase 0 product contract.

## Deliverables
- docs/product/scope.md
- docs/product/non-goals.md
- docs/product/success-metrics.md
- docs/product/product-principles.md
- docs/product/glossary.md

## Constraints
- Product definition only.
- No implementation.

## Acceptance
- v1 scope and later scope are separated.
- Non-goals prevent resume-builder/ATS/spam-product drift.
- Metrics include unsupported-claim rate, time-to-ready, accepted-job rate and application outcome measures.
- Principles include evidence before generation, explainability, human approval for consequential external actions, and BYOK/self-hosting.
""",
    },
]


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def ensure_extra_labels() -> None:
    labels = [
        (REVIEW_RUNNING, "FBCA04", "Independent reviewer dispatched"),
        (VERIFIED, "0E8A16", "Independent verification passed"),
    ]
    for name, colour, desc in labels:
        run(["gh", "label", "create", name, "--color", colour, "--description", desc, "--force"])


def all_issues() -> list[dict]:
    data = core.gh_json(["issue", "list", "--state", "all", "--limit", "200", "--json", "number,title,body,state,labels,url"])
    assert isinstance(data, list)
    return data


def issue_labels(issue: dict) -> set[str]:
    return {x["name"] for x in issue.get("labels", [])}


def seed_backlog() -> None:
    existing = {i["title"]: i for i in all_issues()}
    for spec in SEED:
        if spec["title"] in existing:
            continue
        cp = run(["gh", "issue", "create", "--title", spec["title"], "--body", spec["body"]])
        print(f"CREATED {spec['key']}: {cp.stdout.strip()}")


def control_acceptance_passed(issues: list[dict]) -> bool:
    for issue in issues:
        if re.search(r"(?im)^CONTROL_ACCEPTANCE:\s*true\s*$", issue.get("body") or ""):
            if issue.get("state") == "CLOSED" and VERIFIED in issue_labels(issue):
                return True
    return False


def promote_ready() -> None:
    issues = all_issues()
    control_ok = control_acceptance_passed(issues)
    for issue in issues:
        if issue.get("state") != "OPEN":
            continue
        body = issue.get("body") or ""
        current = issue_labels(issue)
        guarded = {
            core.LABELS["ready"], core.LABELS["running"], core.LABELS["review"],
            REVIEW_RUNNING, core.LABELS["blocker"], core.LABELS["decision"]
        }
        if current & guarded:
            continue
        gated = bool(re.search(r"(?im)^AFTER_CONTROL_ACCEPTANCE:\s*true\s*$", body))
        is_control = bool(re.search(r"(?im)^CONTROL_ACCEPTANCE:\s*true\s*$", body))
        ok, _ = core.controls_pass(body)
        if ok and (is_control or (gated and control_ok)):
            core.add_labels(int(issue["number"]), core.LABELS["ready"])
            print(f"READY #{issue['number']}: {issue['title']}")


def dispatch_review(issue: dict) -> None:
    number = int(issue["number"])
    worktree = ROOT / ".worktrees" / f"issue-{number}"
    if not worktree.exists():
        core.add_labels(number, core.LABELS["blocker"])
        raise RuntimeError(f"review worktree missing for #{number}")
    packet_dir = worktree / ".career-os"
    packet_dir.mkdir(exist_ok=True)
    packet = packet_dir / "REVIEW.md"
    packet.write_text(
        f"""# Independent review — GitHub #{number}

Review the implementation strictly against the GitHub issue, CLAUDE.md, STATE.md, linked specs/ADRs, and tests.

Required checks:
- scope matches issue
- deliverables exist
- tests/evidence support completion
- no unrelated architecture/product changes
- no unsupported factual claims in product documentation
- no destructive production actions

If PASS:
1. comment on the issue with `VERIFIED: PASS` and concise evidence;
2. add label `verified`;
3. remove `agent-review` and `review-running`;
4. close the issue as completed.

If FAIL:
1. comment `VERIFIED: FAIL` with exact failures;
2. remove `agent-review` and `review-running`;
3. add `agent-ready` for repair, unless the failure is systemic;
4. for systemic failure add `system-blocker` instead.

Do not implement fixes during review.
""",
        encoding="utf-8",
    )
    command = core.DISPATCH_TEMPLATE.format(
        cwd=shlex.quote(str(worktree)),
        agent=shlex.quote(REVIEW_AGENT),
        prompt_file=shlex.quote(str(packet)),
        issue=number,
    )
    core.add_labels(number, REVIEW_RUNNING)
    try:
        core.run_shell(command)
    except Exception:
        core.remove_label(number, REVIEW_RUNNING)
        core.add_labels(number, core.LABELS["blocker"])
        raise
    print(f"REVIEW DISPATCHED #{number}: {issue['title']}")


def review_cycle() -> None:
    for issue in core.issue_list(core.LABELS["review"]):
        if REVIEW_RUNNING not in issue_labels(issue):
            dispatch_review(issue)


def cycle() -> None:
    core.preflight()
    ensure_extra_labels()
    seed_backlog()
    review_cycle()
    if core.has_system_blocker():
        print("BLOCKED: system-blocker open")
        return
    promote_ready()
    control_ok = control_acceptance_passed(all_issues())
    core.WIP_LIMIT = 3 if control_ok else 1
    core.once()


def daemon() -> None:
    while True:
        try:
            cycle()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"ORCHESTRATOR ERROR: {exc}")
        time.sleep(POLL_SECONDS)


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["once", "daemon"])
    args = parser.parse_args()
    if args.command == "once":
        cycle()
    else:
        daemon()


if __name__ == "__main__":
    main()
