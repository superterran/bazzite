#!/usr/bin/env bash
set -euo pipefail
# Keep Steam's controller/application identity but discard injected libraries
# that break GTK/FreeRDP initialization outside Steam's own runtime.
exec env -u LD_PRELOAD -u LD_LIBRARY_PATH -u GTK_IM_MODULE -u WAYLAND_DISPLAY \
    DISPLAY="${DISPLAY:-:1}" GDK_BACKEND=x11 \
    /usr/bin/python3 "$HOME/repos/bazzite/bin/secure-desktop-tv.py"
