#!/bin/bash
# Fix SSH Connection Stability Issues
# This script addresses WiFi power saving and SSH configuration issues that cause unstable connections

set -euo pipefail

echo "Fixing SSH connection stability issues..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 1. Fix WiFi Power Saving (Primary Issue)
echo "Checking WiFi power saving configuration..."

# Get WiFi interface name
WIFI_INTERFACE=$(iw dev | awk '/Interface/ {print $2}' | head -1)

if [[ -n "$WIFI_INTERFACE" ]]; then
    echo "WiFi interface detected: $WIFI_INTERFACE"
    
    # Check current power save status
    CURRENT_POWERSAVE=$(iw dev "$WIFI_INTERFACE" get power_save 2>/dev/null | grep -o "on\|off" || echo "unknown")
    echo "Current WiFi power saving: $CURRENT_POWERSAVE"
    
    if [[ "$CURRENT_POWERSAVE" == "on" ]]; then
        echo "Disabling WiFi power saving (immediate fix)..."
        sudo iw dev "$WIFI_INTERFACE" set power_save off
        echo "✓ WiFi power saving disabled immediately"
    else
        echo "✓ WiFi power saving already disabled"
    fi
    
    # Create permanent fix service
    if [[ ! -f /etc/systemd/system/disable-wifi-powersave.service ]]; then
        echo "Creating permanent WiFi power saving disable service..."
        sudo tee /etc/systemd/system/disable-wifi-powersave.service > /dev/null <<SERVICEEOF
[Unit]
Description=Disable WiFi Power Saving for SSH Stability
After=multi-user.target network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c '\
IW=\$(command -v iw || echo /usr/sbin/iw); \
WIFI_IF=\$("$IW" dev | awk "/Interface/ {print \$2}" | head -1); \
if [[ -n "\$WIFI_IF" ]]; then "$IW" dev "\$WIFI_IF" set power_save off; fi'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
SERVICEEOF
        
        sudo systemctl enable disable-wifi-powersave.service
        sudo systemctl start disable-wifi-powersave.service
        echo "✓ Permanent WiFi power saving disable service created and enabled"
    else
        echo "✓ WiFi power saving disable service already exists"
    fi
else
    echo "⚠ No WiFi interface detected, skipping WiFi power management fixes"
fi

# 2. Fix SSH Server Configuration
echo "Configuring SSH server for better stability..."

SSH_CONFIG_BACKUP="/etc/ssh/sshd_config.bak-$(date +%Y%m%d)"
if [[ ! -f "$SSH_CONFIG_BACKUP" ]]; then
    echo "Creating SSH config backup..."
    sudo cp /etc/ssh/sshd_config "$SSH_CONFIG_BACKUP"
    echo "✓ SSH config backed up to $SSH_CONFIG_BACKUP"
fi

# Add SSH stability settings if not already present
SSH_STABILITY_MARKER="# SSH Stability Settings Added by Bazzite Setup"
if ! grep -q "$SSH_STABILITY_MARKER" /etc/ssh/sshd_config; then
    echo "Adding SSH stability configuration..."
    sudo tee -a /etc/ssh/sshd_config > /dev/null <<SSHEOF

$SSH_STABILITY_MARKER
ClientAliveInterval 60
ClientAliveCountMax 3
TCPKeepAlive yes
SSHEOF
    
    echo "✓ SSH server stability settings added"
    
    # Reload SSH daemon
    echo "Reloading SSH daemon..."
    sudo systemctl reload sshd.service
    echo "✓ SSH daemon reloaded with new settings"
else
    echo "✓ SSH stability settings already configured"
fi

# 3. Fix SSH Client Configuration
echo "Configuring SSH client for better stability..."

SSH_CLIENT_CONFIG="$HOME/.ssh/config"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Create backup of existing config
if [[ -f "$SSH_CLIENT_CONFIG" ]] && [[ ! -f "$SSH_CLIENT_CONFIG.bak-$(date +%Y%m%d)" ]]; then
    cp "$SSH_CLIENT_CONFIG" "$SSH_CLIENT_CONFIG.bak-$(date +%Y%m%d)"
    echo "✓ SSH client config backed up"
fi

# Add stability settings if not present
CLIENT_STABILITY_MARKER="# SSH Client Stability Settings Added by Bazzite Setup"
if [[ ! -f "$SSH_CLIENT_CONFIG" ]] || ! grep -q "$CLIENT_STABILITY_MARKER" "$SSH_CLIENT_CONFIG"; then
    echo "Adding SSH client stability configuration..."
    tee -a "$SSH_CLIENT_CONFIG" > /dev/null <<CLIENTEOF

$CLIENT_STABILITY_MARKER
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ConnectTimeout 10
CLIENTEOF
    
    chmod 600 "$SSH_CLIENT_CONFIG"
    echo "✓ SSH client stability settings added"
else
    echo "✓ SSH client stability settings already configured"
fi

# 4. Fix USB Power Management for WiFi adapters
echo "Configuring USB power management for network stability..."

USB_RULE_FILE="/etc/udev/rules.d/50-usb-wifi-no-suspend.rules"
if [[ ! -f "$USB_RULE_FILE" ]]; then
    echo "Creating udev rule to prevent WiFi adapter suspension..."
    sudo tee "$USB_RULE_FILE" > /dev/null <<UDEVEOF
# Disable autosuspend for WiFi adapters to prevent SSH disconnections
ACTION=="add", SUBSYSTEM=="usb", ATTR{bInterfaceClass}=="e0", ATTR{power/autosuspend}="-1"
UDEVEOF
    
    sudo udevadm control --reload-rules
    echo "✓ USB WiFi adapter autosuspend prevention rule created"
else
    echo "✓ USB WiFi adapter autosuspend rule already exists"
fi

# 5. Verify current settings
echo ""
echo "Verifying current configuration..."

if [[ -n "$WIFI_INTERFACE" ]]; then
    CURRENT_PS=$(iw dev "$WIFI_INTERFACE" get power_save 2>/dev/null || echo "unknown")
    echo "- WiFi power saving: $CURRENT_PS"
fi

echo "- SSH server status: $(systemctl is-active sshd.service)"
echo "- SSH server enabled: $(systemctl is-enabled sshd.service)"

if [[ -f "$SSH_CLIENT_CONFIG" ]]; then
    echo "- SSH client config: Present"
else
    echo "- SSH client config: Not found"
fi

echo "- USB autosuspend timeout: $(cat /sys/module/usbcore/parameters/autosuspend 2>/dev/null || echo 'unknown') seconds"

echo ""
echo "✅ SSH Stability Fix Complete!"
echo ""
echo "Summary of changes:"
echo "- WiFi power saving: Disabled (immediate and permanent)"
echo "- SSH server: Added keepalive settings (60s interval, 3 retries)"
echo "- SSH client: Added stability settings for all connections"
echo "- USB management: Prevented WiFi adapter autosuspend"
echo "- All settings: Will persist after reboot"
echo ""
echo "💡 Test your VSCode SSH connection now - it should be much more stable!"
echo "💡 If issues persist, check logs with: journalctl -u sshd.service --since '5 minutes ago'"
echo "💡 Monitor WiFi power saving with: watch 'iw dev $WIFI_INTERFACE get power_save'"
