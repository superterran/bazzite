#!/usr/bin/env bash
# Bazzite DX fallback while the base image omits steamos-manager/steamosctl.
set -euo pipefail
mode="${1:-game}"
case "$mode" in
  game) session=gamescope-session-steam ;;
  desktop) session=gnome ;;
  *) echo 'Usage: switch-bazzite-session.sh game|desktop [--prepare-only]' >&2; exit 2 ;;
esac
[[ -f "/usr/share/wayland-sessions/$session.desktop" ]]
uid="$(id -u)"
# Update only our own account's display-manager selection. Do not restart GDM:
# that would kill the session instead of giving applications a normal logout.
sudo -n busctl call org.freedesktop.Accounts "/org/freedesktop/Accounts/User$uid" org.freedesktop.Accounts.User SetSession s "$session"
sudo -n busctl call org.freedesktop.Accounts "/org/freedesktop/Accounts/User$uid" org.freedesktop.Accounts.User SetXSession s "$session"
sudo -n busctl call org.freedesktop.Accounts "/org/freedesktop/Accounts/User$uid" org.freedesktop.Accounts.User SetSessionType s wayland
if [[ "${2:-}" == --prepare-only ]]; then
    printf 'Next login session: %s\n' "$session"
    exit 0
fi
if pgrep -u "$uid" -x gnome-shell >/dev/null; then
    exec gnome-session-quit --logout --no-prompt
fi
# Gamescope has no GNOME session manager. End only the local seat session.
sid="$(loginctl list-sessions --no-legend | awk -v uid="$uid" '$2 == uid && $4 == "seat0" {print $1; exit}')"
[[ -n "$sid" ]] || { echo 'No local seat session found.' >&2; exit 1; }
exec loginctl terminate-session "$sid"
