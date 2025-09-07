# Common.d Directory

This directory contains modular setup scripts that are executed by `setup.sh` for all system types (both desktop and handheld). The orchestrator runs these scripts first, before any target-specific scripts.

## How it Works

The `setup.sh` script automatically discovers and executes all `.sh` files in lexical order (no executable bit required). This allows for modular, maintainable setup scripts shared across all variants.

## Naming Convention

Scripts are named with a numeric prefix to control execution order:

- `01-*` - System package installations (RPM packages that require user context)
- `10-*` - Early system configuration
- `20-*` - Application-specific configurations and Flatpak installations
- `90-*` - Final setup and cleanup tasks

## Current Scripts

- `01-install-1password.sh` - Installs 1Password GUI app via rpm-ostree (requires user-session context for PolicyKit setup)
- `02-install-warp-terminal.sh` - Installs Warp Terminal via rpm-ostree (requires runtime installation due to container build issues)
- `20-gnome-boxes.sh` - Installs GNOME Boxes virtualization via Flatpak
- `20-install-obsidian.sh` - Installs Obsidian note-taking app via Flatpak
- `20-install-slack.sh` - Installs Slack communication app via Flatpak
- `20-install-utility-flatpaks.sh` - Installs various utility applications via Flatpak

## Why Some Packages Are Here vs Container Build

### Runtime Installation (rpm-ostree in user scripts)
**1Password GUI** - Installed here because:
- PostInstall script requires live user session context
- Needs to discover human users (UID 1000+) for PolicyKit setup
- Creates user-specific desktop integration
- Sets up browser integration with proper permissions
- Container builds don't have the user context needed for proper setup

**Warp Terminal** - Installed here because:
- Simple postinstall script but fails during container build transaction phase
- Reason for container build failure under investigation
- Runtime installation via rpm-ostree works reliably
- Repository configuration and GPG keys handled in container build

### Container Build Installation
**VS Code, podman-docker** - Installed in Containerfile because:
- Simple installation with no user-session dependencies
- System-level integration requirements
- Better performance and reliability when baked into image
- No complex postinstall scripts requiring user context

## Adding New Scripts

To add a new setup script:

1. Create a new `.sh` file with an appropriate numeric prefix
2. Make it executable: `chmod +x your-script.sh`
3. Follow the existing pattern:
   - Use `set -euo pipefail` for strict error handling
   - Include descriptive echo statements
   - Check if tasks are already completed to make scripts idempotent
   - Use `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/..\" && pwd)"` to reference the repo root

## Error Handling

If a script fails, the setup will continue executing remaining scripts. This ensures that one failed component doesn't break the entire setup process.
