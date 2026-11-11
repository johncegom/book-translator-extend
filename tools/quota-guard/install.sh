#!/usr/bin/env bash
# Installs (or with --uninstall removes) the quota-guard mod into the local Claude Code of the current user.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
market="quota-guard-local"
plugin="quota-guard@${market}"

command -v claude >/dev/null 2>&1 || { echo "The 'claude' command is not on PATH. Install Claude Code first." >&2; exit 1; }

if [ "${1:-}" = "--uninstall" ]; then
  claude plugin uninstall "$plugin" || true
  claude plugin marketplace remove "$market" || true
  echo "quota-guard removed. Restart Claude Code or run /reload-plugins."
  exit 0
fi

claude plugin validate "$here"

# Reads the mod from this folder: do not move or delete it while the mod is installed.
if ! claude plugin marketplace list 2>&1 | grep -q "$market"; then
  claude plugin marketplace add "$here"
fi
claude plugin install "$plugin" --scope user --config threshold=85

echo
echo "Installed. In a running Claude Code session type /reload-plugins (or restart it)."
echo "The threshold defaults to 85 (percent of the 5-hour window). Change it with:  claude plugin configure quota-guard"
