#!/bin/bash
# Setup SSH for secure internet-accessible remote access
# This script hardens SSH (pubkey-only, non-standard port) and sets up
# Cloudflare DDNS so the machine is reachable at desktop.superterran.net:2222

set -euo pipefail

echo "Setting up SSH remote access with Cloudflare DDNS..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SSH_PORT=2222
CF_RECORD_NAME="desktop.superterran.net"
DDNS_ENV_FILE="/etc/cloudflare/ddns.env"
DDNS_SCRIPT="/usr/local/bin/cloudflare-ddns"

# ============================================================
# 1. Harden SSH for internet exposure
# ============================================================
echo "Configuring SSH hardening..."

HARDENED_CONF="/etc/ssh/sshd_config.d/00-hardened.conf"
if [[ -f "$HARDENED_CONF" ]] && grep -q "AuthenticationMethods publickey" "$HARDENED_CONF"; then
    echo "SSH hardening already configured."
else
    echo "Creating hardened SSH drop-in config..."
    sudo tee "$HARDENED_CONF" > /dev/null << 'SSHEOF'
# Hardened SSH for internet exposure
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
MaxAuthTries 3
MaxSessions 5
PubkeyAuthentication yes
AuthenticationMethods publickey
X11Forwarding no
PermitEmptyPasswords no
SSHEOF
    echo "SSH hardening config created."
fi

# ============================================================
# 2. Set SSH to listen on non-standard port
# ============================================================
echo "Configuring SSH port..."

PORT_CONF="/etc/ssh/sshd_config.d/01-port.conf"
if [[ -f "$PORT_CONF" ]] && grep -q "Port $SSH_PORT" "$PORT_CONF"; then
    echo "SSH port already set to $SSH_PORT."
else
    echo "Setting SSH listen port to $SSH_PORT..."
    sudo tee "$PORT_CONF" > /dev/null << PORTEOF
Port $SSH_PORT
PORTEOF
    echo "SSH port config created."
fi

# Allow the port in SELinux
if command -v semanage >/dev/null 2>&1; then
    if ! semanage port -l | grep ssh_port_t | grep -q "$SSH_PORT"; then
        echo "Adding port $SSH_PORT to SELinux SSH policy..."
        sudo semanage port -a -t ssh_port_t -p tcp "$SSH_PORT" 2>/dev/null \
            || sudo semanage port -m -t ssh_port_t -p tcp "$SSH_PORT"
    else
        echo "SELinux already allows SSH on port $SSH_PORT."
    fi
fi

# Validate and apply SSH config
echo "Validating SSH configuration..."
if sudo sshd -t; then
    echo "SSH config valid, restarting sshd..."
    sudo systemctl restart sshd
    echo "sshd restarted on port $SSH_PORT."
else
    echo "ERROR: SSH config validation failed, not restarting." >&2
    exit 1
fi

# ============================================================
# 3. Configure firewall
# ============================================================
echo "Configuring firewall..."

if command -v firewall-cmd >/dev/null 2>&1; then
    if ! sudo firewall-cmd --list-ports | grep -q "${SSH_PORT}/tcp"; then
        sudo firewall-cmd --add-port="${SSH_PORT}/tcp" --permanent
        echo "Port $SSH_PORT added to firewall."
    else
        echo "Port $SSH_PORT already open in firewall."
    fi

    # Remove default SSH port if open
    if sudo firewall-cmd --list-services | grep -q '\bssh\b'; then
        sudo firewall-cmd --remove-service=ssh --permanent
        echo "Removed default SSH service (port 22) from firewall."
    fi

    sudo firewall-cmd --reload
    echo "Firewall reloaded."
else
    echo "No firewall-cmd found, skipping firewall configuration."
fi

# ============================================================
# 4. Setup Cloudflare DDNS
# ============================================================
echo "Setting up Cloudflare DDNS for $CF_RECORD_NAME..."

# Check for credentials
if [[ ! -f "$DDNS_ENV_FILE" ]]; then
    echo ""
    echo "Cloudflare DDNS credentials not found at $DDNS_ENV_FILE"
    echo "Please create it with the following format:"
    echo ""
    echo "  CF_AUTH_EMAIL=your-cloudflare-email"
    echo "  CF_AUTH_KEY=your-cloudflare-global-api-key"
    echo "  CF_ZONE_ID=your-zone-id"
    echo "  CF_RECORD_ID=your-dns-record-id"
    echo "  CF_RECORD_NAME=$CF_RECORD_NAME"
    echo ""
    echo "Then re-run this script."
    exit 1
