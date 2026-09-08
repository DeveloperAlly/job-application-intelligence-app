#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

if [[ "${HERDR_ENV:-}" != "1" ]]; then
  echo "BLOCKED: start this from a Herdr-managed pane (HERDR_ENV=1)." >&2
  exit 3
fi

mkdir -p .career-os/tasks .worktrees

python3 ops/herdr-coordinator/coordinator.py bootstrap
python3 ops/herdr-coordinator/orchestrator.py once
exec python3 ops/herdr-coordinator/orchestrator.py daemon
