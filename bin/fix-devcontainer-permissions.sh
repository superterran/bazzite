#!/bin/bash
# Fix devcontainer permissions for Bazzite + Podman setup

set -euo pipefail

echo "🔧 Fixing devcontainer permissions for Bazzite + Podman..."

# Ensure containers.conf exists with proper settings
mkdir -p ~/.config/containers

if [[ ! -f ~/.config/containers/containers.conf ]] || ! grep -q "userns.*keep-id" ~/.config/containers/containers.conf; then
    echo "📝 Updating containers.conf..."
    cat > ~/.config/containers/containers.conf << 'CONF'
[containers]
# Set default user namespace mappings for better file permissions
userns = "keep-id"

[engine]
# Better compatibility with devcontainers
runtime = "crun"
CONF
fi

echo "✅ Devcontainer permissions configured!"
echo "💡 Make sure your devcontainer.json includes:"
echo "   - \"remoteUser\": \"node\""
echo "   - \"updateRemoteUserUID\": true"
echo "   - \"containerUser\": \"node\""

# Check if VS Code devcontainer extension is available
if command -v code &> /dev/null; then
    echo "🔄 You may need to rebuild your devcontainer for changes to take effect."
    echo "   Use: Ctrl+Shift+P -> 'Dev Containers: Rebuild Container'"
fi
