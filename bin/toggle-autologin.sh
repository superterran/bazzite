#!/bin/bash
set -euo pipefail

# Toggle auto login in GDM configuration
# This script modifies /etc/gdm/custom.conf to enable/disable automatic login

GDM_CONFIG="/etc/gdm/custom.conf"
BACKUP_DIR="/tmp"

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    echo "This script requires root privileges. Please run with sudo."
    exit 1
fi

# Check if GDM config exists
if [[ ! -f "$GDM_CONFIG" ]]; then
    echo "Error: $GDM_CONFIG not found!"
    exit 1
fi

# Create backup
BACKUP_FILE="$BACKUP_DIR/custom.conf.backup.$(date +%Y%m%d_%H%M%S)"
cp "$GDM_CONFIG" "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Read current state
CURRENT_STATE=$(grep -E "^AutomaticLoginEnable=" "$GDM_CONFIG" | cut -d'=' -f2 || echo "False")

echo "Current AutomaticLoginEnable state: $CURRENT_STATE"

# Toggle the state
if [[ "$CURRENT_STATE" == "True" ]]; then
    NEW_STATE="False"
    ACTION="Disabling"
else
    NEW_STATE="True"
    ACTION="Enabling"
fi

echo "$ACTION automatic login..."

# Update the configuration
if grep -q "^AutomaticLoginEnable=" "$GDM_CONFIG"; then
    # Setting exists, replace it
    sed -i "s/^AutomaticLoginEnable=.*/AutomaticLoginEnable=$NEW_STATE/" "$GDM_CONFIG"
else
    # Setting doesn't exist, add it to the [daemon] section
    if grep -q "^\[daemon\]" "$GDM_CONFIG"; then
        # [daemon] section exists, add after it
        sed -i "/^\[daemon\]/a AutomaticLoginEnable=$NEW_STATE" "$GDM_CONFIG"
    else
        # No [daemon] section, create one
        echo -e "\n[daemon]\nAutomaticLoginEnable=$NEW_STATE" >> "$GDM_CONFIG"
    fi
fi

# Verify the change
NEW_CURRENT_STATE=$(grep -E "^AutomaticLoginEnable=" "$GDM_CONFIG" | cut -d'=' -f2)
echo "New AutomaticLoginEnable state: $NEW_CURRENT_STATE"

# Show current username for auto login
if [[ "$NEW_CURRENT_STATE" == "True" ]]; then
    USERNAME=$(grep -E "^AutomaticLogin=" "$GDM_CONFIG" | cut -d'=' -f2 || echo "NOT_SET")
    if [[ "$USERNAME" == "NOT_SET" ]]; then
        echo "Warning: AutomaticLoginEnable is True but AutomaticLogin username is not set!"
        echo "You may need to add 'AutomaticLogin=yourusername' to $GDM_CONFIG"
    else
        echo "Automatic login enabled for user: $USERNAME"
    fi
fi

echo "GDM configuration updated successfully!"
echo "Changes will take effect after restarting GDM or rebooting the system."
echo ""
echo "To restart GDM immediately (will close current session):"
echo "  sudo systemctl restart gdm"