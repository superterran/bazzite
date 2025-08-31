#!/bin/bash
# Desktop-specific setup script
# This should only be run on desktop systems, not handheld
# Executes all scripts in the desktop.d/ directory in order

set -euo pipefail

echo "Setting up desktop-specific configurations..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$SCRIPT_DIR/desktop.d"

# Execute all scripts in desktop.d/ directory in order
echo "Found desktop.d/ directory, executing modular setup scripts..."

# Find all executable .sh files and sort them
for script in $(find "$DESKTOP_DIR" -name "*.sh" -type f -executable | sort); do
    script_name=$(basename "$script")
    echo ""
    echo "=== Executing $script_name ==="
    
    if bash "$script"; then
        echo "✓ $script_name completed successfully"
    else
        echo "✗ $script_name failed with exit code $?"
        echo "Continuing with remaining scripts..."
    fi
done

echo ""
echo "Desktop-specific setup complete!"
echo "All modular setup scripts have been executed."
