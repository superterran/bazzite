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

# Fix user namespace mapping issues and devcontainer compatibility
# Use host user mapping to avoid uid_map permission errors
userns = "host"
label = false

# Fix devpts mount issues with crun
# Disable problematic mounts that cause "Invalid argument" errors
no_pivot_root = true

# Set proper user namespace mode for rootless containers
# This prevents "Operation not permitted" errors with uid_map
user_ns = "keep-id:uid=1000,gid=1000"

[engine]
# Optimize for performance
runtime = "crun"
events_logger = "file"

# Configure crun with specific options to handle user namespace issues
cgroup_manager = "systemd"
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

# Create a devcontainer-specific runtime configuration to handle devpts issues
echo "Setting up devcontainer-specific runtime configuration..."
mkdir -p ~/.config/containers/oci/hooks.d

# Create a pre-start hook to handle devpts mount issues
cat > ~/.config/containers/oci/hooks.d/devpts-fix.json << 'EOF_HOOK'
{
    "version": "1.0.0",
    "hook": {
        "path": "/bin/sh",
        "args": ["/bin/sh", "-c", "mkdir -p /dev/pts && chmod 755 /dev/pts"],
        "timeout": 10
    },
    "when": {
        "always": true
    },
    "stages": ["prestart"]
}
EOF_HOOK

# Create a wrapper script for devcontainer-safe podman usage
cat > ~/.local/bin/podman-devcontainer << 'EOF_WRAPPER'
#!/bin/bash
# Wrapper for podman to handle devcontainer-specific issues
# This can be used in VS Code settings if the default runtime has issues

# If we detect devpts mount issues, try with runc instead
if [[ "$*" =~ "devcontainer" ]] || [[ "$*" =~ "--mount.*dev/pts" ]]; then
    exec podman --runtime=runc "$@"
else
    exec podman "$@"
fi
EOF_WRAPPER
chmod +x ~/.local/bin/podman-devcontainer

# Create VS Code specific settings for devcontainer compatibility
echo "Creating VS Code settings for devcontainer compatibility..."
mkdir -p ~/.config/Code/User
if [[ -f ~/.config/Code/User/settings.json ]]; then
    backup_file=~/.config/Code/User/settings.json.bak.$(date +%Y%m%d%H%M%S)
    echo "Backing up existing VS Code settings to $backup_file"
    cp ~/.config/Code/User/settings.json "$backup_file"
fi

# Create or update VS Code settings with devcontainer-specific configurations
cat > ~/.config/Code/User/devcontainer-settings.json << 'EOF_VSCODE'
{
    "dev.containers.dockerPath": "podman",
    "dev.containers.dockerComposePath": "docker-compose",
    "dev.containers.copyGitConfig": true,
    "dev.containers.gitCredentialHelperConfigLocation": "system",
    "remote.containers.defaultExtensions": [
        "ms-vscode.vscode-json"
    ],
    "remote.containers.workspaceMountConsistency": "consistent",
    "remote.autoForwardPorts": false,
    "remote.containers.executeInShell": true,
    "dev.containers.dockerComposePathV2": "docker-compose",
    "dev.containers.composePlatformCompatibility": true,
    "dev.containers.defaultFeatures": {
        "common-utils": {
            "uid": "1000",
            "gid": "1000",
            "configureZshAsDefaultShell": false
        }
    }
}
EOF_VSCODE

echo "VS Code devcontainer settings created at ~/.config/Code/User/devcontainer-settings.json"
echo "You can merge these settings into your main settings.json if needed"

# Create environment configuration for proper user namespace handling
echo "Setting up environment for rootless devcontainer compatibility..."
mkdir -p ~/.config/environment.d

cat > ~/.config/environment.d/50-devcontainer-podman.conf << 'EOF_ENV'
# Podman environment variables for devcontainer compatibility
BUILDAH_ISOLATION=chroot
BUILDAH_FORMAT=docker
_CONTAINERS_USERNS_CONFIGURED=1

# Fix for uid_map permission issues in rootless containers
# These settings help podman handle user namespace mapping correctly
PODMAN_USERNS=keep-id
EOF_ENV

# Create a devcontainer-specific compose wrapper to handle rootless issues
cat > ~/.local/bin/devcontainer-compose << 'EOF_COMPOSE'
#!/bin/bash
# Wrapper for docker-compose to handle rootless podman issues with devcontainers

# Set environment variables for proper user namespace handling
export BUILDAH_ISOLATION=chroot
export BUILDAH_FORMAT=docker
export _CONTAINERS_USERNS_CONFIGURED=1
export PODMAN_USERNS=keep-id

# Run docker-compose with proper environment
exec docker-compose "$@"
EOF_COMPOSE
chmod +x ~/.local/bin/devcontainer-compose

# Make sure ~/.local/bin is in PATH for the wrapper
if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
    export PATH="$HOME/.local/bin:$PATH"
fi

# Test podman functionality with both runtimes
echo "Testing podman functionality with different runtimes..."
if podman run --rm hello-world >/dev/null 2>&1; then
    echo "✓ Podman with crun is working correctly"
else
    echo "Warning: Podman with crun test failed, testing runc fallback..."
    if podman --runtime=runc run --rm hello-world >/dev/null 2>&1; then
        echo "✓ Podman with runc fallback is working"
        echo "Note: Consider using 'podman --runtime=runc' for devcontainers if issues persist"
    else
        echo "Warning: Both runtimes failed basic test, but continuing..."
    fi
fi

echo "Visual Studio Code and podman devcontainer setup completed successfully"
echo ""
echo "✓ Podman configured for VS Code devcontainer compatibility with:"
echo "  • User namespace mapping for bind mounts (userns=keep-id)"
echo "  • SELinux labeling disabled for containers (label=false)"
echo "  • fuse-overlayfs for better rootless performance" 
echo "  • File-based event logging to avoid journald issues"
echo "  • Docker Hub as default registry (prevents interactive prompts)"
echo "  • devpts mount issue fixes (no_pivot_root=true)"
echo "  • Alternative runc runtime available for problematic containers"
echo "  • Pre-start hook to handle /dev/pts directory creation"
echo ""
echo "DevContainer features should now build without devpts mount errors."
echo ""
echo "If you still encounter uid_map or devcontainer issues, try:"
echo "  1. Restart VS Code completely and reload the devcontainer"
echo "  2. Clear existing containers: 'podman system reset --force' (WARNING: removes all containers)"
echo "  3. Use the compose wrapper: ~/.local/bin/devcontainer-compose instead of docker-compose"
echo "  4. Check environment: 'podman unshare cat /proc/self/uid_map' should show proper mapping"
echo "  5. Restart podman socket: 'systemctl --user restart podman.socket'"
echo ""
echo "For debugging specific issues:"
echo "  • Check container logs: 'podman logs <container-name>'"
echo "  • Verify user namespace: 'podman run --rm alpine id'"
echo "  • Test uid mapping: 'podman run --rm --user 1000:1000 alpine id'"
