# Desktop.d Directory

This directory contains modular setup scripts that are executed by `setup.sh` when setting up desktop-specific configurations. The orchestrator runs `common.d` first, then this directory when the target is `desktop`.

## How it Works

The `setup.sh` script automatically discovers and executes all `.sh` files in lexical order (no executable bit required). This allows for modular, maintainable setup scripts.

## Naming Convention

Scripts are named with a numeric prefix to control execution order:

- `01-*` - System package installations (RPM packages)
- `10-*` - Early user configuration for desktop
- `20-*` - Application-specific configurations
- `90-*` - Final setup and cleanup tasks
- `100-*` - System-level fixes and optimizations

## Current Scripts

- `02-install-warp-terminal.sh` - Verifies Warp Terminal installation (Warp requires user-session context for proper setup)
- `10-install-vscode.sh` - Configures VS Code (installed via container build) and podman for optimal devcontainer performance
- `10-setup-basic-memory.sh` - Installs basic-memory MCP server for VS Code and other tools
- `10-setup-ollama.sh` - Installs Ollama via Homebrew for AI model management with GPU acceleration and Alpaca compatibility
- `10-setup-shell-config.sh` - Sets up shell configuration and development directories
- `20-setup-openrgb.sh` - Configures OpenRGB with custom profiles and systemd service
- `20-setup-ssh.sh` - Enables SSH service for remote connections using ujust
- `21-setup-vscode-tunnel.sh` - Configures VS Code tunnel for remote development
- `22-fix-ssh-stability.sh` - Fixes SSH stability issues and configuration
- `25-setup-gamescope-display.sh` - Configures gamescope to prioritize HDMI over DisplayPort for Steam Big Picture mode
- `100-fix-sleep-issues.sh` - Fixes NVIDIA GPU sleep/wake issues and USB wake-up problems

## Adding New Scripts

To add a new setup script:

1. Create a new `.sh` file with an appropriate numeric prefix
2. Make it executable: `chmod +x your-script.sh`
3. Follow the existing pattern:
   - Use `set -euo pipefail` for strict error handling
   - Include descriptive echo statements
   - Check if tasks are already completed to make scripts idempotent
   - Use `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"` to reference the repo root

## Error Handling

If a script fails, the desktop setup will continue executing remaining scripts. This ensures that one failed component doesn't break the entire setup process.

## Testing

You can test individual scripts by running them directly:

```bash
./desktop.d/01-install-1password.sh
```

Or run the orchestrator (auto-detects target, or pass `desktop` explicitly):

```bash
./setup.sh desktop
```
