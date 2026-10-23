#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
command -v 1password >/dev/null || { echo 'Install native 1Password first; Flatpak cannot supply its SSH agent.' >&2; exit 1; }
mkdir -p "$HOME/.config/systemd/user" "$HOME/.config/1Password/ssh"
install -m 644 "$REPO_ROOT/config/systemd/user/onepassword-private.service" "$HOME/.config/systemd/user/"
systemctl --user daemon-reload
systemctl --user enable --now onepassword-private.service
python3 "$REPO_ROOT/bin/setup-onepassword-tv.py"
