#!/bin/bash
# Toggle between GNOME and Gamescope sessions
# This utility allows you to switch the default GDM session for autologin

set -euo pipefail

# AccountsService user config file
USER_CONFIG="/var/lib/AccountsService/users/$USER"

# Available sessions
GNOME_SESSION="gnome-wayland.desktop"
GAMESCOPE_SESSION="gamescope-session.desktop"

# Function to get current session
get_current_session() {
    if [ -f "$USER_CONFIG" ]; then
        grep "^Session=" "$USER_CONFIG" 2>/dev/null | cut -d'=' -f2 || echo ""
    else
        echo ""
    fi
}

# Function to show current session
show_current() {
    local current=$(get_current_session)
    
    if [ -z "$current" ]; then
        echo "No session preference set (using system default)"
    else
        case "$current" in
            "$GNOME_SESSION")
                echo "Current session: GNOME (Wayland)"
                ;;
            "$GAMESCOPE_SESSION")
                echo "Current session: Gamescope (Gaming Mode)"
                ;;
            *)
                echo "Current session: $current"
                ;;
        esac
    fi
}

# Function to set session
set_session() {
    local session="$1"
    local session_name="$2"
    
    echo "Setting default session to: $session_name"
    
    # Create the directory if it doesn't exist
    sudo mkdir -p "$(dirname "$USER_CONFIG")"
    
    # Check if file exists and has Session= line
    if [ -f "$USER_CONFIG" ] && grep -q "^Session=" "$USER_CONFIG"; then
        # Update existing Session line
        sudo sed -i "s|^Session=.*|Session=$session|" "$USER_CONFIG"
    else
        # Add Session line (preserve existing content)
        if [ -f "$USER_CONFIG" ]; then
            echo "Session=$session" | sudo tee -a "$USER_CONFIG" > /dev/null
        else
            # Create new file with basic structure
            cat << EOF | sudo tee "$USER_CONFIG" > /dev/null
[User]
Session=$session
XSession=
SystemAccount=false
EOF
        fi
    fi
    
    echo "✓ Session preference updated to: $session_name"
}

# Function to toggle between sessions
toggle_session() {
    local current=$(get_current_session)
    
    case "$current" in
        "$GNOME_SESSION")
            set_session "$GAMESCOPE_SESSION" "Gamescope (Gaming Mode)"
            ;;
        "$GAMESCOPE_SESSION"|"")
            # If empty or gamescope, switch to GNOME
            set_session "$GNOME_SESSION" "GNOME (Wayland)"
            ;;
        *)
            # Unknown session, default to GNOME
            echo "Unknown session '$current', switching to GNOME"
            set_session "$GNOME_SESSION" "GNOME (Wayland)"
            ;;
    esac
}

# Function to restart GDM (requires sudo)
restart_gdm() {
    echo ""
    echo "Restarting GDM will log you out and apply the new session."
    read -p "Are you sure you want to restart GDM now? [y/N] " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Restarting GDM..."
        sudo systemctl restart gdm
    else
        echo "Restart cancelled. Changes will take effect on next login/reboot."
    fi
}

# Main logic
case "${1:-toggle}" in
    "toggle")
        show_current
        echo ""
        toggle_session
        
        # Ask about restart if -r flag wasn't provided
        if [ "${2:-}" != "-r" ] && [ "${2:-}" != "--restart" ]; then
            echo ""
            echo "To apply changes:"
            echo "  1. Log out and log back in"
            echo "  2. Reboot the system"
            echo "  3. Run: $0 toggle --restart"
        else
            restart_gdm
        fi
        ;;
    "gnome")
        set_session "$GNOME_SESSION" "GNOME (Wayland)"
        
        if [ "${2:-}" = "-r" ] || [ "${2:-}" = "--restart" ]; then
            restart_gdm
        else
            echo "Log out or reboot to apply changes, or run with --restart to restart GDM now."
        fi
        ;;
    "gamescope"|"gamemode"|"gaming")
        set_session "$GAMESCOPE_SESSION" "Gamescope (Gaming Mode)"
        
        if [ "${2:-}" = "-r" ] || [ "${2:-}" = "--restart" ]; then
            restart_gdm
        else
            echo "Log out or reboot to apply changes, or run with --restart to restart GDM now."
        fi
        ;;
    "current"|"status")
        show_current
        ;;
    "restart")
        echo "Current configuration:"
        show_current
        restart_gdm
        ;;
    "-h"|"--help"|"help")
        cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
  toggle          - Toggle between GNOME and Gamescope sessions (default)
  gnome           - Set session to GNOME (Wayland)
  gamescope       - Set session to Gamescope (Gaming Mode)
  gamemode        - Alias for gamescope
  gaming          - Alias for gamescope
  current         - Show current session configuration
  status          - Alias for current
  restart         - Restart GDM to apply changes immediately
  help            - Show this help message

Options:
  -r, --restart   - Restart GDM immediately after changing session

Examples:
  $0              # Toggle session and prompt for restart
  $0 toggle -r    # Toggle and restart immediately
  $0 gnome        # Set to GNOME
  $0 gamescope -r # Set to Gamescope and restart immediately
  $0 current      # Show current session

Note: This script requires sudo access to modify system files and restart GDM.
      The session change takes effect after logout/login or restart.
EOF
        ;;
    *)
        echo "Error: Unknown command '$1'"
        echo "Run '$0 help' for usage information"
        exit 1
        ;;
esac
