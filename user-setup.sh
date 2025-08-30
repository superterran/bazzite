#!/bin/bash
# User-level setup script to be run after rebasing to the custom image
# This handles configurations that can't be done at the container build level

set +e

echo "Setting up user-level configurations..."

# Enable user services
echo "Enabling user services..."
systemctl --user enable --now ollama.service || echo "ollama service not available, skipping..."
systemctl --user enable --now openrgb.service || echo "openrgb service not available, skipping..."
systemctl --user enable --now sunshine.service || echo "sunshine service not available, skipping..."

# Install common Flatpaks
echo "Installing Flatpaks..."
flatpak install -y flathub \
    com.google.Chrome \
    com.slack.Slack \
    md.obsidian.Obsidian \
    com.github.tchx84.Flatseal \
    com.mattjakeman.ExtensionManager \
    io.missioncenter.MissionCenter \
    com.github.Matoking.protontricks \
    com.vysp3r.ProtonPlus \
    io.github.flattool.Warehouse \
    org.mozilla.Thunderbird \
    org.openrgb.OpenRGB \
    || echo "Some Flatpaks may have failed to install, continuing..."


# Install 1Password
# rpm-ostree --import https://downloads.1password.com/linux/keys/1password.asc
rpm-ostree install https://downloads.1password.com/linux/rpm/stable/x86_64/1password-latest.rpm

# install warp-terminal
# rpm --import https://releases.warp.dev/linux/keys/warp.asc
rpm-ostree install warp-terminal


# Create directories for development tools
mkdir -p ~/.local/bin
mkdir -p ~/.config/systemd/user

echo "User setup complete!"
echo ""
echo "Next steps:"
echo "1. Reboot to ensure all changes take effect"
echo "2. Configure GNOME extensions via Extension Manager"
echo "3. Sign into your accounts (Chrome, Slack, etc.)"
echo "4. Configure development tools as needed"
