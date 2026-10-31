#!/usr/bin/env bash
# Bazzite DX fallback while the base image omits steamos-manager/steamosctl.
set -euo pipefail
unset LD_PRELOAD LD_LIBRARY_PATH
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
if [[ "$mode" == game ]] && systemctl --user is-active --quiet gamescope-session-plus@steam.service; then
    echo 'Already in Game Mode; leaving the current display untouched.'
    exit 0
fi
if [[ "$mode" == desktop ]] && pgrep -u "$uid" -x gnome-shell >/dev/null; then
    echo 'Already in GNOME; leaving the current display untouched.'
    exit 0
fi
if [[ "${2:-}" != --worker ]]; then
    # Keep cleanup alive after Steam and its login session exit.
    exec systemd-run --user --collect --unit=bazzite-session-switch \
        /usr/bin/bash "$(readlink -f "$0")" "$mode" --worker
fi
if pgrep -u "$uid" -x gnome-shell >/dev/null; then
    exec gnome-session-quit --logout --no-prompt
fi
# End the user-manager graphical lifecycle, not just the loginctl seat. GNOME50
# refuses to start if graphical-session.target is still active from Gamescope.
if systemctl --user is-active --quiet gamescope-session-plus@steam.service; then
    exec systemctl --user stop gamescope-session.target graphical-session.target graphical-session-pre.target
fi
# Gamescope has no GNOME session manager. End only the local seat session.
sid="$(loginctl list-sessions --no-legend | awk -v uid="$uid" '$2 == uid && $4 == "seat0" {print $1; exit}')"
[[ -n "$sid" ]] || { echo 'No local seat session found.' >&2; exit 1; }
exec loginctl terminate-session "$sid"
