#!/bin/bash
# Setup Samba file sharing service
# This script installs and configures Samba for sharing home directory and fast/slow drives

set -euo pipefail

echo "Setting up Samba file sharing service..."

# Check if Samba is already installed
if ! rpm -q samba &>/dev/null; then
    echo "Installing Samba packages..."
    sudo rpm-ostree install samba samba-common-tools || {
        echo "Failed to install Samba packages"; exit 1;
    }
    echo "Samba packages installed. Reboot required to apply changes."
    exit 0
fi

echo "Samba packages are already installed."

# Check if Samba is already configured
if [ -f /etc/samba/smb.conf.bak ]; then
    echo "Samba is already configured, skipping configuration..."
else
    echo "Configuring Samba..."
    
    # Backup original configuration
    sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak
    
    # Create clean Samba configuration for macOS compatibility
    sudo tee /etc/samba/smb.conf > /dev/null << 'SAMBA_CONF'
[global]
    workgroup = WORKGROUP
    server string = Desktop Samba Server
    netbios name = Desktop
    security = user
    map to guest = never
    dns proxy = no
    log level = 2
    log file = /var/log/samba/log.%m
    max log size = 1000
    server role = standalone server
    
    # Protocol settings
    server min protocol = SMB2
    server max protocol = SMB3
    
    # macOS specific compatibility
    vfs objects = catia fruit streams_xattr
    fruit:metadata = stream
    fruit:model = MacSamba
    fruit:posix_rename = yes
    fruit:veto_appledouble = no
    fruit:wipe_intentionally_left_blank_rfork = yes
    fruit:delete_empty_adfiles = yes

[me]
    comment = Me Home Directory
    path = /var/home/me
    browseable = yes
    read only = no
    valid users = me
    create mask = 0644
    directory mask = 0755

[fast]
    comment = Fast Drive
    path = /var/mnt/fast
    browseable = yes
    read only = no
    valid users = me
    create mask = 0644
    directory mask = 0755

[slow]
    comment = Slow Drive
    path = /var/mnt/slow
    browseable = yes
    read only = no
    valid users = me
    create mask = 0644
    directory mask = 0755
SAMBA_CONF

    echo "Samba configuration created successfully."
fi

# Fix directory permissions for Samba access
echo "Setting up directory permissions..."
chmod 755 /var/home/me 2>/dev/null || echo "Home directory permissions already set"

# Fix ownership for slow drive if needed
if [ "$(stat -c %U /var/mnt/slow 2>/dev/null)" != "me" ]; then
    echo "Fixing ownership of slow drive..."
    sudo chown me:me /var/mnt/slow
fi

# Configure SELinux for Samba (critical fix)
echo "Configuring SELinux for Samba..."

# Enable Samba home directory access
if ! getsebool samba_enable_home_dirs | grep -q "on"; then
    echo "Enabling SELinux Samba home directory access..."
    sudo setsebool -P samba_enable_home_dirs on
fi

# Set proper SELinux contexts for mounted drives
echo "Setting SELinux contexts for shared drives..."
sudo semanage fcontext -a -t samba_share_t "/mnt/fast(/.*)?" 2>/dev/null || echo "Fast drive context already set"
sudo semanage fcontext -a -t samba_share_t "/mnt/slow(/.*)?" 2>/dev/null || echo "Slow drive context already set"
sudo restorecon -R /var/mnt/fast /var/mnt/slow 2>/dev/null || echo "Contexts already applied"

# Check if Samba service is enabled
if systemctl is-enabled smb.service >/dev/null 2>&1; then
    echo "Samba service is already enabled."
else
    echo "Enabling Samba service..."
    sudo systemctl enable smb.service
    sudo systemctl enable nmb.service
fi

# Check if Samba service is running
if systemctl is-active --quiet smb.service; then
    echo "Samba service is already running."
else
    echo "Starting Samba service..."
    sudo systemctl start smb.service
    sudo systemctl start nmb.service
fi

# Configure firewall for Samba
echo "Configuring firewall for Samba..."
if command -v firewall-cmd >/dev/null 2>&1; then
    if ! sudo firewall-cmd --list-services | grep -q samba; then
        sudo firewall-cmd --permanent --add-service=samba
        sudo firewall-cmd --reload
        echo "Firewall configured for Samba."
    else
        echo "Firewall is already configured for Samba."
    fi
else
    echo "No firewall-cmd found, skipping firewall configuration."
fi

# Check if user 'me' exists in Samba
if sudo pdbedit -L | grep -q "^me:"; then
    echo "Samba user 'me' already exists."
else
    echo ""
    echo "Setting up Samba user 'me'..."
    echo "You will be prompted to set a Samba password for user 'me':"
    sudo smbpasswd -a me
fi

echo ""
echo "Samba setup completed successfully!"
echo ""
echo "Server name: Desktop"
echo ""
echo "Available shares:"
echo "  - Home directory: smb://Desktop/me or smb://$(hostname -I | awk '{print $1}')/me"
echo "  - Fast drive: smb://Desktop/fast or smb://$(hostname -I | awk '{print $1}')/fast" 
echo "  - Slow drive: smb://Desktop/slow or smb://$(hostname -I | awk '{print $1}')/slow"
echo ""
echo "Network discovery: smb://Desktop/ or smb://$(hostname -I | awk '{print $1}')/"
echo ""
echo "Connect using username: me"
echo ""
echo "Note: SELinux contexts and permissions have been configured for proper macOS compatibility."
