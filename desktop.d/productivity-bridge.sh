#!/usr/bin/env bash
# Isolated GNOME Wayland session and fixed-target TLS RDP/VNC bridge.
set -euo pipefail

# Retired in favor of the independent encrypted desktop. Explicit rollback only.
if [[ "${BAZZITE_ENABLE_LEGACY_PRODUCTIVITY:-0}" != 1 ]]; then
    echo 'Legacy productivity setup skipped; encrypted GNOME is the default.'
    exit 0
fi
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
account=desktop-remote
account_home=/var/home/desktop-remote
if ! id "$account" >/dev/null 2>&1; then
    sudo useradd --create-home --home-dir "$account_home" --shell /bin/bash \
        --comment 'Independent remote productivity desktop' "$account"
fi
account_uid=$(id -u "$account")
as_remote=(sudo -u "$account" env "HOME=$account_home" "XDG_RUNTIME_DIR=/run/user/$account_uid" "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$account_uid/bus")
sudo loginctl enable-linger "$account"

# The backend must never be exposed directly. Loopback is permitted by firewalld.
for scope in runtime permanent; do
    flags=()
    [[ "$scope" == permanent ]] && flags+=(--permanent)
    sudo firewall-cmd "${flags[@]}" --zone=moonlight-tailnet --add-port=3391/tcp
    for zone in FedoraWorkstation nm-shared docker moonlight-tailnet; do
        for family in ipv4 ipv6; do
            sudo firewall-cmd "${flags[@]}" --zone="$zone" --add-rich-rule="rule priority=\"-100\" family=\"$family\" port port=\"5902\" protocol=\"tcp\" drop"
        done
    done
done

sudo install -m 755 "$repo_root/bin/productivity-vnc-tls-adapter.py" /usr/local/libexec/productivity-vnc-tls-adapter.py
sudo install -d -o "$account" -g "$account" -m 700 "$account_home/.config/systemd/user"
sudo install -d -o "$account" -g "$account" -m 700 "$account_home/.config/environment.d" "$account_home/.config/systemd/user/gnome-remote-desktop-headless.service.d"
sudo install -o "$account" -g "$account" -m 644 "$repo_root/config/productivity-bridge/environment.conf" "$account_home/.config/environment.d/10-productivity.conf"
sudo install -o "$account" -g "$account" -m 644 "$repo_root/config/productivity-bridge/headless-session.conf" "$account_home/.config/systemd/user/gnome-remote-desktop-headless.service.d/session.conf"
for unit in remote-productivity-shell productivity-vnc-tls-adapter; do
    sudo install -o "$account" -g "$account" -m 644 "$repo_root/config/productivity-bridge/$unit.service" "$account_home/.config/systemd/user/"
done

# Transfer the existing credential only through anonymous stdin, not shell args.
python3 "$repo_root/bin/setup-productivity-credentials.py"
"${as_remote[@]}" /usr/bin/gsettings set org.gnome.desktop.remote-desktop.vnc encryption "['none']"
"${as_remote[@]}" /usr/bin/gsettings set org.gnome.desktop.session idle-delay 0
"${as_remote[@]}" /usr/bin/gsettings set org.gnome.desktop.screensaver lock-enabled false
"${as_remote[@]}" systemctl --user set-environment WAYLAND_DISPLAY=wayland-productivity XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=GNOME
"${as_remote[@]}" systemctl --user daemon-reload
"${as_remote[@]}" systemctl --user enable remote-productivity-shell.service gnome-remote-desktop-headless.service productivity-vnc-tls-adapter.service
"${as_remote[@]}" systemctl --user start remote-productivity-shell.service gnome-remote-desktop-headless.service productivity-vnc-tls-adapter.service

sudo install -d -m 700 /var/lib/productivity-bridge
if ! sudo test -s /var/lib/productivity-bridge/tls.key; then
    sudo openssl req -new -newkey rsa:3072 -nodes -x509 -days 365 \
        -subj /CN=desktop-productivity -addext subjectAltName=IP:100.119.114.55 \
        -keyout /var/lib/productivity-bridge/tls.key \
        -out /var/lib/productivity-bridge/tls.crt 2>/dev/null
    sudo chmod 600 /var/lib/productivity-bridge/tls.key
fi
sudo install -m 644 "$repo_root/config/productivity-bridge/xrdp.ini" /var/lib/productivity-bridge/xrdp.ini
if ! sudo podman image exists localhost/productivity-xrdp:test; then
    sudo podman build -t localhost/productivity-xrdp:test "$repo_root/config/productivity-bridge"
fi
if ! sudo podman container exists productivity-xrdp; then
    sudo podman create --name productivity-xrdp --network host --cap-drop all \
        --security-opt no-new-privileges \
        -v /var/lib/productivity-bridge/xrdp.ini:/etc/xrdp/productivity.ini:ro,Z \
        -v /var/lib/productivity-bridge/tls.key:/etc/xrdp/productivity-tls.key:ro,Z \
        -v /var/lib/productivity-bridge/tls.crt:/etc/xrdp/productivity-tls.crt:ro,Z \
        localhost/productivity-xrdp:test
fi
sudo install -m 644 "$repo_root/config/systemd/productivity-xrdp.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable productivity-xrdp.service
# Adopt only this experiment's manually started container during initial setup.
if ! sudo systemctl is-active --quiet productivity-xrdp.service; then
    sudo podman stop --time 5 productivity-xrdp >/dev/null || true
    sudo systemctl start productivity-xrdp.service
fi
