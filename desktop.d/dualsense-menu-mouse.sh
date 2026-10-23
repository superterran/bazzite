#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
/usr/bin/python3 -c 'import evdev'
sudo install -m644 "$REPO_ROOT/config/udev/rules.d/71-dualsense-touchpad.rules" /etc/udev/rules.d/71-dualsense-touchpad.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --action=change --subsystem-match=input
install -Dm644 "$REPO_ROOT/config/systemd/user/dualsense-menu-mouse.service" "$HOME/.config/systemd/user/dualsense-menu-mouse.service"
systemctl --user daemon-reload
systemctl --user enable --now dualsense-menu-mouse.service
