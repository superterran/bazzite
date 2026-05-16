#!/bin/bash
# Open firewalld ports for Sunshine (Moonlight game streaming).
# Installs a 'sunshine' firewalld service definition and enables it in the
# active zone. Idempotent.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_XML="$SCRIPT_DIR/config/firewalld/services/sunshine.xml"
TARGET_XML="/etc/firewalld/services/sunshine.xml"

if [ ! -f "$SERVICE_XML" ]; then
    echo "ERROR: source file missing: $SERVICE_XML" >&2
    exit 1
fi

ZONE="$(sudo firewall-cmd --get-default-zone)"

# Install the service definition
if ! sudo cmp -s "$SERVICE_XML" "$TARGET_XML" 2>/dev/null; then
    echo "Installing firewalld service: sunshine"
    sudo install -m 0644 "$SERVICE_XML" "$TARGET_XML"
    sudo firewall-cmd --reload
else
    echo "firewalld service 'sunshine' already up to date"
fi

# Enable it in the active zone
if sudo firewall-cmd --zone="$ZONE" --query-service=sunshine >/dev/null 2>&1; then
    echo "Sunshine service already allowed in zone '$ZONE'"
else
    echo "Adding 'sunshine' service to zone '$ZONE' (permanent + runtime)"
    sudo firewall-cmd --permanent --zone="$ZONE" --add-service=sunshine
    sudo firewall-cmd --zone="$ZONE" --add-service=sunshine
fi

echo ""
echo "Sunshine firewall setup complete."
echo "Open ports: TCP 47984/47989/47990/48010, UDP 47998-48002 (excl. 48001)"
