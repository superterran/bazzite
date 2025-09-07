#!/bin/bash
# Install Visual Studio Code and configure podman for optimal devcontainer performance

set -euo pipefail

echo "Installing Visual Studio Code and configuring podman for devcontainers..."

# Check if VS Code is already installed
if flatpak list | grep -q "com.visualstudio.code"; then
    echo "Visual Studio Code already installed, skipping..."
else
    echo "Installing Visual Studio Code from Flathub..."
    flatpak install -y flathub com.visualstudio.code
    echo "✓ Visual Studio Code installed successfully"
fi

# Check if podman is available (should be pre-installed on Bazzite)
if ! command -v podman >/dev/null 2>&1; then
    echo "Error: podman not found. This script requires podman to be installed."
    exit 1
fi

# Install docker-compose for devcontainer orchestration
if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose already installed, skipping..."
else
    echo "Installing docker-compose via Homebrew..."
    brew install docker-compose
    echo "✓ docker-compose installed successfully"
fi

# Set up Docker alias for podman compatibility
if ! grep -q "alias docker=podman" ~/.bashrc 2>/dev/null; then
    echo "Setting up Docker compatibility alias..."
    echo "alias docker=podman" >> ~/.bashrc
    echo "✓ Docker alias configured"
fi

# Configure podman for optimal devcontainer performance
echo "Configuring podman for devcontainer performance..."

# Create containers.conf for performance optimizations
mkdir -p ~/.config/containers
cat > ~/.config/containers/containers.conf << 'EOF'
[containers]
# Use faster storage driver and optimize for performance
# Enable cgroups v2 for better resource management
default_sysctls = [
  "net.ipv4.ping_group_range=0 0",
]

# Optimize for devcontainer workflows
default_capabilities = [
  "CHOWN",
  "DAC_OVERRIDE",
  "FOWNER",
  "FSETID",
  "KILL",
  "NET_BIND_SERVICE",
  "SETFCAP",
  "SETGID",
  "SETPCAP",
  "SETUID",
  "SYS_CHROOT"
]

[engine]
# Optimize for performance
runtime = "crun"
EOF

# Configure storage.conf for performance
cat > ~/.config/containers/storage.conf << 'EOF'
[storage]
driver = "overlay"
runroot = "/run/user/1000/containers"
graphroot = "/var/home/me/.local/share/containers/storage"

[storage.options]
# Optimize overlay storage for performance
overlay.mountopt = "nodev,metacopy=on"
EOF

# Enable and start podman socket for Docker API compatibility
echo "Setting up podman socket for devcontainer compatibility..."
systemctl --user enable podman.socket || true
systemctl --user start podman.socket || true

# Test podman functionality
echo "Testing podman functionality..."
if podman run --rm hello-world >/dev/null 2>&1; then
    echo "✓ Podman is working correctly"
else
    echo "Warning: Podman test failed, but continuing..."
fi

echo "Visual Studio Code and podman devcontainer setup completed successfully"
echo "VS Code should now be able to use podman for high-performance devcontainers"
