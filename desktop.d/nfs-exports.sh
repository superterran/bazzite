#!/bin/bash
set -euo pipefail

echo "Setting up NFS exports for all mounted drives and home directory..."

# Check if nfs-utils is installed
if ! rpm -q nfs-utils &>/dev/null; then
    echo "Installing nfs-utils..."
    sudo rpm-ostree install nfs-utils || {
        echo "Failed to install nfs-utils"; exit 1;
    }
    echo "nfs-utils installed. Reboot required to apply changes."
    exit 0
fi

# Get all mounted drives (excluding system mounts and [SWAP], only real directories)
# Only export /fast, /slow, and the current user's home directory
VALID_MOUNTS=""
for DIR in /var/mnt/fast /var/mnt/slow "$HOME"; do
    if [ -d "$DIR" ]; then
        VALID_MOUNTS+="$DIR\n"
    fi
done

# Add home directory
HOME_DIR="$HOME"

EXPORTS_FILE="/etc/exports"

# Backup current exports file
if [ -f "$EXPORTS_FILE" ]; then
    sudo cp "$EXPORTS_FILE" "$EXPORTS_FILE.bak"
    # Remove any previous [SWAP] entries
    sudo sed -i '/\[SWAP\]/d' "$EXPORTS_FILE"
fi

# Build export lines
EXPORT_LINES=""
for MOUNT in $(echo -e "$VALID_MOUNTS"); do
    # Skip if already exported
    if grep -q "^$MOUNT " "$EXPORTS_FILE" 2>/dev/null; then
        echo "$MOUNT already exported, skipping..."
        continue
    fi
    EXPORT_LINES+="$MOUNT *(rw,sync,no_subtree_check)\n"
done

# Export home directory if not already exported
if ! grep -q "^$HOME_DIR " "$EXPORTS_FILE" 2>/dev/null; then
    EXPORT_LINES+="$HOME_DIR *(rw,sync,no_subtree_check)\n"
fi

# Append new exports
if [ -n "$EXPORT_LINES" ]; then
    echo -e "$EXPORT_LINES" | sudo tee -a "$EXPORTS_FILE"
    echo "Updated $EXPORTS_FILE with new exports."
else
    echo "No new exports needed."
fi

# Enable and start NFS server
sudo systemctl enable --now nfs-server

# Configure firewall for NFS
echo "Configuring firewall for NFS..."
sudo firewall-cmd --permanent --add-service=nfs
sudo firewall-cmd --permanent --add-service=nfs3
sudo firewall-cmd --permanent --add-service=mountd
sudo firewall-cmd --permanent --add-service=rpc-bind
sudo firewall-cmd --reload

sudo exportfs -ra

echo "NFS exports setup completed successfully."
