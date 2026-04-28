# Custom Bazzite Variants

This repository contains custom Bazzite variants optimized for personal setup:

- **Desktop**: `ghcr.io/superterran/bazzite:desktop` (based on Bazzite DX with NVIDIA)
- **Handheld (ROG Ally X)**: `ghcr.io/superterran/bazzite:handheld`

## Features

### Desktop Variant (DX Base)

**Inherited from Bazzite DX:**
- Visual Studio Code with dev containers support
- Podman with Docker CLI compatibility (podman-docker)
- Development toolchains (Node.js, Python, Go, Rust)
- Distrobox & Toolbox for container-based dev environments
- GitHub CLI & Git

**Runtime setup (via setup scripts):**
- **1Password** — Password manager with SSH agent integration
- **Syncthing** — Continuous file sync between desktop and ROG Ally
- **Claude CLI** — AI coding assistant with MCP server integrations
- **OpenCode** — AI coding web UI (port 3333) with Ollama, Poe, and LiteLLM providers
- **Cloudflare Tunnel** — Exposes OpenCode via `opencode.superterran.net`
- **LiteLLM Proxy** — AI routing gateway with cost-tiered model selection
- **MCP Servers** — mcpvault, basic-memory, phpstan, context7, playwright, commerce-extensibility
- **Ollama** — Local AI models with CUDA GPU acceleration (RTX 4070)
- **OpenRGB** — RGB lighting control with custom profiles
- **SSH enhancements** — Agent forwarding, stability fixes, VS Code tunnel
- **Flatpak applications** — Slack, Obsidian, utilities

### Handheld Variant (ROG Ally X)

**Runtime setup:**
- **1Password** — SSH agent integration
- **Syncthing** — Game save and config sync with desktop
- **Flatpak applications** — Obsidian, utilities

### General Features
- Modular setup system with auto-detection (desktop vs handheld)
- Automated builds via GitHub Actions
- Config templates for all services (OpenCode, LiteLLM, Cloudflare Tunnel)
- Systemd unit templates in `config/systemd/user/`

## Quick Start

### Fresh Installation

1. **Install standard Bazzite** from [bazzite.gg](https://bazzite.gg)
   - Desktop: Choose **Bazzite DX** variant (NVIDIA)
   - Handheld: Choose base Bazzite Deck variant

2. **Switch to custom variant:**
   ```bash
   curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/fresh-install.sh | bash
   ```

3. **Complete setup** (after reboot):
   ```bash
   curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash
   ```

### Existing Systems

```bash
# Desktop with NVIDIA
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:desktop

# ROG Ally X (handheld)
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:handheld

sudo systemctl reboot
```

Then run setup:
```bash
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash
```

## Repository Structure

```
common.d/           # Scripts for all systems
├── 1password.sh    # 1Password with SSH agent
├── claude.sh       # Claude CLI installation
├── syncthing.sh    # Syncthing file sync service
├── obsidian.sh     # Obsidian (Flatpak)
├── slack.sh        # Slack (Flatpak)
└── utility-flatpaks.sh

desktop.d/           # Desktop-only scripts
├── cloudflared.sh   # Cloudflare Tunnel setup
├── display-gamescope.sh
├── litellm.sh       # LiteLLM AI routing proxy
├── mcp-servers.sh   # MCP server installation
├── nfs-exports.sh
├── ollama.sh        # Ollama with CUDA GPU
├── opencode.sh      # OpenCode Web UI
├── openrgb.sh
├── samba.sh
├── shell-config.sh
├── sleep-fix.sh
├── ssh.sh
├── ssh-agent-forwarding.sh
├── ssh-remote-access.sh
├── ssh-stability.sh
└── vscode-tunnel.sh

handheld.d/          # Handheld-only scripts (ROG Ally X)
├── syncthing.sh     # Handheld-specific sync config
└── README.md

config/              # Configuration templates
├── cloudflared/     # Cloudflare Tunnel config template
├── litellm/         # LiteLLM proxy config (cost-tiered routing)
├── opencode/        # OpenCode config (Ollama + MCP servers)
├── openrgb/         # RGB lighting profiles
├── systemd/user/    # Systemd unit templates
└── yum.repos.d/     # Package repository configs (1Password)

bin/                 # Utility scripts
├── ollama-server
├── switch-display.sh
├── switch-session.sh
└── toggle-autologin.sh
```

## Local Development

```bash
just build-desktop        # Build desktop image
just build-handheld       # Build handheld image
just build-all            # Build both

just setup                # Run setup (auto-detects system)
just desktop-setup        # Desktop setup
just handheld-setup       # Handheld setup
just setup-ally           # Run setup on ROG Ally via SSH

just backup-config        # Backup current system config
```

## Remote Access (SSH)

The desktop variant is configured for secure remote access via SSH on a non-standard port with Cloudflare DDNS:

```bash
ssh -p 2222 desktop.superterran.net
```

**SSH client config** (`~/.ssh/config`):
```
Host desktop
    HostName desktop.superterran.net
    Port 2222
    User doug
```

**Security hardening** (applied automatically by `desktop.d/ssh-remote-access.sh`):
- Public key authentication only (passwords disabled)
- Non-standard port (2222) to reduce noise
- Root login disabled, max 3 auth attempts
- SELinux and firewall configured for port 2222
- Default SSH port (22) removed from firewall

**Cloudflare DDNS** keeps `desktop.superterran.net` pointed at the current public IP, updating every 5 minutes via a systemd timer. Credentials are stored in `/etc/cloudflare/ddns.env`.

## Updating

Images are automatically rebuilt weekly (Fridays) and on every push to main:

```bash
sudo rpm-ostree upgrade
sudo systemctl reboot
```
