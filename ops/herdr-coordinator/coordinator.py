#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORKTREES = ROOT / ".worktrees"
TASK_DIR = ROOT / ".career-os" / "tasks"
DISPATCHER = ROOT / "ops" / "herdr-coordinator" / "herdr_dispatch.sh"
BASE_BRANCH = os.getenv("CAREER_OS_BASE_BRANCH", "main")
AGENT = os.getenv("CAREER_OS_AGENT", "claude")
WIP_LIMIT = int(os.getenv("CAREER_OS_WIP", "1"))
POLL_SECONDS = int(os.getenv("CAREER_OS_POLL_SECONDS", "60"))

LABELS = {
    "ready": "agent-ready",
    "running": "agent-running",
    "review": "agent-review",
    "blocker": "system-blocker",
    "decision": "decision-required",
}


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd or ROOT, text=True, capture_output=True, check=check)


def gh_json(args: list[str]) -> object:
    cp = run(["gh", *args])
    return json.loads(cp.stdout or "null")


def repo_name() -> str:
    return run(["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"]).stdout.strip()


def ensure_labels() -> None:
    labels = [
        (LABELS["ready"], "0E8A16", "Eligible for coordinator dispatch"),
        (LABELS["running"], "1D76DB", "Worker dispatched and running"),
        (LABELS["review"], "5319E7", "Worker finished; evidence/review required"),
        (LABELS["blocker"], "B60205", "Foundational/systemic blocker"),
        (LABELS["decision"], "D93F0B", "Human product/architecture decision required"),
    ]
    for name, colour, desc in labels:
        run(["gh", "label", "create", name, "--color", colour, "--description", desc, "--force"])


def preflight() -> None:
    for binary in ("git", "gh", "herdr", "python3"):
        if run(["sh", "-lc", f"command -v {shlex.quote(binary)}"], check=False).returncode != 0:
            raise SystemExit(f"BLOCKED: missing required binary: {binary}")
    if os.getenv("HERDR_ENV") != "1":
        raise SystemExit("BLOCKED: coordinator must run inside a Herdr-managed pane (HERDR_ENV=1)")
    if run(["gh", "auth", "status"], check=False).returncode != 0:
        raise SystemExit("BLOCKED: gh is not authenticated")
    if repo_name() != "DeveloperAlly/job-application-intelligence-app":
        raise SystemExit(f"BLOCKED: wrong repository: {repo_name()}")
    if not (ROOT / "STATE.md").exists() or not (ROOT / "CLAUDE.md").exists():
        raise SystemExit("BLOCKED: STATE.md and CLAUDE.md are required")
    if not DISPATCHER.exists():
        raise SystemExit(f"BLOCKED: native Herdr dispatcher missing: {DISPATCHER}")
    ensure_labels()


def issue_list(label: str) -> list[dict]:
    data = gh_json([
        "issue", "list", "--state", "open", "--label", label,
        "--limit", "100", "--json", "number,title,body,labels,url"
    ])
    assert isinstance(data, list)
    return data


def has_system_blocker() -> bool:
    return bool(issue_list(LABELS["blocker"]))


def controls_pass(body: str) -> tuple[bool, str]:
    checks = {
        "DEPENDENCIES_RESOLVED": r"(?im)^\s*DEPENDENCIES_RESOLVED\s*:\s*true\s*$",
        "PREFLIGHT": r"(?im)^\s*PREFLIGHT\s*:\s*(PASS|N/A)\s*$",
        "PHASE_GATE": r"(?im)^\s*PHASE_GATE\s*:\s*PASS\s*$",
    }
    missing = [name for name, pattern in checks.items() if not re.search(pattern, body or "")]
    return (not missing, "pass" if not missing else "missing/failed controls: " + ", ".join(missing))


def add_labels(number: int, *labels: str) -> None:
    run(["gh", "issue", "edit", str(number), "--add-label", ",".join(labels)])


def remove_label(number: int, label: str) -> None:
    run(["gh", "issue", "edit", str(number), "--remove-label", label], check=False)


def create_worktree(number: int) -> tuple[Path, str]:
    WORKTREES.mkdir(exist_ok=True)
    path = WORKTREES / f"issue-{number}"
    branch = f"agent/issue-{number}"
    if path.exists():
        return path, branch
    run(["git", "fetch", "origin", BASE_BRANCH])
    first = run(["git", "worktree", "add", "-b", branch, str(path), f"origin/{BASE_BRANCH}"], check=False)
    if first.returncode != 0:
        second = run(["git", "worktree", "add", str(path), branch], check=False)
        if second.returncode != 0:
            raise RuntimeError(first.stderr + "\n" + second.stderr)
    return path, branch


