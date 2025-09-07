#!/bin/bash
set -euo pipefail

# Install basic-memory MCP server for VS Code and other tools
echo "Setting up basic-memory MCP server..."

# Check if already installed
if command -v basic-memory &> /dev/null; then
    echo "basic-memory already installed, skipping..."
    exit 0
fi

# Install basic-memory via npm (assuming it's available via npm)
# If it's available via other package managers, adjust accordingly
if command -v npm &> /dev/null; then
    echo "Installing basic-memory via npm..."
    npm install -g basic-memory
elif command -v brew &> /dev/null; then
    echo "Installing basic-memory via Homebrew..."
    brew install basic-memory
else
    echo "Warning: Neither npm nor brew found. Please install basic-memory manually."
    echo "You can install it via:"
    echo "  npm install -g basic-memory"
    echo "  or"
    echo "  brew install basic-memory"
    exit 1
fi

# Verify installation
if command -v basic-memory &> /dev/null; then
    echo "basic-memory MCP server setup completed successfully"
    basic-memory --version
else
    echo "Warning: basic-memory installation may have failed"
    exit 1
fi
