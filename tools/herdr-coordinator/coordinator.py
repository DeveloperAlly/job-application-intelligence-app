#!/usr/bin/env python3
"""Career OS persistent coordinator.

GitHub/aDNA hold durable state. This process enforces gates, dispatches bounded
work into Herdr, and watches GitHub for completion/blocker state.

No Herdr CLI syntax is guessed here. HERDR_DISPATCH_TEMPLATE is configured once
on the machine that runs Herdr. Required placeholders: {cwd}, {agent},
{prompt_file}, {issue}.
"""

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
BASE_BRANCH = os.getenv("CAREER_OS_BASE_BRANCH", "main")
AGENT = os.getenv("CAREER_OS_AGENT", "claude")
WIP_LIMIT = int(os.getenv("CAREER_OS_WIP", "3"))
POLL_SECONDS = int(os.getenv("CAREER_OS_POLL_SECONDS", "60"))
DISPATCH_TEMPLATE = os.getenv("HERDR_DISPATCH_TEMPLATE", "").strip()

LABELS = {
    "ready": "agent-ready",
    "running": "agent-running",
    "review": "agent-review",
    "blocker": "system-blocker",
    "decision": "decision-required",
}


def run(args: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd or ROOT, text=True, capture_output=True, check=check)


def run_shell(command: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd or ROOT, text=True, shell=True, capture_output=True, check=True)


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
    for binary in ("git", "gh", "herdr"):
        if run(["sh", "-lc", f"command -v {shlex.quote(binary)}"], check=False).returncode != 0:
            raise SystemExit(f"BLOCKED: missing required binary: {binary}")
    if run(["gh", "auth", "status"], check=False).returncode != 0:
        raise SystemExit("BLOCKED: gh is not authenticated")
    if not (ROOT / "STATE.md").exists() or not (ROOT / "CLAUDE.md").exists():
        raise SystemExit("BLOCKED: STATE.md and CLAUDE.md are required")
    if not DISPATCH_TEMPLATE:
        raise SystemExit(
            "BLOCKED: HERDR_DISPATCH_TEMPLATE is not configured. "
            "Set it once in .career-os/herdr.env using the local Herdr command that launches "
            "an agent for a cwd + prompt file."
        )
    for field in ("{cwd}", "{agent}", "{prompt_file}", "{issue}"):
        if field not in DISPATCH_TEMPLATE:
            raise SystemExit(f"BLOCKED: HERDR_DISPATCH_TEMPLATE missing placeholder {field}")
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
    if missing:
        return False, "missing/failed controls: " + ", ".join(missing)
    return True, "pass"


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
    cp = run(["git", "worktree", "add", "-b", branch, str(path), f"origin/{BASE_BRANCH}"], check=False)
    if cp.returncode != 0:
        # Idempotent recovery when branch already exists.
        cp2 = run(["git", "worktree", "add", str(path), branch], check=False)
        if cp2.returncode != 0:
            raise RuntimeError(cp.stderr + "\n" + cp2.stderr)
    return path, branch


def build_prompt(issue: dict, worktree: Path) -> Path:
    TASK_DIR.mkdir(parents=True, exist_ok=True)
    prompt_file = TASK_DIR / f"issue-{issue['number']}.md"
    prompt_file.write_text(
        f"""# Career OS worker packet — GitHub #{issue['number']}\n\n"
        f"Title: {issue['title']}\n"
        f"URL: {issue['url']}\n\n"
        "## Authoritative instructions\n"
        "1. Read CLAUDE.md and STATE.md before editing.\n"
        "2. Work only on this issue. Do not redesign unrelated architecture.\n"
        "3. Treat specs/ADRs linked by the issue as authoritative.\n"
        "4. If a foundational dependency fails, STOP. Add label `system-blocker`, remove `agent-running`, "
        "and comment with expected capability, observed failure, failure layer, alternatives, chosen resolution test.\n"
        "5. Do not apply destructive production migrations.\n"
        "6. Completion requires tests/evidence, a pushed branch, and a PR.\n"
        "7. On successful completion, comment IMPLEMENTED / TEST RESULTS / CHANGED / PR, remove `agent-running`, "
        "add `agent-review`.\n\n"
        "## Issue\n\n"
        f"{issue.get('body') or ''}\n",
        encoding="utf-8",
    )
    # Worker needs the packet inside its worktree as well.
    local_dir = worktree / ".career-os"
    local_dir.mkdir(exist_ok=True)
    local = local_dir / "TASK.md"
    local.write_text(prompt_file.read_text(encoding="utf-8"), encoding="utf-8")
    return local


def dispatch(issue: dict) -> None:
    number = int(issue["number"])
    ok, reason = controls_pass(issue.get("body") or "")
    if not ok:
        print(f"SKIP #{number}: {reason}")
        return
    worktree, _branch = create_worktree(number)
    prompt_file = build_prompt(issue, worktree)
    command = DISPATCH_TEMPLATE.format(
        cwd=shlex.quote(str(worktree)),
        agent=shlex.quote(AGENT),
        prompt_file=shlex.quote(str(prompt_file)),
        issue=number,
    )
    remove_label(number, LABELS["ready"])
    add_labels(number, LABELS["running"])
    try:
        run_shell(command)
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
    ready = issue_list(LABELS["ready"])
    dispatched = 0
    for issue in ready:
        if dispatched >= slots:
            break
        ok, _ = controls_pass(issue.get("body") or "")
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
    globals()[args.command]()


if __name__ == "__main__":
    main()
