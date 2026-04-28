#!/bin/bash
set -euo pipefail

echo "Setting up MCP (Model Context Protocol) servers..."

# MCP servers are used by OpenCode, Claude CLI, and VS Code for AI tool integrations.
# They run as stdio subprocesses, not persistent services.

install_npm_global() {
    local pkg="$1"
    local cmd="${2:-$1}"
    if command -v "$cmd" >/dev/null 2>&1; then
        echo "  ✓ $pkg already installed"
    else
        echo "  Installing $pkg..."
        npm install -g "$pkg"
    fi
}

# Ensure npm is available
if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm not found. Ensure Node.js is installed via nvm."
    exit 1
fi

echo ""
echo "Installing npm-based MCP servers..."

install_npm_global "@bitbonsai/mcpvault" "mcpvault"
install_npm_global "@webkult/phpstan-mcp-server" "phpstan-mcp-server"
install_npm_global "@adobe-commerce/commerce-extensibility-tools" "commerce-extensibility-tools-mcp-server"
install_npm_global "@adobe/aio-cli" "aio"
install_npm_global "@upstash/context7-mcp" "context7-mcp"
install_npm_global "@playwright/mcp" "playwright-mcp"

# Install uvx-based MCP servers
echo ""
echo "Installing uvx-based MCP servers..."
if command -v uvx >/dev/null 2>&1; then
    echo "  ✓ uvx available (basic-memory runs via 'uvx basic-memory mcp')"
else
    echo "  WARNING: uvx not found. Install uv for basic-memory support."
fi

# Register MCP servers with Claude CLI if available
if command -v claude >/dev/null 2>&1; then
    echo ""
    echo "Registering MCP servers with Claude CLI..."

    claude mcp add commerce-extensibility -s user -- commerce-extensibility-tools-mcp-server 2>/dev/null || true
    claude mcp add phpstan -s user -- phpstan-mcp-server 2>/dev/null || true
    claude mcp add basic-memory -s user -- uvx basic-memory mcp 2>/dev/null || true
    claude mcp add context7 -s user -- context7-mcp 2>/dev/null || true
    claude mcp add mcpvault -s user -- mcpvault 2>/dev/null || true
    claude mcp add playwright -s user -- playwright-mcp --headless --save-trace --output-dir /tmp/playwright-traces --ignore-https-errors --caps vision 2>/dev/null || true

    echo "  ✓ MCP servers registered with Claude CLI"
else
    echo ""
    echo "Claude CLI not found, skipping MCP registration."
    echo "Install Claude CLI and re-run to register MCP servers."
fi

echo ""
echo "MCP server setup completed successfully"
echo ""
echo "Installed servers:"
echo "  mcpvault              - Obsidian vault access"
echo "  phpstan-mcp-server    - PHP static analysis"
echo "  commerce-extensibility - Adobe Commerce tools"
echo "  context7-mcp          - Up-to-date library documentation"
echo "  playwright-mcp        - Browser automation (headless Chromium)"
echo "  basic-memory          - Knowledge graph (via uvx)"
