# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This repository builds custom Bazzite OS variants (desktop and handheld) using container-based immutable Linux distribution techniques. Bazzite is based on Universal Blue and uses rpm-ostree for system management.

**Key variants:**
- **Desktop**: `ghcr.io/superterran/bazzite:desktop` - NVIDIA GPU optimized desktop system
- **Handheld**: `ghcr.io/superterran/bazzite:handheld` - ROG Ally X optimized handheld system

## Essential Development Commands

### Building Images
```bash
# Build specific variants
just build-handheld
just build-desktop
just build-all

# Build for registry
just build-handheld-release
just build-desktop-release

# Push to registry (requires login)
just push-handheld
just push-desktop
just push-all
```

### Testing and Development
```bash
# Run variants interactively
just run-handheld
just run-desktop

# Test package installations
just test-desktop-packages
just test-handheld-packages

# Local system rebasing for testing
just rebase-desktop-local
just rebase-handheld-local
```

### Setup and Configuration
```bash
# Run modular setup (auto-detects system type)
just setup
./setup.sh

# Force specific target
./setup.sh desktop
./setup.sh handheld
just desktop-setup

# Backup current configuration
just backup-config
./backup-config.sh

# Fresh installation script (for new systems)
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/fresh-install.sh | bash
```

### Container Operations
```bash
# Clean up local images
just clean

# Manual docker builds
docker build --target handheld -t bazzite:handheld .
docker build --target desktop -t bazzite:desktop .
```

## Architecture and Structure

### Container Build System
- **Multi-stage Containerfile**: Builds both desktop and handheld variants from different Bazzite base images
- **Base images**: 
  - Handheld: `ghcr.io/ublue-os/bazzite-deck-gnome:latest`
  - Desktop: `ghcr.io/ublue-os/bazzite-deck-nvidia-gnome:latest`
- **Build-time customization**: Minimal - only repository configurations are added during build
- **Runtime setup**: All software installation and configuration happens via modular setup scripts

### Modular Setup System
The repository uses a sophisticated modular setup system with execution order control:

**Directory structure:**
- `common.d/` - Scripts run on all system types (Flatpak installations, basic setup)
- `desktop.d/` - Desktop-specific scripts (OpenRGB, SSH, hardware-specific fixes)
- `handheld.d/` - Handheld-specific scripts (will be created as needed for handheld customizations)

**Execution order:** Scripts are executed in lexical order using numeric prefixes:
- `01-*` - System package installations (RPM packages)
- `10-*` - Early user configuration
- `20-*` - Application-specific configurations  
- `90-*` - Final setup tasks
- `100-*` - System-level fixes and optimizations

**Key characteristics:**
- Scripts are bash executed regardless of executable bit
- Error handling: Failed scripts don't stop execution of remaining scripts
- Idempotent: Scripts check for existing installations/configurations
- Auto-detection: `setup.sh` detects system type (desktop vs handheld) automatically

### Configuration Management
- `config/yum.repos.d/` - Third-party repository configurations (1Password, Warp Terminal, VS Code)
- `config/openrgb/` - RGB lighting profiles and configurations
- `config/systemd/user/` - User-level systemd service files
- `bin/` - Utility scripts (display switching, etc.)

### Version Control and CI/CD
- **GitHub Actions**: Automated builds on push to main branch and weekly rebuilds
- **Container registry**: GitHub Container Registry (`ghcr.io/superterran/bazzite`)
- **Multi-variant matrix builds**: Single workflow builds both desktop and handheld variants
- **Base image updates**: Weekly scheduled rebuilds capture upstream Bazzite updates

## Development Workflow for System Customizations

When making changes to desktop or handheld system configurations, follow this standardized procedure:

### 1. Create Modular Script
- Create a new `.sh` file in the appropriate directory (`common.d/`, `desktop.d/`, or `handheld.d/`)
- Use numeric prefix to control execution order (see naming convention above)
- Follow existing script patterns:
  ```bash
  #!/bin/bash
  set -euo pipefail
  
  # Script description and purpose
  echo "Setting up [feature name]..."
  
  # Check if already configured (idempotency)
  if [[ condition_to_check_existing_setup ]]; then
      echo "[Feature] already configured, skipping..."
      exit 0
  fi
  
  # Implementation
  # ...
  
  echo "[Feature] setup completed successfully"
  ```

### 2. Execute and Test Script
- Make script executable: `chmod +x path/to/script.sh`
- Test script individually: `./desktop.d/XX-feature-name.sh`
- Test via orchestrator: `./setup.sh [desktop|handheld]`
- Verify functionality and check for any issues

### 3. Validate Results
- Confirm the intended configuration is applied
- Test that the feature works as expected
- Ensure script is idempotent (can run multiple times safely)
- Verify no negative impact on existing functionality

### 4. Document and Commit
- Update relevant README.md files (especially `desktop.d/README.md` or `handheld.d/README.md`)
- Add script description to the current scripts list
- Commit changes with descriptive commit message
- Consider updating this WARP.md if the change affects development workflow

### Example Workflow
```bash
# 1. Create script
vi desktop.d/25-setup-new-feature.sh

# 2. Test execution
chmod +x desktop.d/25-setup-new-feature.sh
./desktop.d/25-setup-new-feature.sh

# 3. Validate via full setup
./setup.sh desktop

# 4. Document and commit
vi desktop.d/README.md  # Add script description
git add desktop.d/25-setup-new-feature.sh desktop.d/README.md
git commit -m "Add feature X setup for desktop systems"
```

## System Integration

### rpm-ostree Integration
This is an immutable Linux distribution using rpm-ostree:
- System changes require rebasing: `sudo rpm-ostree rebase <image>`
- Updates: `sudo rpm-ostree upgrade` followed by reboot
- Layered packages: Most software installed as Flatpaks or via setup scripts
- System configuration: Handled through modular setup scripts post-rebase

### Hardware-Specific Features
- **NVIDIA GPU support**: Desktop variant includes NVIDIA drivers and power management fixes
- **ROG Ally X optimization**: Handheld variant optimized for gaming handheld form factor
- **OpenRGB integration**: Automated RGB lighting control with "lights off" profiles
- **Display management**: Custom display switching utilities for multi-monitor setups
- **Gaming optimizations**: Gamescope configuration for Steam Big Picture mode

### Development Workflow
1. **Code changes**: Modify setup scripts, configurations, or container build
2. **Local testing**: Build and test variants locally using `just` commands
3. **System testing**: Use local rebase commands to test on actual hardware
4. **CI validation**: Push to main triggers automated builds
5. **Deployment**: Users rebase to new images using `rpm-ostree rebase`

## Important Notes

- **Immutable base**: The OS layer is immutable; all customizations happen via layered packages or user-space configuration
- **Modular design**: Setup scripts are designed to be independently executable and idempotent
- **Hardware detection**: System automatically detects desktop vs handheld and applies appropriate configurations
- **Container-first**: Development and deployment use container images as the primary artifact
- **User-space focus**: Most applications installed as Flatpaks to avoid modifying the base system
- **Customization workflow**: Always use the modular script approach for system changes to maintain consistency and reproducibility
