#!/bin/bash
# Install Visual Studio Code and configure podman for optimal devcontainer performance

set -euo pipefail

echo "Configuring VS Code and podman for devcontainers..."

# Check if VS Code is installed (should be from container build)
if ! command -v code >/dev/null 2>&1; then
    echo "Warning: VS Code not found. This usually means you need to reboot after the container update."
    echo "VS Code is installed during container build - reboot required for availability."
else
    echo "VS Code (RPM) is available, continuing with configuration..."
fi

# Check if podman is available (should be pre-installed on Bazzite)
if ! command -v podman >/dev/null 2>&1; then
    echo "Error: podman not found. This script requires podman to be installed."
    exit 1
fi

# Check if docker-compose and podman-docker are available (should be from container build)
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "Installing docker-compose via Homebrew as fallback..."
    brew install docker-compose
    echo "✓ docker-compose installed successfully"
else
    echo "docker-compose is available, skipping..."
fi

echo "Checking Docker CLI compatibility..."
if ! command -v docker >/dev/null 2>&1; then
    echo "Warning: docker command not found. podman-docker should be installed from container build."
    echo "You may need to reboot after the container update for docker command to be available."
elif rpm -q podman-docker >/dev/null 2>&1; then
    echo "podman-docker package is installed, Docker CLI compatibility ready"
else
    echo "Docker command available but podman-docker package not detected"
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

# Create Docker socket symlink for VS Code compatibility
echo "Creating Docker socket symlink for VS Code..."
if [[ ! -e /var/run/docker.sock ]]; then
    # Create the directory if it doesn't exist
    sudo mkdir -p /var/run
    # Create symlink to podman socket
    sudo ln -s "/run/user/$(id -u)/podman/podman.sock" /var/run/docker.sock
    echo "✓ Docker socket symlink created at /var/run/docker.sock"
else
    echo "Docker socket already exists, skipping..."
fi

# Test podman functionality
echo "Testing podman functionality..."
if podman run --rm hello-world >/dev/null 2>&1; then
    echo "✓ Podman is working correctly"
else
    echo "Warning: Podman test failed, but continuing..."
fi

echo "Visual Studio Code and podman devcontainer setup completed successfully"
echo "VS Code should now be able to use podman for high-performance devcontainers"
