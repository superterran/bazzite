#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
if ! systemctl is-enabled --quiet productivity-push.service; then
    echo 'Phone approval service required before installing Secure Desktop TV.'
    exit 0
fi
if [[ ! -x /home/linuxbrew/.linuxbrew/bin/xfreerdp ]]; then
    brew install freerdp
fi
# Refresh only the public certificate pin; never read the gateway private key.
sudo openssl x509 -in /var/lib/productivity-secure-bridge/tls.crt -noout -fingerprint -sha256 |
    cut -d= -f2 > "$repo_root/config/secure-productivity/viewer-cert.sha256"
if mountpoint -q /var/home/desktop-secure && sudo test -f /var/home/desktop-secure/.local/share/gnome-remote-desktop/native-rdp/tls.crt; then
    sudo openssl x509 -in /var/home/desktop-secure/.local/share/gnome-remote-desktop/native-rdp/tls.crt -noout -fingerprint -sha256 |
        cut -d= -f2 > "$repo_root/config/secure-productivity/native-rdp-cert.sha256"
fi
/usr/bin/python3 "$repo_root/bin/setup-secure-desktop-tv.py"
