#!/usr/bin/env bash
# Keep encrypted Jump3392 and gaming Moonlight; preserve legacy home data.
set -euo pipefail
if ! sudo test -s /etc/productivity-secure.json; then
    echo 'Encrypted desktop is not provisioned; leaving legacy access intact.'
    exit 0
fi
sudo systemctl disable --now productivity-xrdp.service
if id desktop-remote >/dev/null 2>&1; then
    old_uid=$(id -u desktop-remote)
    old_gid=$(id -g desktop-remote)
    if sudo systemctl is-active --quiet "user@$old_uid.service"; then
        sudo setpriv "--reuid=$old_uid" "--regid=$old_gid" --init-groups \
            env HOME=/var/home/desktop-remote "XDG_RUNTIME_DIR=/run/user/$old_uid" \
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$old_uid/bus" \
            systemctl --user disable --now productivity-vnc-tls-adapter.service \
            gnome-remote-desktop-headless.service remote-productivity-shell.service
    fi
    sudo loginctl disable-linger desktop-remote
    sudo systemctl stop "user@$old_uid.service"
fi
/usr/bin/gsettings set org.gnome.desktop.remote-desktop.rdp enable false
/usr/bin/gsettings set org.gnome.desktop.remote-desktop.vnc enable false
systemctl --user disable --now gnome-remote-desktop.service
override="$HOME/.config/systemd/user/gnome-remote-desktop.service.d/jump-compat.conf"
if [[ -f "$override" ]] && /usr/bin/grep -q launch-gnome-rdp-compat.sh "$override"; then
    rm "$override"
fi
rm -rf "$HOME/.local/lib/gnome-rdp-jump-compat"
systemctl --user daemon-reload
for scope in runtime permanent; do
    flags=()
    [[ "$scope" == permanent ]] && flags+=(--permanent)
    for port in 3389 3391 5901; do
        if sudo firewall-cmd "${flags[@]}" --zone=moonlight-tailnet --query-port="$port/tcp" >/dev/null; then
            sudo firewall-cmd "${flags[@]}" --zone=moonlight-tailnet --remove-port="$port/tcp"
        fi
    done
done
echo 'Legacy test endpoints retired; old account data preserved. Encrypted3392 unchanged.'