fi

sudo chmod 600 "$DDNS_ENV_FILE"
sudo chown root:root "$DDNS_ENV_FILE"
echo "DDNS credentials file secured."

# Install the DDNS update script
echo "Installing DDNS update script..."
sudo tee "$DDNS_SCRIPT" > /dev/null << 'DDNSEOF'
#!/bin/bash
set -euo pipefail

source /etc/cloudflare/ddns.env

# Get current public IP
CURRENT_IP=$(curl -4 -sf ifconfig.me || curl -4 -sf icanhazip.com)
if [[ -z "$CURRENT_IP" ]]; then
    echo "Failed to get public IP" >&2
    exit 1
fi

# Get IP currently in DNS
DNS_IP=$(curl -sf -X GET "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/${CF_RECORD_ID}" \
    -H "X-Auth-Email: ${CF_AUTH_EMAIL}" \
    -H "X-Auth-Key: ${CF_AUTH_KEY}" \
    -H "Content-Type: application/json" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['content'])")

if [[ "$CURRENT_IP" == "$DNS_IP" ]]; then
    echo "IP unchanged: $CURRENT_IP"
    exit 0
fi

# Update the record
RESULT=$(curl -sf -X PUT "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records/${CF_RECORD_ID}" \
    -H "X-Auth-Email: ${CF_AUTH_EMAIL}" \
    -H "X-Auth-Key: ${CF_AUTH_KEY}" \
    -H "Content-Type: application/json" \
    --data "{\"type\":\"A\",\"name\":\"${CF_RECORD_NAME}\",\"content\":\"${CURRENT_IP}\",\"ttl\":300,\"proxied\":false}")

SUCCESS=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['success'])")
if [[ "$SUCCESS" == "True" ]]; then
    echo "Updated: $DNS_IP -> $CURRENT_IP"
else
    echo "Update failed: $RESULT" >&2
    exit 1
fi
DDNSEOF
sudo chmod 755 "$DDNS_SCRIPT"
echo "DDNS script installed at $DDNS_SCRIPT."

# ============================================================
# 5. Setup systemd timer for DDNS
# ============================================================
echo "Setting up DDNS systemd timer..."

sudo tee /etc/systemd/system/cloudflare-ddns.service > /dev/null << 'SVCEOF'
[Unit]
Description=Cloudflare DDNS Update
After=network-online.target nss-lookup.target
Wants=network-online.target nss-lookup.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/cloudflare-ddns
Restart=on-failure
RestartSec=30
RestartMaxDelaySec=5min
SVCEOF

sudo tee /etc/systemd/system/cloudflare-ddns.timer > /dev/null << 'TMREOF'
[Unit]
Description=Cloudflare DDNS Update Timer

[Timer]
OnBootSec=30
OnUnitActiveSec=5min
RandomizedDelaySec=30

[Install]
WantedBy=timers.target
TMREOF

sudo systemctl daemon-reload
sudo systemctl enable --now cloudflare-ddns.timer
echo "DDNS timer enabled (updates every 5 minutes)."

# Run an initial update
echo "Running initial DDNS update..."
sudo systemctl start cloudflare-ddns.service
sudo journalctl -u cloudflare-ddns.service --no-pager -n 3

# ============================================================
# Verification
# ============================================================
echo ""
echo "Verifying configuration..."
echo "- SSH port: $(sudo ss -tlnp | grep sshd | head -1 | awk '{print $4}')"
echo "- SSH auth: pubkey only (passwords disabled)"
echo "- DDNS timer: $(systemctl is-active cloudflare-ddns.timer)"
echo "- DNS resolution: $(dig +short $CF_RECORD_NAME)"
echo "- Public IP: $(curl -4 -sf ifconfig.me)"

echo ""
echo "SSH Remote Access Setup Complete!"
echo "================================="
echo ""
echo "Connect from anywhere:"
echo "  ssh -p $SSH_PORT $(whoami)@$CF_RECORD_NAME"
echo ""
echo "Suggested SSH client config (~/.ssh/config):"
echo "  Host desktop"
echo "      HostName $CF_RECORD_NAME"
echo "      Port $SSH_PORT"
echo "      User $(whoami)"
echo ""
echo "For Apple Shortcuts / iOS:"
echo "  Host: $CF_RECORD_NAME"
echo "  Port: $SSH_PORT"
echo ""
echo "DDNS credentials: $DDNS_ENV_FILE"
echo "DDNS update logs: journalctl -u cloudflare-ddns"
