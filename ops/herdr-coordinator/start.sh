#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

mkdir -p .career-os/tasks .worktrees

if [[ ! -f .career-os/herdr.env ]]; then
  cp ops/herdr-coordinator/herdr.env.example .career-os/herdr.env
  echo "BLOCKED: edit .career-os/herdr.env once and set HERDR_DISPATCH_TEMPLATE to the exact local Herdr launch command."
  exit 2
fi

set -a
# shellcheck disable=SC1091
source .career-os/herdr.env
set +a

python3 ops/herdr-coordinator/coordinator.py bootstrap
python3 ops/herdr-coordinator/orchestrator.py once
exec python3 ops/herdr-coordinator/orchestrator.py daemon
