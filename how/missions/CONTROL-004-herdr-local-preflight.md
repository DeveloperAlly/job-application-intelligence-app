# CONTROL-004 — Herdr local preflight

## State
READY FOR HUMAN-ONLY LOCAL STEP.

## Outcome
Resolve the only environment boundary ChatGPT cannot access: the installed local Herdr CLI and authenticated local repo environment.

## Why human-only
The runtime is on the local development machine. Cloud ChatGPT cannot execute or inspect local binaries.

## Required local command
From the root of the local clone of `DeveloperAlly/job-application-intelligence-app`, run:

```bash
printf '\n=== HERDR VERSION ===\n'
herdr --version || true
printf '\n=== HERDR AGENT START HELP ===\n'
herdr agent start --help || true
printf '\n=== HERDR AGENT PROMPT HELP ===\n'
herdr agent prompt --help || true
printf '\n=== HERDR PANE RUN HELP ===\n'
herdr pane run --help || true
printf '\n=== GH AUTH ===\n'
gh auth status
printf '\n=== REPO ===\n'
gh repo view --json nameWithOwner --jq .nameWithOwner
```

Paste the complete output back into the coordinator chat.

## Acceptance
- Local Herdr binary/version identified.
- Exact supported dispatch syntax identified from local CLI help.
- `gh` authenticated.
- Local clone resolves to the correct repository.

## Next automatic action
Once the output is supplied, update the bridge to the exact local Herdr syntax, remove the placeholder dispatch template requirement, then provide one final bootstrap command that starts the persistent coordinator.
