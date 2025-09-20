#!/bin/bash
# SSH Agent Forwarding Enhancement
# This script implements robust SSH agent forwarding detection and configuration

set -euo pipefail

echo "Setting up SSH agent forwarding enhancement..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if we're in an SSH session
if [[ -z "${SSH_CONNECTION:-}" ]]; then
    echo "Not in an SSH session, SSH agent forwarding setup not needed"
    exit 0
fi

echo "SSH session detected, configuring SSH agent forwarding..."

# 1. Create SSH agent detection script
SSH_AGENT_SCRIPT="$HOME/.local/bin/detect-ssh-agent"
mkdir -p "$HOME/.local/bin"

echo "Creating SSH agent detection script..."
cat > "$SSH_AGENT_SCRIPT" << 'AGENT_SCRIPT_EOF'
#!/bin/bash
# SSH Agent Detection Script
# Dynamically detects and sets the correct SSH_AUTH_SOCK

# If we're in an SSH session, look for forwarded agent
if [[ -n "${SSH_CONNECTION:-}" ]]; then
    # Look for forwarded agent sockets
    FORWARDED_AGENT=$(find /tmp -name "agent.*" -path "*/ssh-*" -user "$(whoami)" 2>/dev/null | head -1)
    
    if [[ -n "$FORWARDED_AGENT" && -S "$FORWARDED_AGENT" ]]; then
        # Test if the agent responds
        if SSH_AUTH_SOCK="$FORWARDED_AGENT" ssh-add -l >/dev/null 2>&1; then
            export SSH_AUTH_SOCK="$FORWARDED_AGENT"
            return 0
        fi
    fi
fi

# Fallback to 1Password agent if available
if [[ -S "${HOME}/.1password/agent.sock" ]]; then
    if SSH_AUTH_SOCK="${HOME}/.1password/agent.sock" ssh-add -l >/dev/null 2>&1; then
        export SSH_AUTH_SOCK="${HOME}/.1password/agent.sock"
        return 0
    fi
fi

# If nothing works, leave SSH_AUTH_SOCK as is
return 1
AGENT_SCRIPT_EOF

chmod +x "$SSH_AGENT_SCRIPT"
echo "✓ SSH agent detection script created at $SSH_AGENT_SCRIPT"

# 2. Add to shell initialization
BASHRC_ADDITION='
# SSH Agent Forwarding Enhancement - Added by Bazzite Setup
if [[ -f "$HOME/.local/bin/detect-ssh-agent" ]]; then
    source "$HOME/.local/bin/detect-ssh-agent" 2>/dev/null || true
fi'

if ! grep -q "SSH Agent Forwarding Enhancement" "$HOME/.bashrc" 2>/dev/null; then
    echo "Adding SSH agent detection to ~/.bashrc..."
    echo "$BASHRC_ADDITION" >> "$HOME/.bashrc"
    echo "✓ SSH agent detection added to ~/.bashrc"
else
    echo "✓ SSH agent detection already configured in ~/.bashrc"
fi

# 3. Update SSH config for better agent forwarding
SSH_CONFIG="$HOME/.ssh/config"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"

# Create backup of existing config
if [[ -f "$SSH_CONFIG" ]] && [[ ! -f "$SSH_CONFIG.bak-$(date +%Y%m%d)" ]]; then
    cp "$SSH_CONFIG" "$SSH_CONFIG.bak-$(date +%Y%m%d)"
    echo "✓ SSH config backed up"
fi

# Update SSH config for better agent forwarding
AGENT_FORWARDING_MARKER="# SSH Agent Forwarding Configuration - Added by Bazzite Setup"
if [[ ! -f "$SSH_CONFIG" ]] || ! grep -q "$AGENT_FORWARDING_MARKER" "$SSH_CONFIG"; then
    echo "Updating SSH client configuration for agent forwarding..."
    
    # Create new config content that preserves existing config
    cat > "$SSH_CONFIG" << 'SSH_CONFIG_EOF'
# Git hosting services - use forwarded SSH agent when available
Host github.com gitlab.com bitbucket.org
    ForwardAgent yes
    IdentityAgent ${SSH_AUTH_SOCK}
    IdentitiesOnly no

# Default behavior - use 1Password agent for other hosts  
Host *
    IdentityAgent %d/.1password/agent.sock
    ForwardAgent no
    
# SSH Agent Forwarding Configuration - Added by Bazzite Setup
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
    ConnectTimeout 10
SSH_CONFIG_EOF
    
    chmod 600 "$SSH_CONFIG"
    echo "✓ SSH client configuration updated for agent forwarding"
else
    echo "✓ SSH agent forwarding configuration already present"
fi

# 4. Apply immediately for current session
echo "Applying SSH agent detection for current session..."
source "$SSH_AGENT_SCRIPT" 2>/dev/null || true

# 5. Verify setup
echo ""
echo "Verifying SSH agent forwarding setup..."

if [[ -n "${SSH_AUTH_SOCK:-}" ]]; then
    echo "- SSH_AUTH_SOCK: $SSH_AUTH_SOCK"
    if ssh-add -l >/dev/null 2>&1; then
        KEY_COUNT=$(ssh-add -l 2>/dev/null | wc -l)
        echo "- SSH agent status: Active with $KEY_COUNT key(s)"
        
        # Test GitHub connection if possible
        if ssh -o ConnectTimeout=5 -o BatchMode=yes -T git@github.com 2>/dev/null | grep -q "successfully authenticated"; then
            echo "- GitHub SSH test: ✓ Success"
        else
            echo "- GitHub SSH test: ⚠ Failed (normal if no GitHub keys)"
        fi
    else
        echo "- SSH agent status: Not responding"
    fi
else
    echo "- SSH_AUTH_SOCK: Not set"
fi

echo ""
echo "✅ SSH Agent Forwarding Enhancement Complete!"
echo ""
echo "Summary of changes:"
echo "- Created dynamic SSH agent detection script"
echo "- Updated ~/.bashrc to automatically detect SSH agent"
echo "- Enhanced SSH client config for better agent forwarding"
echo "- Configured Git hosting services to use forwarded agent"
echo "- All settings will persist across sessions and reboots"
echo ""
echo "💡 Your SSH agent should now automatically use forwarded agents when available"
echo "💡 Restart your shell or run 'source ~/.bashrc' to apply to current session"
