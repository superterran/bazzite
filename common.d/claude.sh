#!/bin/bash
set -euo pipefail

echo "Setting up Claude CLI..."

# Check if Claude CLI is already installed
if command -v claude >/dev/null 2>&1; then
    echo "Claude CLI already installed"
    exit 0
fi

# Install Claude CLI
# Claude CLI installs to ~/.local/bin
if [[ -f "$HOME/.local/bin/claude" ]]; then
    echo "Claude CLI binary exists at ~/.local/bin/claude"
    exit 0
fi

echo "Installing Claude CLI..."

# Claude CLI is distributed via npm
if command -v npm >/dev/null 2>&1; then
    npm install -g @anthropic-ai/claude-code
    echo "Claude CLI installed via npm"
else
    echo "WARNING: npm not found. Install Node.js via nvm first, then re-run."
    echo "  nvm install --lts"
    echo "  npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo ""
echo "Claude CLI setup completed successfully"
echo ""
echo "Run 'claude' to start an interactive session."
echo "MCP servers can be registered via desktop.d/mcp-servers.sh"
