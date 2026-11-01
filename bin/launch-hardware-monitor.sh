#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
exec env -u LD_PRELOAD -u GTK_IM_MODULE GDK_BACKEND=x11 GDK_SCALE=2 GDK_DPI_SCALE=1 \
    /usr/bin/python3 "$REPO_ROOT/bin/hardware-monitor.py"