def build_prompt(issue: dict, worktree: Path) -> Path:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    text = (
        f"# Career OS worker packet — GitHub #{issue['number']}\n\n"
        f"Title: {issue['title']}\n"
        f"URL: {issue['url']}\n\n"
        "## Authoritative instructions\n"
        "1. Read CLAUDE.md and STATE.md before editing.\n"
        "2. Work only on this issue. Do not redesign unrelated architecture.\n"
        "3. Treat linked specs and ADRs as authoritative.\n"
        "4. On a foundational dependency failure: STOP; add `system-blocker`; remove `agent-running`; comment with root cause and verification plan.\n"
        "5. Do not apply destructive production migrations.\n"
        "6. Completion requires tests/evidence, a pushed branch, and a PR.\n"
        "7. On success: comment IMPLEMENTED / TEST RESULTS / CHANGED / PR; remove `agent-running`; add `agent-review`.\n\n"
        "## Issue\n\n"
        f"{issue.get('body') or ''}\n"
    )
    packet = TASK_DIR / f"issue-{issue['number']}.md"
    packet.write_text(text, encoding="utf-8")
    local_dir = worktree / ".career-os"
    local_dir.mkdir(exist_ok=True)
    local = local_dir / "TASK.md"
    local.write_text(text, encoding="utf-8")
    return local


def dispatch_agent(worktree: Path, agent_kind: str, prompt_file: Path, issue_number: int) -> None:
    cp = run([
        "bash", str(DISPATCHER), str(worktree), agent_kind, str(prompt_file), str(issue_number)
    ], check=False)
    if cp.stdout:
        print(cp.stdout, end="")
    if cp.returncode != 0:
        if cp.stderr:
            print(cp.stderr, file=sys.stderr, end="")
        raise RuntimeError(f"Herdr dispatch failed for issue #{issue_number} (exit {cp.returncode})")


def dispatch(issue: dict) -> None:
    number = int(issue["number"])
    ok, reason = controls_pass(issue.get("body") or "")
    if not ok:
        print(f"SKIP #{number}: {reason}")
        return
    worktree, _branch = create_worktree(number)
    prompt_file = build_prompt(issue, worktree)
    remove_label(number, LABELS["ready"])
    add_labels(number, LABELS["running"])
    try:
        dispatch_agent(worktree, AGENT, prompt_file, number)
    except Exception:
        remove_label(number, LABELS["running"])
        add_labels(number, LABELS["blocker"])
        raise
    print(f"DISPATCHED #{number}: {issue['title']}")


def once() -> None:
    preflight()
    if has_system_blocker():
        print("BLOCKED: open system-blocker issue exists; no dependent work dispatched")
        return
    running = issue_list(LABELS["running"])
    slots = max(0, WIP_LIMIT - len(running))
    if slots == 0:
        print(f"RUNNING: WIP limit reached ({WIP_LIMIT})")
        return
    dispatched = 0
    for issue in issue_list(LABELS["ready"]):
        if dispatched >= slots:
            break
        ok, _reason = controls_pass(issue.get("body") or "")
        if not ok:
            continue
        dispatch(issue)
        dispatched += 1
    if dispatched == 0:
        print("IDLE: no eligible agent-ready work")


def status() -> None:
    print(json.dumps({
        "repo": repo_name(),
        "ready": len(issue_list(LABELS["ready"])),
        "running": len(issue_list(LABELS["running"])),
        "review": len(issue_list(LABELS["review"])),
        "system_blockers": len(issue_list(LABELS["blocker"])),
        "decisions": len(issue_list(LABELS["decision"])),
        "wip_limit": WIP_LIMIT,
    }, indent=2))


def daemon() -> None:
    preflight()
    print(f"Career OS coordinator running; poll={POLL_SECONDS}s WIP={WIP_LIMIT}")
    while True:
        try:
            once()
        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"COORDINATOR ERROR: {exc}", file=sys.stderr)
        time.sleep(POLL_SECONDS)


def bootstrap() -> None:
    preflight()
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    WORKTREES.mkdir(exist_ok=True)
    print("PASS: coordinator preflight")
    status()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["bootstrap", "once", "daemon", "status"])
    args = parser.parse_args()
    if args.command == "bootstrap":
        bootstrap()
    elif args.command == "once":
        once()
    elif args.command == "daemon":
        daemon()
    else:
        status()


if __name__ == "__main__":
    main()
