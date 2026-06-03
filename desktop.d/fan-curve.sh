#!/bin/bash
# Install the quiet AIO fan curve service (system-level, requires sudo).
# - Loads nct6775 at boot (exposes the NCT6799 Super I/O fan controls)
# - Re-applies the pwm2 curve at boot (BIOS reprograms SuperIO on power cycle)

set -euo pipefail

echo "Installing fan-curve module + service..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

sudo install -m 0644 "$SCRIPT_DIR/config/modules-load.d/nct6775.conf" /etc/modules-load.d/nct6775.conf
sudo install -m 0755 "$SCRIPT_DIR/bin/fan-curve.sh"                     /usr/local/bin/fan-curve.sh
sudo install -m 0644 "$SCRIPT_DIR/config/systemd/system/fan-curve.service" /etc/systemd/system/fan-curve.service

# Make sure the module is loaded now so the first ExecStart finds the hwmon
sudo modprobe nct6775 || true

sudo systemctl daemon-reload
sudo systemctl enable --now fan-curve.service

echo
echo "Done. Verify with:"
echo "  systemctl status fan-curve"
echo "  sensors | grep -A1 nct6799"
