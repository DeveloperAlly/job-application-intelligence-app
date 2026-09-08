#!/usr/bin/env bash
set -euo pipefail

CWD="$1"
AGENT_KIND="$2"
PROMPT_FILE="$3"
ISSUE="$4"

if [[ "${HERDR_ENV:-}" != "1" ]]; then
  echo "BLOCKED: coordinator must run inside a Herdr-managed pane (HERDR_ENV=1)" >&2
  exit 3
fi

case "$AGENT_KIND" in
  pi|claude|codex|gemini|cursor|devin|agy|cline|omp|mastracode|opencode|copilot|kimi|kiro|droid|amp|grok|hermes|kilo|qodercli|qwen|maki|muse) ;;
  *) echo "BLOCKED: unsupported Herdr agent kind: $AGENT_KIND" >&2; exit 4 ;;
esac

NAME="${AGENT_KIND}-issue-${ISSUE}"
NAME="$(printf '%s' "$NAME" | tr -cd 'a-z0-9_-' | cut -c1-32)"
PROMPT="$(cat "$PROMPT_FILE")"

SPLIT_JSON="$(herdr pane split --current --direction right --cwd "$CWD" --no-focus)"
PANE_ID="$(printf '%s' "$SPLIT_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')"

herdr agent start "$NAME" --kind "$AGENT_KIND" --pane "$PANE_ID" --timeout 120000
herdr agent prompt "$NAME" "$PROMPT" --wait --timeout 1800000

STATE_JSON="$(herdr agent get "$NAME")"
printf '%s\n' "$STATE_JSON"

STATUS="$(printf '%s' "$STATE_JSON" | python3 -c 'import json,sys; d=json.load(sys.stdin); print((d.get("result") or {}).get("agent",{}).get("state") or (d.get("result") or {}).get("state") or "unknown")')"
if [[ "$STATUS" == "blocked" ]]; then
  herdr agent read "$NAME" --source recent-unwrapped --lines 120 || true
  exit 5
fi
