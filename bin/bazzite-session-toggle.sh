#!/bin/bash

# Bazzite Session Toggle Script v2
# Switches between Gaming Mode (Steam) and GNOME desktop
# This version handles Bazzite's actual SDDM-based session management

IMAGE_INFO="/usr/share/ublue-os/image-info.json"
BASE_IMAGE_NAME=$(jq -r '.["base-image-name"]' < $IMAGE_INFO)

# Bazzite uses SDDM configuration, not GDM for session control
SDDM_CONFIG="/etc/sddm.conf.d/steamos.conf"
DESKTOP_AUTOLOGIN_MARKER="/etc/bazzite/desktop_autologin"

# Session identifiers
GAMEMODE_SESSION="gamescope-session.desktop"
if [[ "$BASE_IMAGE_NAME" == "silverblue" ]]; then
    GNOME_SESSION="gnome-wayland.desktop"
else
    # Fallback for other bases
    GNOME_SESSION="gnome.desktop"
fi

# Function to get current session from SDDM config
get_configured_session() {
    grep "^Session=" "$SDDM_CONFIG" 2>/dev/null | cut -d'=' -f2
}

# Function to detect what's currently running
get_running_session() {
    if pgrep -f "gdm-wayland-session.*gamescope-session-plus\|gamescope-session" >/dev/null 2>&1; then
        echo "$GAMEMODE_SESSION"
    elif pgrep -f "gnome-session" >/dev/null 2>&1; then
        echo "$GNOME_SESSION"
    else
        echo "unknown"
    fi
}

# Function to set session to Gaming Mode
set_gaming_session() {
    # Remove desktop autologin marker to enable gaming mode
    sudo rm -f "$DESKTOP_AUTOLOGIN_MARKER"
    sudo sed -i "s/^Session=.*/Session=$GAMEMODE_SESSION/g" "$SDDM_CONFIG"
}

# Function to set session to GNOME Desktop
set_gnome_session() {
    # Create desktop autologin marker to enable desktop mode
    sudo mkdir -p /etc/bazzite
    sudo touch "$DESKTOP_AUTOLOGIN_MARKER"
    sudo sed -i "s/^Session=.*/Session=$GNOME_SESSION/g" "$SDDM_CONFIG"
}

# Function to show current status
show_status() {
    local configured=$(get_configured_session)
    local running=$(get_running_session)
    local autologin_marker=""
    
    if [[ -f "$DESKTOP_AUTOLOGIN_MARKER" ]]; then
        autologin_marker="present (desktop mode)"
    else
        autologin_marker="absent (gaming mode)"
    fi
    
    echo "=== Bazzite Session Status ==="
    echo "Currently running: $running"
    if [[ "$running" == "$GAMEMODE_SESSION" ]]; then
        echo "  Status: Gaming Mode (Steam) is active"
    elif [[ "$running" == "$GNOME_SESSION" ]]; then
        echo "  Status: GNOME Desktop is active"
    else
        echo "  Status: Unknown session type active"
    fi
    
    echo ""
    echo "Configured for next boot: $configured"
    echo "Desktop autologin marker: $autologin_marker"
    
    if [[ "$configured" == "$GAMEMODE_SESSION" ]]; then
        echo "  Status: Will boot into Gaming Mode (Steam)"
    elif [[ "$configured" == "$GNOME_SESSION" ]]; then
        echo "  Status: Will boot into GNOME Desktop"
    else
        echo "  Status: Unknown session type configured"
    fi
    
    if [[ "$configured" != "$running" ]]; then
        echo ""
        echo "⚠️  Configuration has changed! Restart required to apply changes."
    else
        echo ""
        echo "✓ Current session matches configured session"
    fi
}

# Main logic
case "$1" in
    "gaming"|"gamemode"|"steam")
        echo "Switching to Gaming Mode (Steam)..."
        set_gaming_session
        echo "✓ System will boot into Gaming Mode on next restart"
        echo ""
        echo "💡 You need to restart your system for this change to take effect!"
        ;;
    "gnome"|"desktop")
        echo "Switching to GNOME Desktop..."
        set_gnome_session
        echo "✓ System will boot into GNOME Desktop on next restart"
        echo ""
        echo "💡 You need to restart your system for this change to take effect!"
        ;;
    "status"|"")
        show_status
        ;;
    "toggle")
        configured=$(get_configured_session)
        if [[ "$configured" == "$GAMEMODE_SESSION" ]]; then
            echo "Currently configured for Gaming Mode, switching to GNOME Desktop..."
            set_gnome_session
            echo "✓ System will boot into GNOME Desktop on next restart"
        else
            echo "Currently configured for GNOME Desktop, switching to Gaming Mode..."
            set_gaming_session
            echo "✓ System will boot into Gaming Mode on next restart"
        fi
        echo ""
        echo "💡 You need to restart your system for this change to take effect!"
        ;;
    "restart"|"reboot")
        echo "Restarting system to apply session changes..."
        sudo systemctl reboot
        ;;
    "help"|"-h"|"--help")
        echo "Bazzite Session Toggle v2 - Switch between Gaming Mode and GNOME Desktop"
        echo ""
        echo "Usage: $0 [OPTION]"
        echo ""
        echo "Options:"
        echo "  gaming, gamemode, steam  - Switch to Gaming Mode (Steam)"
        echo "  gnome, desktop          - Switch to GNOME Desktop"
        echo "  toggle                  - Toggle between current modes"
        echo "  status                  - Show current session status"
        echo "  restart, reboot         - Restart system to apply changes"
        echo "  help                    - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 gaming     # Switch to Gaming Mode"
        echo "  $0 gnome      # Switch to GNOME Desktop"
        echo "  $0 toggle     # Toggle between modes"
        echo "  $0 status     # Check current mode"
        echo "  $0 restart    # Restart to apply changes"
        echo ""
        echo "Note: This script modifies Bazzite's SDDM configuration and the"
        echo "      /etc/bazzite/desktop_autologin marker file to control sessions."
        echo "      Changes require a system restart to take effect!"
        ;;
    *)
        echo "Unknown option: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
