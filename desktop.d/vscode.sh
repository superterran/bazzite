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

# Backup existing config if it exists
if [[ -f ~/.config/containers/containers.conf ]]; then
    backup_file=~/.config/containers/containers.conf.bak.$(date +%Y%m%d%H%M%S)
    echo "Backing up existing containers.conf to $backup_file"
    cp ~/.config/containers/containers.conf "$backup_file"
fi

cat > ~/.config/containers/containers.conf << 'EOF_CONF'
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

# Fix devcontainer feature build issues on rootless + SELinux
# Prevents permission denied errors during RUN --mount operations
userns = "keep-id"
label = false

[engine]
# Optimize for performance
runtime = "crun"
events_logger = "file"
EOF_CONF

# Backup existing storage.conf if it exists
if [[ -f ~/.config/containers/storage.conf ]]; then
    backup_file=~/.config/containers/storage.conf.bak.$(date +%Y%m%d%H%M%S)
    echo "Backing up existing storage.conf to $backup_file"
    cp ~/.config/containers/storage.conf "$backup_file"
fi

# Configure storage.conf for performance
cat > ~/.config/containers/storage.conf << 'EOF_STORAGE'
[storage]
driver = "overlay"
runroot = "/run/user/1000/containers"
graphroot = "/var/home/me/.local/share/containers/storage"

[storage.options]
# Optimize overlay storage for performance and rootless compatibility
overlay.mountopt = "nodev,metacopy=on"
# Use fuse-overlayfs for better rootless support
mount_program = "/usr/bin/fuse-overlayfs"
EOF_STORAGE

# Backup existing registries.conf if it exists
if [[ -f ~/.config/containers/registries.conf ]]; then
    backup_file=~/.config/containers/registries.conf.bak.$(date +%Y%m%d%H%M%S)
    echo "Backing up existing registries.conf to $backup_file"
    cp ~/.config/containers/registries.conf "$backup_file"
fi

# Configure registries.conf to prevent interactive prompts and default to Docker Hub
echo "Configuring container registries to prevent interactive prompts..."
cat > ~/.config/containers/registries.conf << 'EOF_REGISTRIES'
# Container registries configuration for devcontainer compatibility
# Using registries.conf v2 format only

# Default to Docker Hub for unqualified image names
# This prevents "Please select an image" interactive prompts
unqualified-search-registries = ["docker.io"]

# Registry configuration
[[registry]]
prefix = "docker.io"
location = "docker.io"

[[registry]]
prefix = "registry.fedoraproject.org"
location = "registry.fedoraproject.org"

[[registry]]
prefix = "registry.access.redhat.com"
location = "registry.access.redhat.com"

[[registry]]
prefix = "quay.io"
location = "quay.io"
EOF_REGISTRIES

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
echo ""
echo "✓ Podman configured for VS Code devcontainer compatibility with:"
echo "  • User namespace mapping for bind mounts (userns=keep-id)"
echo "  • SELinux labeling disabled for containers (label=false)"
echo "  • fuse-overlayfs for better rootless performance" 
echo "  • File-based event logging to avoid journald issues"
echo "  • Docker Hub as default registry (prevents interactive prompts)"
echo ""
echo "DevContainer features should now build without permission errors or registry prompts."
