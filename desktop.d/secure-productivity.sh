#!/usr/bin/env bash
# Deploy the separate encrypted endpoint; never replace the working3391 desktop.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
sudo test -s /etc/productivity-secure.json

# TLS identities authenticate the gateway to the root broker. These are not
# volume-unlock keys; the LUKS passphrase is supplied only by the remote login.
tls=/var/lib/productivity-secure-bridge/unlock-tls
sudo install -d -m 700 "$tls/client"
if ! sudo test -s "$tls/ca.key"; then
    sudo openssl req -x509 -newkey rsa:3072 -nodes -days 3650 \
        -subj /CN=productivity-unlock-CA -addext basicConstraints=critical,CA:TRUE \
        -addext keyUsage=critical,keyCertSign,cRLSign \
        -keyout "$tls/ca.key" -out "$tls/ca.crt" 2>/dev/null
fi
if ! sudo test -s "$tls/server.crt"; then
    sudo openssl req -new -newkey rsa:3072 -nodes -subj /CN=productivity-unlock \
        -keyout "$tls/server.key" -out "$tls/server.csr" 2>/dev/null
    sudo openssl x509 -req -in "$tls/server.csr" -CA "$tls/ca.crt" -CAkey "$tls/ca.key" \
        -CAcreateserial -days 825 -out "$tls/server.crt" \
        -extfile "$repo_root/config/secure-productivity/unlock-server.cnf"
fi
if ! sudo test -s "$tls/client/client.crt"; then
    sudo openssl req -new -newkey rsa:3072 -nodes -subj /CN=productivity-gateway \
        -keyout "$tls/client/client.key" -out "$tls/client/client.csr" 2>/dev/null
    sudo openssl x509 -req -in "$tls/client/client.csr" -CA "$tls/ca.crt" -CAkey "$tls/ca.key" \
        -CAcreateserial -days 825 -out "$tls/client/client.crt" \
        -extfile "$repo_root/config/secure-productivity/unlock-client.cnf"
fi
sudo cp "$tls/ca.crt" "$tls/client/ca.crt"
sudo find "$tls" -name '*.key' -exec chmod 600 {} +

for scope in runtime permanent; do
    flags=()
    [[ "$scope" == permanent ]] && flags+=(--permanent)
    sudo firewall-cmd "${flags[@]}" --zone=moonlight-tailnet --add-port=3392/tcp
    for zone in FedoraWorkstation nm-shared docker moonlight-tailnet; do
        for family in ipv4 ipv6; do
            sudo firewall-cmd "${flags[@]}" --zone="$zone" --add-rich-rule="rule priority=\"-100\" family=\"$family\" port port=\"5914\" protocol=\"tcp\" drop"
        done
    done
done
for script in productivity-volume-broker.py productivity-pam-unlock.py productivity-vnc-tls-adapter.py; do
    sudo install -m 755 "$repo_root/bin/$script" "/usr/local/libexec/$script"
done
sudo install -m 644 "$repo_root/config/secure-productivity/pam-host-session" /etc/pam.d/productivity-secure
for unit in productivity-volume-broker.service productivity-secure-xrdp.service productivity-secure-session@.service; do
    sudo install -m 644 "$repo_root/config/systemd/$unit" /etc/systemd/system/
done
sudo systemctl daemon-reload
sudo systemctl enable --now productivity-volume-broker.service

sudo install -d -m 700 /var/lib/productivity-secure-bridge
if ! sudo test -s /var/lib/productivity-secure-bridge/tls.key; then
    sudo openssl req -new -newkey rsa:3072 -nodes -x509 -days 365 \
        -subj /CN=desktop-secure -addext subjectAltName=IP:100.119.114.55 \
        -keyout /var/lib/productivity-secure-bridge/tls.key \
        -out /var/lib/productivity-secure-bridge/tls.crt 2>/dev/null
    sudo chmod 600 /var/lib/productivity-secure-bridge/tls.key
fi
sudo install -m 644 "$repo_root/config/secure-productivity/xrdp.ini" /var/lib/productivity-secure-bridge/xrdp.ini
if ! sudo podman image exists localhost/productivity-secure-xrdp:test; then
    sudo podman build -t localhost/productivity-secure-xrdp:test -f "$repo_root/config/secure-productivity/Containerfile" "$repo_root"
fi
if ! sudo podman container exists productivity-secure-xrdp; then
    sudo podman create --name productivity-secure-xrdp --network host --cap-drop all \
        --security-opt no-new-privileges \
        -v /var/lib/productivity-secure-bridge/xrdp.ini:/etc/xrdp/secure-productivity.ini:ro,Z \
        -v /var/lib/productivity-secure-bridge/tls.key:/etc/xrdp/productivity-tls.key:ro,Z \
        -v /var/lib/productivity-secure-bridge/tls.crt:/etc/xrdp/productivity-tls.crt:ro,Z \
        -v /var/lib/productivity-secure-bridge/unlock-tls/client:/etc/productivity-unlock:ro,Z \
        localhost/productivity-secure-xrdp:test
fi
sudo systemctl enable --now productivity-secure-xrdp.service
