#!/usr/bin/env bash
# PreToolUse hook: block direct edits to vault.yml
# Ansible Vault files must be edited via: ansible-vault edit group_vars/all/vault.yml

set -euo pipefail

FILE=$(jq -r '.tool_input.file_path // .tool_input.notebook_path // empty' 2>/dev/null || echo "")

[[ -z "$FILE" ]] && exit 0

BASENAME=$(basename "$FILE")

if [[ "$BASENAME" == "vault.yml" ]]; then
  echo "BLOCKED: Direct edits to vault.yml are not allowed." >&2
  echo "Use: ansible-vault edit group_vars/all/vault.yml" >&2
  exit 2
fi
