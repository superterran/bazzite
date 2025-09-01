#!/bin/bash
# Unified setup orchestrator
# Runs common.d and <target>.d (desktop|handheld) modular scripts in order

set -euo pipefail

# Resolve repo root
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Bazzite Modular Setup"
echo "======================"

# Determine target from first arg or auto-detect
TARGET_DIR_ARG="${1:-}"
TARGET=""

detect_system_type() {
    if grep -qi "ROG Ally\|Steam Deck\|GPD" /sys/devices/virtual/dmi/id/product_name 2>/dev/null; then
        echo handheld
    elif grep -qi "desktop\|tower" /sys/devices/virtual/dmi/id/chassis_type 2>/dev/null; then
        echo desktop
    else
        echo desktop
    fi
}

if [[ -n "$TARGET_DIR_ARG" ]]; then
    TARGET="$TARGET_DIR_ARG"
else
    TARGET="$(detect_system_type)"
fi

COMMON_DIR="$REPO_ROOT/common.d"
TARGET_DIR="$REPO_ROOT/${TARGET}.d"

echo "Target: $TARGET"
echo "Root: $REPO_ROOT"
echo ""

run_dir() {
    local dir="$1"
    local title="$2"
    if [[ -d "$dir" ]]; then
        echo "Running $title scripts from: $dir"
        # Execute all .sh files in lexical order regardless of executable bit
        while IFS= read -r -d '' script; do
            local name
            name="$(basename "$script")"
            echo ""
            echo "=== Executing $name ==="
            if bash "$script"; then
                echo "✓ $name completed successfully"
            else
                echo "✗ $name failed with exit code $?"
                echo "Continuing with remaining scripts..."
            fi
        done < <(find "$dir" -maxdepth 1 -type f -name "*.sh" -print0 | sort -z)
    else
        echo "Skipping $title: directory not found: $dir"
    fi
}

# Run common first, then target-specific
run_dir "$COMMON_DIR" "common"
run_dir "$TARGET_DIR" "$TARGET"

echo ""
echo "Setup complete for target: $TARGET"
echo "All modular setup scripts have been executed."
