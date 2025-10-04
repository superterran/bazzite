# Common.d Directory

This directory contains modular setup scripts that are executed by `setup.sh` for all system types (both desktop and handheld). The orchestrator runs these scripts first, before any target-specific scripts.

**Note:** The desktop variant is based on Bazzite DX and inherits VS Code, Docker, and development toolchains. These scripts focus on additional applications and user-level configuration.

## How it Works

The `setup.sh` script automatically discovers and executes all `.sh` files in lexical order (no executable bit required). This allows for modular, maintainable setup scripts shared across all variants.

## Naming Convention

**Updated**: Scripts now use descriptive names without numeric prefixes for easier identification and tab completion. The setup orchestrator executes scripts in alphabetical order, but dependencies are managed through script logic rather than execution order.

**Benefits**:
- Easy tab completion: Type `./common.d/war<TAB>` to run `warp.sh`
- Self-documenting: Script names clearly indicate their purpose
- Flexible execution: Run individual scripts directly without memorizing numbers

## Current Scripts

### Security & Authentication
- `1password.sh` - Installs 1Password GUI app via rpm-ostree (requires user-session context)

### Development & Productivity
- `obsidian.sh` - Installs Obsidian note-taking app via Flatpak
- `warp.sh` - Installs Warp Terminal via rpm-ostree (requires user-session context)

### Communication & Utilities
- `slack.sh` - Installs Slack communication app via Flatpak
- `utility-flatpaks.sh` - Installs utility applications (Flatseal, Extension Manager, Mission Center, etc.)

### Notes on DX Base
**GNOME Boxes** is inherited from Bazzite DX base and does not need installation.

## Why Some Packages Are Here vs Container Build

### DX Base (Desktop Only)
**VS Code, Podman (with Docker CLI), Development Tools** - Inherited from Bazzite DX:
- Pre-configured development environment with podman-docker for Docker CLI compatibility
- Optimized for container development (podman and docker commands work interchangeably)
- No installation needed in custom build
- Focus on leveraging what's already provided

### Runtime Installation (rpm-ostree in user scripts)
**1Password GUI** - Installed here because:
- PostInstall script requires live user session context
- Needs to discover human users (UID 1000+) for PolicyKit setup
- Creates user-specific desktop integration
- Sets up browser integration with proper permissions
- Container builds don't have the user context needed for proper setup

**Warp Terminal** - Installed here because:
- Requires user session context for proper setup
- Benefits from runtime installation flexibility
- Repository configuration provided in container build

### Container Build (Minimal)
**Repository configurations only** - Added in Dockerfile:
- 1Password repository and GPG keys
- Warp Terminal repository and GPG keys
- No actual package installations at build time
- All installations happen at runtime for better flexibility

## Adding New Scripts

To add a new setup script:

1. Create a new `.sh` file with a descriptive name (e.g., `application-name.sh`)
2. Make it executable: `chmod +x your-script.sh`
3. Follow the existing pattern:
   - Use `set -euo pipefail` for strict error handling
   - Include descriptive echo statements
   - Check if tasks are already completed to make scripts idempotent
   - Use `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}").." && pwd)"` to reference the repo root

## Error Handling

If a script fails, the setup will continue executing remaining scripts. This ensures that one failed component doesn't break the entire setup process.
