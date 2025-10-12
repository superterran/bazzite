#!/bin/bash
set -euo pipefail

# Toggle between GNOME and Gamescope sessions
# This script modifies /var/lib/AccountsService/users/username to switch default session

# Parse arguments
FORCE_SESSION=""
CURRENT_USER="me"

# Show usage
show_usage() {
    echo "Usage: $0 [gamescope|desktop] [username]"
    echo ""
    echo "Options:"
    echo "  gamescope    Force switch to Gamescope (Gaming Mode)"
    echo "  desktop      Force switch to GNOME (Desktop Mode)"
    echo "  username     Target user (default: me)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Toggle session for 'me' user"
    echo "  $0 gamescope          # Force gamescope session for 'me' user"
    echo "  $0 desktop            # Force desktop session for 'me' user"
    echo "  $0 gamescope otheruser # Force gamescope session for 'otheruser'"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        gamescope)
            FORCE_SESSION="gamescope-session"
            shift
            ;;
        desktop)
            FORCE_SESSION="gnome"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            # Assume it's a username if it doesn't match known options
            CURRENT_USER="$1"
            shift
            ;;
    esac
done

ACCOUNTS_SERVICE_CONFIG="/var/lib/AccountsService/users/$CURRENT_USER"
BACKUP_DIR="/tmp"

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
    echo "This script requires root privileges. Please run with sudo."
    exit 1
fi

# Check if AccountsService config exists
if [[ ! -f "$ACCOUNTS_SERVICE_CONFIG" ]]; then
    echo "Error: $ACCOUNTS_SERVICE_CONFIG not found!"
    echo "Creating basic configuration file..."
    mkdir -p "$(dirname "$ACCOUNTS_SERVICE_CONFIG")"
    cat > "$ACCOUNTS_SERVICE_CONFIG" << EOF
[User]
Session=gnome
XSession=
Icon=
SystemAccount=false
EOF
fi

# Create backup
BACKUP_FILE="$BACKUP_DIR/$(basename "$ACCOUNTS_SERVICE_CONFIG").backup.$(date +%Y%m%d_%H%M%S)"
cp "$ACCOUNTS_SERVICE_CONFIG" "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"

# Read current session
CURRENT_SESSION=$(grep -E "^Session=" "$ACCOUNTS_SERVICE_CONFIG" | cut -d'=' -f2 || echo "gnome")

echo "Current session for user '$CURRENT_USER': $CURRENT_SESSION"

# Determine new session
if [[ -n "$FORCE_SESSION" ]]; then
    # Force to specific session
    NEW_SESSION="$FORCE_SESSION"
    case "$NEW_SESSION" in
        "gnome")
            ACTION="Forcing switch to GNOME (Desktop Mode)"
            ;;
        "gamescope-session")
            ACTION="Forcing switch to Gamescope (Gaming Mode)"
            ;;
    esac
else
    # Toggle the session
    if [[ "$CURRENT_SESSION" == "gnome" ]]; then
        NEW_SESSION="gamescope-session"
        ACTION="Switching to Gamescope (Gaming Mode)"
    elif [[ "$CURRENT_SESSION" == "gamescope-session" ]]; then
        NEW_SESSION="gnome"
        ACTION="Switching to GNOME (Desktop Mode)"
    else
        # If current session is something else, default to gnome
        NEW_SESSION="gnome"
        ACTION="Switching to GNOME (Desktop Mode) from unknown session"
    fi
fi

# Skip if already set to desired session
if [[ "$CURRENT_SESSION" == "$NEW_SESSION" ]]; then
    echo "Session is already set to the desired state: $NEW_SESSION"
    case "$NEW_SESSION" in
        "gnome")
            echo "✓ Already in GNOME (Desktop Mode)"
            ;;
        "gamescope-session")
            echo "✓ Already in Gamescope (Gaming Mode)"
            ;;
    esac
    exit 0
fi

echo "$ACTION..."

sudo killall gdm 2>/dev/null || true
sleep 1

# Update the configuration
if grep -q "^Session=" "$ACCOUNTS_SERVICE_CONFIG"; then
    # Session setting exists, replace it
    sed -i "s/^Session=.*/Session=$NEW_SESSION/" "$ACCOUNTS_SERVICE_CONFIG"
else
    # Session setting doesn't exist, add it to the [User] section
    if grep -q "^\[User\]" "$ACCOUNTS_SERVICE_CONFIG"; then
        # [User] section exists, add after it
        sed -i "/^\[User\]/a Session=$NEW_SESSION" "$ACCOUNTS_SERVICE_CONFIG"
    else
        # No [User] section, create one
        echo -e "\n[User]\nSession=$NEW_SESSION" >> "$ACCOUNTS_SERVICE_CONFIG"
    fi
fi

# Verify the change
NEW_CURRENT_SESSION=$(grep -E "^Session=" "$ACCOUNTS_SERVICE_CONFIG" | cut -d'=' -f2)
echo "New session for user '$CURRENT_USER': $NEW_CURRENT_SESSION"

# Show session information
case "$NEW_CURRENT_SESSION" in
    "gnome")
        echo "✓ GNOME session selected - Desktop mode with full desktop environment"
        ;;
    "gamescope-session")
        echo "✓ Gamescope session selected - Gaming mode optimized for gaming"
        ;;
    *)
        echo "✓ Session set to: $NEW_CURRENT_SESSION"
        ;;
esac

echo ""
echo "Session configuration updated successfully!"
echo ""

# Automatically restart GDM to apply changes immediately
echo "Restarting GDM to apply changes immediately..."
echo "Warning: This will close your current session!"
sleep 2

# Kill GDM to force restart
killall gdm 2>/dev/null || {
    echo "Note: Failed to kill GDM directly, trying systemctl restart..."
    systemctl restart gdm
}

echo "GDM restarted. Session changes should be active on next login."