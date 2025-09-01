#!/bin/bash
# Fresh install setup script for custom Bazzite variants
# Run this on a fresh Bazzite installation to switch to custom variant

set -euo pipefail

echo "=== Custom Bazzite Fresh Install Setup ==="
echo ""

# Detect system type
if lspci | grep -i nvidia &>/dev/null; then
    VARIANT="desktop"
    echo "🖥️  Detected NVIDIA GPU - will install desktop variant"
elif [[ -f /sys/class/dmi/id/product_name ]] && grep -i "ally" /sys/class/dmi/id/product_name &>/dev/null; then
    VARIANT="handheld"
    echo "🎮 Detected ROG Ally - will install handheld variant"
else
    echo "❓ Could not auto-detect system type"
    echo "Please choose your variant:"
    echo "1) Handheld (ROG Ally X)"
    echo "2) Desktop (NVIDIA)"
    read -p "Enter choice (1 or 2): " choice
    
    case $choice in
        1) VARIANT="handheld" ;;
        2) VARIANT="desktop" ;;
        *) echo "Invalid choice. Exiting."; exit 1 ;;
    esac
fi

echo ""
echo "🔄 Rebasing to custom Bazzite variant: $VARIANT"
echo "This will download and switch to the custom image..."
echo ""

# Rebase to custom variant
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:$VARIANT

echo ""
echo "✅ Rebase complete!"
echo ""
echo "🔄 Rebooting to apply changes..."
echo "After reboot, run the setup script:"
echo "curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash"
echo ""
echo "Rebooting in 10 seconds... (Ctrl+C to cancel)"
sleep 10
sudo systemctl reboot
