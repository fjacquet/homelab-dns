#!/usr/bin/env bash
# PostToolUse hook: run yamllint on YAML files after edit/write
# Skips vault.yml (encrypted) and mkdocs.yml (has !!python tags yamllint dislikes)

set -euo pipefail

FILE=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null || echo "")

[[ -z "$FILE" ]] && exit 0
[[ "$FILE" != *.yml ]] && exit 0
[[ "$(basename "$FILE")" == "vault.yml" ]] && exit 0
[[ "$(basename "$FILE")" == "mkdocs.yml" ]] && exit 0
[[ ! -f "$FILE" ]] && exit 0

# exit 2 + stderr so Claude sees the lint errors
if ! OUT=$(uv run --project "$CLAUDE_PROJECT_DIR" yamllint "$FILE" 2>&1); then
  echo "--- yamllint: $(basename "$FILE") ---" >&2
  echo "$OUT" >&2
  exit 2
fi
