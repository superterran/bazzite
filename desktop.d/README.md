# Desktop.d Directory

This directory contains modular setup scripts for desktop-specific configurations. The orchestrator runs `common.d` first, then this directory when the target is `desktop`.

The desktop variant is based on **Bazzite DX**, inheriting a pre-configured development environment.

## DX Base Integration

The desktop variant leverages Bazzite DX's pre-configured environment:
- **VS Code**: Pre-installed and optimized for container development
- **Podman (with Docker CLI)**: Configured with proper devcontainer support via podman-docker
- **Development toolchains**: Node.js, Python, Go, Rust ready out-of-box
- **Container optimization**: User mapping and permissions pre-configured

## Current Scripts

### AI/ML and Development
- `ollama.sh` - Containerized Ollama with CUDA GPU acceleration via Podman
- `opencode.sh` - OpenCode Web UI (port 3333) with Ollama/Poe/LiteLLM providers
- `litellm.sh` - LiteLLM AI routing proxy (port 4000) with cost-tiered model selection
- `mcp-servers.sh` - MCP server installation (mcpvault, basic-memory, phpstan, context7, playwright, commerce-extensibility)

### Networking & Tunneling
- `cloudflared.sh` - Cloudflare Tunnel (opencode.superterran.net → localhost:3333)
- `nfs-exports.sh` - Exports mounted drives and home directory via NFS
- `samba.sh` - Samba file sharing with macOS compatibility
- `ssh.sh` - Enables SSH service
- `ssh-agent-forwarding.sh` - Robust SSH agent forwarding (1Password fallback)
- `ssh-stability.sh` - Fixes SSH stability issues (WiFi power saving, keepalives)
- `ssh-remote-access.sh` - SSH remote access configuration
- `vscode-tunnel.sh` - VS Code tunnel service for remote access

### Hardware & System
- `display-gamescope.sh` - Gamescope display prioritization (DP/HDMI)
- `openrgb.sh` - OpenRGB with custom profiles and systemd service
- `sleep-fix.sh` - NVIDIA GPU sleep/wake fixes
- `shell-config.sh` - Shell configuration and development directories

### Utilities (in `../bin/`)
- `switch-display.sh` - Manage Gamescope display selection
- `switch-session.sh` - Toggle between GNOME and Gamescope sessions
- `toggle-autologin.sh` - Enable/disable GDM auto-login
- `ollama-server` - Ollama server management

## Config Templates

Setup scripts deploy config templates from `config/`:
- `config/opencode/opencode.json` → `~/.config/opencode/opencode.json`
- `config/litellm/config.yaml` → `~/.config/litellm/config.yaml`
- `config/cloudflared/config.yml.example` → `~/.cloudflared/config.yml` (manual copy)
- `config/systemd/user/*.service` → `~/.config/systemd/user/`

## Testing

Run individual scripts directly:
```bash
./desktop.d/ollama.sh
./desktop.d/opencode.sh
./desktop.d/litellm.sh
```

Or run the orchestrator:
```bash
./setup.sh desktop
```
