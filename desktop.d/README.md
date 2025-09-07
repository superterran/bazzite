# Desktop.d Directory

This directory contains modular setup scripts that are executed by `setup.sh` when setting up desktop-specific configurations. The orchestrator runs `common.d` first, then this directory when the target is `desktop`.

## How it Works

The `setup.sh` script automatically discovers and executes all `.sh` files in lexical order (no executable bit required). This allows for modular, maintainable setup scripts.

## Naming Convention

**Updated**: Scripts now use descriptive names without numeric prefixes for easier identification and tab completion. The setup orchestrator executes scripts in alphabetical order, but dependencies are managed through script logic rather than execution order.

**Benefits**:
- Easy tab completion: Type `./desktop.d/oll<TAB>` to run `ollama.sh`
- Self-documenting: Script names clearly indicate their purpose
- Flexible execution: Run individual scripts directly without memorizing numbers

## Current Scripts

### Core Applications
- `ollama.sh` - Containerized Ollama with CUDA GPU acceleration via Podman
- `vscode.sh` - Configures VS Code and podman for optimal devcontainer performance

### System Configuration
- `display-gamescope.sh` - Configures gamescope to prioritize HDMI over DisplayPort
- `basic-memory-mcp.sh` - Installs basic-memory MCP server for VS Code and other tools
- `shell-config.sh` - Sets up shell configuration and development directories
- `sleep-fix.sh` - Fixes NVIDIA GPU sleep/wake issues and USB wake-up problems

### Hardware & Peripherals
- `openrgb.sh` - Configures OpenRGB with custom profiles and systemd service

### Network & Remote Access
- `ssh.sh` - Enables SSH service for remote connections using ujust
- `ssh-stability.sh` - Fixes SSH stability issues and configuration
- `vscode-tunnel.sh` - Configures VS Code tunnel for remote development

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
./desktop.d/ollama.sh
# or any script by name:
./desktop.d/vscode.sh
./desktop.d/openrgb.sh
```

Or run the orchestrator (auto-detects target, or pass `desktop` explicitly):

```bash
./setup.sh desktop
```
