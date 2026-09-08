#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

mkdir -p .career-os/tasks .worktrees

if [[ -f .career-os/herdr.env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .career-os/herdr.env
  set +a
fi

python3 tools/herdr-coordinator/coordinator.py bootstrap

cat <<'EOF'
PASS: local bootstrap complete.
Start persistent coordination with:
  set -a; source .career-os/herdr.env; set +a
  python3 tools/herdr-coordinator/coordinator.py daemon
EOF
