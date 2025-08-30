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
After rebasing and rebooting, run the user setup script:

```bash
# Download and run the user setup script
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/user-setup.sh | bash
```

This will:
- Install common Flatpak applications (Chrome, Slack, Obsidian, etc.)
- Enable user services (ollama, openrgb, sunshine)
- Set up development directories

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
