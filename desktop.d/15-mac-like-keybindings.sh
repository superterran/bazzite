#!/bin/bash
# Enable mac-like keybindings using keyd (Wayland-friendly)
# Maps Super (Command) combos to Control combos while preserving Super alone.

set -euo pipefail

echo "Configuring mac-like keybindings (Super -> Command-style combos)..."

# Ensure keyd is installed (layered)
if ! rpm -q keyd &>/dev/null; then
  echo "Queuing keyd install via rpm-ostree..."
  sudo rpm-ostree install keyd || true
  echo "A reboot will be required to start keyd."
fi

sudo mkdir -p /etc/keyd

CONF_PATH="/etc/keyd/default.conf"
if [[ ! -f "$CONF_PATH" ]]; then
  echo "Writing $CONF_PATH"
  sudo tee "$CONF_PATH" >/dev/null <<'EOF'
[ids]
leftmeta = overload(control, leftmeta)
rightmeta = overload(control, rightmeta)

[main]
meta.c = C-c
meta.v = C-v
meta.x = C-x
meta.z = C-z
meta.a = C-a
meta.s = C-s
meta.f = C-f
meta.t = C-t
meta.w = C-w
meta.q = C-q
meta.left = home
meta.right = end
meta.backspace = C-backspace
EOF
else
  echo "keyd config already exists; leaving as-is"
fi

# Enable and start keyd if present (will fail harmlessly if not installed yet)
if systemctl list-unit-files | grep -q '^keyd.service'; then
  sudo systemctl enable keyd.service || true
  sudo systemctl restart keyd.service || true
fi

echo "Mac-like keybindings configured. Reboot may be required if keyd was newly installed."