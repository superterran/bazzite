#!/bin/bash
# Manual display switcher for gamescope
# This utility allows you to manually switch between HDMI and DisplayPort

set -euo pipefail

GAMESCOPE_CONF="$HOME/.config/environment.d/10-gamescope-session.conf"

# Function to show current configuration
show_current() {
    if [ -f "$GAMESCOPE_CONF" ]; then
        echo "Current configuration:"
        cat "$GAMESCOPE_CONF"
    else
        echo "No gamescope display configuration found."
    fi
}

# Function to get current display
get_current_display() {
    if [ -f "$GAMESCOPE_CONF" ]; then
        grep "^OUTPUT_CONNECTOR=" "$GAMESCOPE_CONF" | cut -d'=' -f2
    else
        echo ""
    fi
}

# Function to get connected displays
get_connected_displays() {
    local displays=()
    
    # Check HDMI
    for status_file in /sys/class/drm/card*/card*-HDMI*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            local status=$(cat "$status_file")
            local output_name=$(echo "$connector" | sed 's/^card[0-9]*-//')
            if [ "$status" = "connected" ]; then
                displays+=("$output_name")
            fi
        fi
    done
    
    # Check DisplayPort
    for status_file in /sys/class/drm/card*/card*-DP*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            local status=$(cat "$status_file")
            local output_name=$(echo "$connector" | sed 's/^card[0-9]*-//')
            if [ "$status" = "connected" ]; then
                displays+=("$output_name")
            fi
        fi
    done
    
    printf '%s\n' "${displays[@]}"
}

# Function to list available displays
list_displays() {
    echo "Connected displays:"
    
    # Check HDMI
    for status_file in /sys/class/drm/card*/card*-HDMI*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            local status=$(cat "$status_file")
            local output_name=$(echo "$connector" | sed 's/^card[0-9]*-//')
            echo "  $output_name: $status"
        fi
    done
    
    # Check DisplayPort
    for status_file in /sys/class/drm/card*/card*-DP*/status; do
        if [ -f "$status_file" ]; then
            local connector=$(basename $(dirname "$status_file"))
            local status=$(cat "$status_file")
            local output_name=$(echo "$connector" | sed 's/^card[0-9]*-//')
            echo "  $output_name: $status"
        fi
    done
}

# Function to toggle between connected displays
toggle_display() {
    local current_display=$(get_current_display)
    local connected_displays=($(get_connected_displays))
    
    if [ ${#connected_displays[@]} -lt 2 ]; then
        echo "Error: Need at least 2 connected displays to toggle. Found ${#connected_displays[@]}."
        echo "Connected displays:"
        printf '  %s\n' "${connected_displays[@]}"
        return 1
    fi
    
    # Find the next display to switch to
    local next_display=""
    if [ -z "$current_display" ]; then
        # No current display set, use the first one
        next_display="${connected_displays[0]}"
    else
        # Find current display in the array and get the next one
        for i in "${!connected_displays[@]}"; do
            if [ "${connected_displays[$i]}" = "$current_display" ]; then
                # Get next display (wrap around to first if at end)
                next_index=$(( (i + 1) % ${#connected_displays[@]} ))
                next_display="${connected_displays[$next_index]}"
                break
            fi
        done
        
        # If current display not found in connected displays, use first connected
        if [ -z "$next_display" ]; then
            next_display="${connected_displays[0]}"
        fi
    fi
    
    echo "Toggling from '$current_display' to '$next_display'"
    set_display "$next_display"
}

# Function to set display
set_display() {
    local display="$1"
    
    mkdir -p ~/.config/environment.d
    echo "OUTPUT_CONNECTOR=$display" > "$GAMESCOPE_CONF"
    echo "Set gamescope display to: $display"
    echo "Restart gamescope session for changes to take effect."
}

# Main logic
case "${1:-}" in
    "")
        echo "Usage: $0 [DISPLAY_NAME|list|current|auto|toggle]"
        echo ""
        echo "Commands:"
        echo "  list     - Show all available displays"
        echo "  current  - Show current configuration"
        echo "  auto     - Run automatic display detection (prioritizes HDMI)"
        echo "  toggle   - Toggle between connected displays"
        echo "  DISPLAY_NAME - Set specific display (e.g., HDMI-A-2, DP-2)"
        echo ""
        list_displays
        ;;
    "list")
        list_displays
        ;;
    "current")
        show_current
        ;;
    "auto")
        echo "Running automatic display configuration..."
        exec "$(dirname "$0")/../desktop.d/25-setup-gamescope-display.sh"
        ;;
    "toggle")
        toggle_display
        ;;
    *)
        set_display "$1"
        ;;
esac
