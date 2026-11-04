#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$HOME/.local/share/hyde-ci/service" "$HOME/.config/systemd/user"
chmod 700 "$HOME/.local/share/hyde-ci/service"
podman build -t localhost/hyde-ci-linux:2.338.2 "$REPO_ROOT/config/hyde-ci"
install -m 644 "$REPO_ROOT/config/systemd/user/hyde-ci-linux.service" "$HOME/.config/systemd/user/hyde-ci-linux.service"
systemctl --user daemon-reload
systemctl --user enable --now hyde-ci-linux
