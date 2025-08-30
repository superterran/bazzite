#!/bin/bash
# Backup current system configuration for replication purposes

set -euo pipefail

BACKUP_DIR="./config-backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up system configuration to $BACKUP_DIR..."

# Backup RPM packages
echo "Backing up RPM package information..."
rpm-ostree status --verbose > "$BACKUP_DIR/rpm-ostree-status.txt"
rpm -qa > "$BACKUP_DIR/installed-rpms.txt"

# Backup Flatpak applications
echo "Backing up Flatpak applications..."
flatpak list --app --columns=application,version,branch,origin > "$BACKUP_DIR/flatpak-apps.txt" || echo "No Flatpaks found"

# Backup enabled user services
echo "Backing up user services..."
systemctl --user list-unit-files --state=enabled --no-pager > "$BACKUP_DIR/user-services-enabled.txt"

# Backup GNOME shell extensions settings
echo "Backing up GNOME extensions settings..."
dconf dump /org/gnome/shell/extensions/ > "$BACKUP_DIR/gnome-extensions.dconf" || echo "No GNOME extensions settings found"

# Backup key GNOME settings
echo "Backing up key GNOME settings..."
dconf dump /org/gnome/desktop/ > "$BACKUP_DIR/gnome-desktop.dconf" || echo "No GNOME desktop settings found"
dconf dump /org/gnome/shell/ > "$BACKUP_DIR/gnome-shell.dconf" || echo "No GNOME shell settings found"

# Backup container/systemd customizations if they exist
if [ -d ~/.config/systemd/user ]; then
    echo "Backing up user systemd units..."
    cp -r ~/.config/systemd/user "$BACKUP_DIR/systemd-user-units/" || echo "No custom user systemd units found"
fi

# Create a restore script template
cat > "$BACKUP_DIR/restore-guide.md" << 'EOF'
# Configuration Restore Guide

## RPM Packages
The following RPM packages were installed:
- LayeredPackages: See rpm-ostree-status.txt
- LocalPackages: See rpm-ostree-status.txt

## Flatpak Applications
See flatpak-apps.txt for the complete list.
Install with: `flatpak install -y flathub <app-id>`

## User Services
See user-services-enabled.txt for enabled services.
Enable with: `systemctl --user enable --now <service>`

## GNOME Configuration
Restore settings with:
```bash
dconf load /org/gnome/shell/extensions/ < gnome-extensions.dconf
dconf load /org/gnome/desktop/ < gnome-desktop.dconf
dconf load /org/gnome/shell/ < gnome-shell.dconf
```

## Custom Systemd Units
Copy files from systemd-user-units/ to ~/.config/systemd/user/
Then run: `systemctl --user daemon-reload`
EOF

echo "Backup complete! Configuration saved to $BACKUP_DIR"
echo "Use the restore-guide.md for manual restoration steps."
