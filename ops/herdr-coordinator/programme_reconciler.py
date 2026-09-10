#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "how" / "programme.json"
READY = "agent-ready"
RUNNING = "agent-running"
REVIEW = "agent-review"
REVIEW_RUNNING = "review-running"
VERIFIED = "verified"
BLOCKER = "system-blocker"
DECISION = "decision-required"
PHASE_APPROVED = "phase-approved"


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def gh_json(args: list[str]) -> object:
    cp = run(["gh", *args])
    return json.loads(cp.stdout or "null")


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def all_issues() -> list[dict]:
    data = gh_json(["issue", "list", "--state", "all", "--limit", "500", "--json", "number,title,body,state,labels,url"])
    assert isinstance(data, list)
    return data


def labels(issue: dict) -> set[str]:
    return {x["name"] for x in issue.get("labels", [])}


def key_from_body(body: str) -> str | None:
    m = re.search(r"(?im)^PROGRAMME_KEY:\s*(\S+)\s*$", body or "")
    return m.group(1) if m else None


def task_key(phase_id: str, index: int) -> str:
    return f"{phase_id}-T{index:02d}"


def gate_key(phase_id: str) -> str:
    return f"{phase_id}-GATE"


def ensure_labels() -> None:
    for name, colour, desc in [
        (PHASE_APPROVED, "0E8A16", "Human phase gate approved"),
        (DECISION, "D93F0B", "Human decision required"),
    ]:
        run(["gh", "label", "create", name, "--color", colour, "--description", desc, "--force"])


def create_issue(title: str, body: str) -> None:
    run(["gh", "issue", "create", "--title", title, "--body", body])


def phase_task_body(phase: dict, key: str, task: str) -> str:
    return f"""PROGRAMME_KEY: {key}
PHASE: {phase['id']}
DEPENDENCIES_RESOLVED: true
PREFLIGHT: N/A
PHASE_GATE: PASS

## Outcome
Complete: {task}.

## Programme authority
`how/programme.json` is authoritative for sequence and scope. Work only on this task and the currently approved phase.

## Engineering process
Before implementation work, follow the required chain: product spec → UX → data/API contract → acceptance criteria → evals → implementation plan → code → tests → independent review.

## Completion
- Durable deliverable/evidence exists.
- Independent review passes.
- Issue closes with label `verified`.
"""


def phase_gate_body(phase: dict, key: str) -> str:
    return f"""PROGRAMME_KEY: {key}
PHASE: {phase['id']}
DEPENDENCIES_RESOLVED: false
PREFLIGHT: N/A
PHASE_GATE: BLOCKED
HUMAN_GATE: true

## Outcome
Approve completion of {phase['id']} — {phase['title']}.

## Gate criteria
- Every task in this phase is closed.
- Every task in this phase has label `verified`.
- No open `system-blocker` exists.
- Human explicitly approves advancement.

## Approval result
Close this issue and apply label `phase-approved`.
"""


def ensure_phase_issues(phase: dict, existing_by_key: dict[str, dict]) -> None:
    for idx, task in enumerate(phase["tasks"], start=1):
        key = task_key(phase["id"], idx)
        if key not in existing_by_key:
            create_issue(f"{key} — {task}", phase_task_body(phase, key, task))
    gkey = gate_key(phase["id"])
    if gkey not in existing_by_key:
        create_issue(f"{gkey} — {phase['gate']}", phase_gate_body(phase, gkey))


def issue_map() -> dict[str, dict]:
    result: dict[str, dict] = {}
    for issue in all_issues():
        key = key_from_body(issue.get("body") or "")
        if key:
            result[key] = issue
    return result


def is_complete(issue: dict) -> bool:
    return issue.get("state") == "CLOSED" and VERIFIED in labels(issue)


def gate_approved(issue: dict) -> bool:
    return issue.get("state") == "CLOSED" and PHASE_APPROVED in labels(issue)


def open_system_blocker() -> bool:
    data = gh_json(["issue", "list", "--state", "open", "--label", BLOCKER, "--limit", "1", "--json", "number"])
    return bool(data)


def add_label(number: int, label: str) -> None:
    run(["gh", "issue", "edit", str(number), "--add-label", label])


def remove_label(number: int, label: str) -> None:
    run(["gh", "issue", "edit", str(number), "--remove-label", label], check=False)


def set_gate_ready(gate: dict) -> None:
    number = int(gate["number"])
    body = gate.get("body") or ""
    body = re.sub(r"(?im)^DEPENDENCIES_RESOLVED:\s*false\s*$", "DEPENDENCIES_RESOLVED: true", body)
    body = re.sub(r"(?im)^PHASE_GATE:\s*BLOCKED\s*$", "PHASE_GATE: PASS", body)
    run(["gh", "issue", "edit", str(number), "--body", body, "--add-label", DECISION])


def reconcile() -> dict:
    ensure_labels()
    manifest = load_manifest()
    current = issue_map()

    # Seed only the current phase plus next phase after approval; this keeps GitHub usable while the manifest remains authoritative.
    for phase in manifest["phases"]:
        ensure_phase_issues(phase, current)
        current = issue_map()

    blocked = open_system_blocker()
    active_phase = None
    active_tasks: list[str] = []
    awaiting_gate = None

    for phase in manifest["phases"]:
        tasks = [current[task_key(phase["id"], i)] for i in range(1, len(phase["tasks"]) + 1)]
        gate = current[gate_key(phase["id"])]
        complete = all(is_complete(x) for x in tasks)

        if complete and not gate_approved(gate):
            if not blocked and DECISION not in labels(gate):
                set_gate_ready(gate)
            active_phase = phase["id"]
            awaiting_gate = gate_key(phase["id"])
            break

        if not complete:
            active_phase = phase["id"]
            if not blocked:
                guarded = {READY, RUNNING, REVIEW, REVIEW_RUNNING, BLOCKER, DECISION}
                candidates = [x for x in tasks if not is_complete(x) and not (labels(x) & guarded)]
                wip = manifest["rules"]["wip_after_control_acceptance"]
                currently_active = sum(1 for x in tasks if labels(x) & {READY, RUNNING, REVIEW, REVIEW_RUNNING})
                slots = max(0, wip - currently_active)
                for issue in candidates[:slots]:
                    add_label(int(issue["number"]), READY)
                    active_tasks.append(key_from_body(issue.get("body") or "") or str(issue["number"]))
            break

        # phase complete and gate approved: continue to next phase

    return {
        "active_phase": active_phase,
        "newly_ready": active_tasks,
        "awaiting_gate": awaiting_gate,
        "system_blocked": blocked,
    }


if __name__ == "__main__":
    print(json.dumps(reconcile(), indent=2))
