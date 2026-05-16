#!/usr/bin/env bash
# Headless GNOME compositor — for Sunshine streaming alongside Gamescope.
#
# Runs gnome-shell as a wayland compositor with a virtual-monitor (no physical
# output), exposing a named WAYLAND_DISPLAY socket. Sunshine captures that
# socket; the local Gamescope session on HDMI is untouched.
#
# Tunables (env):
#   WAYLAND_DISPLAY  Wayland socket name (default: wayland-headless)
#   HEADLESS_RES     Virtual monitor mode (default: 2560x1440@60)

set -euo pipefail

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
export XDG_SESSION_TYPE=wayland
export XDG_CURRENT_DESKTOP=GNOME
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-headless}"

HEADLESS_RES="${HEADLESS_RES:-2560x1440@60}"

exec /usr/bin/gnome-shell \
    --wayland \
    --no-x11 \
    --headless \
    --virtual-monitor "${HEADLESS_RES}" \
    --wayland-display "${WAYLAND_DISPLAY}"
