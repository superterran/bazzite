# Custom Bazzite Variants

This repository contains custom Bazzite variants optimized for my personal setup:

- **Handheld (ROG Ally X)**: `ghcr.io/superterran/bazzite:handheld`
- **Desktop**: `ghcr.io/superterran/bazzite:desktop`

## Features

- **Pre-installed software**: 
  - **1Password** - Password manager and secure vault
  - **Visual Studio Code** - Full-featured code editor and IDE
  - **Docker Compose** - Container orchestration
  - **GNOME Boxes** - Virtual machine manager
  - **Podman Docker** - Docker compatibility layer
  - **Warp Terminal** - Modern terminal emulator
- **User-level setup**: Script for Flatpaks and services
- **Automated builds**: GitHub Actions for continuous integration
- **Easy deployment**: Works on new installs and existing systems

## Quick Start

### Fresh Installation (New Systems)

For completely new systems, follow these steps:

1. **Install standard Bazzite first**:
   - Download from [bazzite.gg](https://bazzite.gg)
   - Choose the base variant that matches your hardware
   - Flash to USB and install normally

2. **Switch to custom variant** (after first boot):
   ```bash
   # Auto-detect and rebase (recommended)
   curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/fresh-install.sh | bash
   ```

3. **Complete setup** (after reboot):
   ```bash
   # Install apps and configure system (auto-detects desktop/handheld)
   curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/desktop-setup.sh | bash
   ```

### For Existing Bazzite Systems
Rebase to the custom variant:

```bash
# For ROG Ally X (handheld)
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:handheld

# For Desktop with NVIDIA
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:desktop

# Reboot to apply changes
sudo systemctl reboot
```

### Post-Rebase Setup
After rebasing and rebooting, run the setup script:

```bash
# Smart setup - automatically detects desktop vs handheld
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/desktop-setup.sh | bash
```

**Or run setup manually with the unified orchestrator:**

```bash
# Run only common modules (Flatpaks, user services, shell config)
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/user-setup.sh | bash

# Run desktop-specific modules (includes common first)
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/desktop-setup.sh | bash -s -- desktop

# Run handheld-specific modules (if/when present)
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/desktop-setup.sh | bash -s -- handheld
```

This will (common modules):
- Install common Flatpak applications (Slack, Obsidian, etc.)
- Enable user services (ollama, sunshine) when available
- Set up shell and development directories

### Desktop-Specific Setup
For desktop systems that need OpenRGB configuration:

```bash
# Download and run the desktop setup script
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/desktop-setup.sh | bash
```

This will:
- Install and configure OpenRGB with the "Ideal" profile (turns off all RGB lights)
- Set up OpenRGB to start automatically on login
- Configure the systemd service for RGB control

## Local Development

Build images locally using just commands:

```bash
# Build handheld variant
ujust build-handheld

# Build desktop variant  
ujust build-desktop

# Build both variants
ujust build-all
```

## Updating

Images are automatically built when changes are pushed to main. To update:

```bash
sudo rpm-ostree upgrade
sudo systemctl reboot
```
