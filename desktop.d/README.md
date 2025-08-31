# Desktop.d Directory

This directory contains modular setup scripts that are executed by `desktop-setup.sh` when setting up desktop-specific configurations.

## How it Works

The `desktop-setup.sh` script automatically discovers and executes all executable `.sh` files in this directory in alphabetical order. This allows for modular, maintainable setup scripts.

## Naming Convention

Scripts are named with a numeric prefix to control execution order:

- `01-*` - System package installations (RPM packages)
- `10-*` - User configuration and shell setup
- `20-*` - Application-specific configurations
- `90-*` - Final setup and cleanup tasks
- `100-*` - System-level fixes and optimizations

## Current Scripts

- `01-install-1password.sh` - Installs 1Password from official RPM
- `02-install-warp-terminal.sh` - Installs Warp Terminal from official RPM  
- `10-setup-shell-config.sh` - Applies bashrc additions and shell configurations
- `20-setup-openrgb.sh` - Configures OpenRGB with custom profiles and systemd service
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

Or test the entire desktop setup:

```bash
./desktop-setup.sh
```
