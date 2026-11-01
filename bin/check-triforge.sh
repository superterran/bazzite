#!/usr/bin/env bash
set -euo pipefail
repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
state_dir="$HOME/.local/state/triforge-watch"
mkdir -p "$state_dir"
exec 9>"$state_dir/run.lock"
flock -n 9 || exit 0
[[ ! -f "$state_dir/installed-both" ]] || exit 0
export PATH="$HOME/.local/bin:/home/linuxbrew/.linuxbrew/bin:/usr/local/bin:/usr/bin:/bin"
if [[ "${1:-}" == --check ]]; then
    command -v codex
    codex login status
    test -r "$repo_dir/config/triforge-watch-prompt.txt"
    exit 0
fi
codex --search --ask-for-approval never exec --sandbox danger-full-access \
    --cd "$repo_dir" --output-last-message "$state_dir/latest-report.md" \
    - < "$repo_dir/config/triforge-watch-prompt.txt"
date -Iseconds > "$state_dir/last-successful-run"
if [[ -f "$state_dir/installed-both" ]]; then
    notify-send 'Triforge installed' 'Steam setup and sync verified on desktop and Ally.' || true
    systemctl --user disable --now triforge-watch.timer
fi
