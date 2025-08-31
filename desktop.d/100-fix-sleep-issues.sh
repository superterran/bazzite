#!/bin/bash
# Fix Sleep/Wake Issues on NVIDIA Systems
# This script addresses NVIDIA driver sleep/resume problems and USB wake-up issues

set -euo pipefail

echo "Configuring sleep/wake fixes for NVIDIA systems..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/..") && pwd)"

# Check if we have NVIDIA GPU
if ! lspci | grep -q "NVIDIA"; then
    echo "No NVIDIA GPU detected, skipping NVIDIA-specific fixes..."
    exit 0
fi

echo "NVIDIA GPU detected, applying sleep fixes..."

# 1. Configure NVIDIA power management options
echo "Setting up NVIDIA power management..."
sudo mkdir -p /etc/modprobe.d

if [ ! -f /etc/modprobe.d/nvidia-power.conf ]; then
    echo "Creating NVIDIA power management configuration..."
    sudo tee /etc/modprobe.d/nvidia-power.conf > /dev/null <<EOF
# NVIDIA power management options for better suspend/resume
options nvidia NVreg_PreserveVideoMemoryAllocations=1 NVreg_TemporaryFilePath=/var/tmp
options nvidia_drm modeset=1
EOF
    echo "✓ NVIDIA power management options configured"
else
    echo "✓ NVIDIA power management already configured"
fi

# 2. Set up s2idle sleep mode service
echo "Setting up s2idle sleep mode..."
if [ ! -f /etc/systemd/system/set-sleep-mode.service ]; then
    echo "Creating sleep mode configuration service..."
    sudo tee /etc/systemd/system/set-sleep-mode.service > /dev/null <<EOF
[Unit]
Description=Set s2idle sleep mode for better NVIDIA compatibility
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'echo s2idle > /sys/power/mem_sleep'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl enable set-sleep-mode.service
    echo "✓ Sleep mode service created and enabled"
else
    echo "✓ Sleep mode service already exists"
fi

# 3. USB wake-up management removed
# Note: USB wake-up disabling has been removed to allow USB devices to wake the system
echo "✓ USB wake-up functionality preserved"

# 4. Apply settings immediately (if files exist)
echo "Applying settings immediately..."

# Set s2idle mode now
if [ -w /sys/power/mem_sleep ]; then
    echo "s2idle" | sudo tee /sys/power/mem_sleep > /dev/null
    echo "✓ Sleep mode set to s2idle"
else
    echo "⚠ Could not set sleep mode immediately (will apply on next boot)"
fi

# USB wake-up sources left enabled for device wake functionality
echo "✓ USB wake-up functionality preserved"

# 5. Verify current configuration
echo ""
echo "Current sleep configuration:"
if [ -r /sys/power/mem_sleep ]; then
    echo "Sleep mode: $(cat /sys/power/mem_sleep)"
fi

if [ -r /proc/acpi/wakeup ]; then
    echo "USB Controller wake status:"
    grep -E "(XHC0|XHC1)" /proc/acpi/wakeup || echo "USB controllers not found in wake-up table"
fi

echo ""
echo "✅ Sleep fix configuration complete!"
echo ""
echo "Summary of changes:"
echo "- NVIDIA power management: Enabled video memory preservation"
echo "- Sleep mode: Set to s2idle (more reliable than deep sleep)"  
echo "- USB wake-up: Preserved for device wake functionality"
echo "- All settings: Will persist after reboot"
echo ""
echo "💡 To test sleep functionality, run: systemctl suspend"
echo "💡 After waking, check logs with: journalctl -u systemd-suspend.service --since '5 minutes ago'"
