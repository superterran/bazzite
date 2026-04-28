# Common.d Directory

This directory contains modular setup scripts that are executed by `setup.sh` for all system types (both desktop and handheld). The orchestrator runs these scripts first, before any target-specific scripts.

**Note:** The desktop variant is based on Bazzite DX and inherits VS Code, Docker, and development toolchains. These scripts focus on additional applications and user-level configuration.

## How it Works

The `setup.sh` script automatically discovers and executes all `.sh` files in lexical order (no executable bit required). This allows for modular, maintainable setup scripts shared across all variants.

## Current Scripts

### Security & Authentication
- `1password.sh` - Installs 1Password GUI app via rpm-ostree (requires user-session context)

### AI & Development Tools
- `claude.sh` - Installs Claude CLI (AI coding assistant)

### File Synchronization
- `syncthing.sh` - Installs and configures Syncthing with systemd service (desktop ↔ handheld sync)

### Productivity
- `obsidian.sh` - Installs Obsidian note-taking app via Flatpak

### Communication & Utilities
- `slack.sh` - Installs Slack communication app via Flatpak
- `utility-flatpaks.sh` - Installs utility applications (Flatseal, Extension Manager, Mission Center, etc.)

## Why Some Packages Are Here vs Container Build

### Container Build (Minimal)
**Repository configurations only** — Added in Dockerfile:
- 1Password repository and GPG keys
- No actual package installations at build time

### Runtime Installation (in setup scripts)
**1Password GUI** — Installed here because PostInstall requires live user session context for PolicyKit setup and browser integration.

### Linuxbrew
**Syncthing, Claude CLI** — Installed via Homebrew to avoid rpm-ostree layering and reboots on this immutable OS.

## Adding New Scripts

1. Create a new `.sh` file with a descriptive name
2. Make it executable: `chmod +x your-script.sh`
3. Follow the existing pattern with `set -euo pipefail` and idempotency checks
4. Reference repo root: `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"`

## Error Handling

If a script fails, the setup will continue executing remaining scripts.
