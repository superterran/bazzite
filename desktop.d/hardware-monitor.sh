#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 -c 'import gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk'
chmod +x "$REPO_ROOT/bin/hardware-monitor.py" "$REPO_ROOT/bin/launch-hardware-monitor.sh" "$REPO_ROOT/bin/setup-hardware-monitor.py"
mkdir -p "$HOME/.local/share/applications"
python3 -c 'from pathlib import Path; import sys; root=Path(sys.argv[1]); target=Path.home()/".local/share/applications/hardware-monitor.desktop"; target.write_text((root/"config/hardware-monitor.desktop.in").read_text().replace("@REPO_ROOT@",str(root)))' "$REPO_ROOT"
python3 "$REPO_ROOT/bin/setup-hardware-monitor.py"
