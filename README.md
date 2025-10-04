# Custom Bazzite Variants

This repository contains custom Bazzite variants optimized for personal setup:

- **Handheld (ROG Ally X)**: `ghcr.io/superterran/bazzite:handheld`
- **Desktop**: `ghcr.io/superterran/bazzite:desktop` (based on Bazzite DX)

## Features

### Desktop Variant (DX Base)

The desktop variant is based on **Bazzite DX**, which provides a complete development environment out of the box:

**Inherited from Bazzite DX:**
- **Visual Studio Code** - Pre-configured with dev containers support
- **Docker & Podman** - Container development with proper user mapping
- **Development toolchains** - Node.js, Python, Go, Rust, and more
- **Distrobox & Toolbox** - Container-based development environments
- **GitHub CLI & Git** - Version control tools

**Custom additions via container build:**
- Repository configurations for 1Password and Warp Terminal
- GPG keys for third-party repositories

**Runtime setup (via setup scripts):**
- **1Password** - Password manager with SSH agent integration
- **Warp Terminal** - Modern terminal emulator
- **OpenRGB** - RGB lighting control with custom profiles
- **Ollama** - AI/ML tools with CUDA GPU acceleration
- **SSH enhancements** - Agent forwarding, stability fixes, tunnel services
- **Flatpak applications** - Slack, Obsidian, GNOME Boxes, utilities
- **System optimizations** - Sleep fixes, display management, NFS exports

### General Features
- **Modular setup system**: Automated configuration via bash scripts
- **Automated builds**: GitHub Actions for continuous integration
- **Easy deployment**: Works on new installs and existing systems
- **Hardware optimizations**: NVIDIA GPU support, gaming optimizations

## Quick Start

### Fresh Installation (New Systems)

For completely new systems, follow these steps:

1. **Install standard Bazzite first**:
   - Download from [bazzite.gg](https://bazzite.gg)
   - For desktop: Choose **Bazzite DX** variant (NVIDIA for desktop GPUs)
   - For handheld: Choose the base Bazzite Deck variant
   - Flash to USB and install normally

2. **Switch to custom variant** (after first boot):
   ```bash
   # Auto-detect and rebase (recommended)
   curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/fresh-install.sh | bash
   ```

3. **Complete setup** (after reboot):
   ```bash
   # Install apps and configure system (auto-detects desktop/handheld)
   curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash
   ```

### For Existing Bazzite Systems
Rebase to the custom variant:

```bash
# For ROG Ally X (handheld)
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:handheld

# For Desktop with NVIDIA (DX-based variant)
sudo rpm-ostree rebase ostree-unverified-registry:ghcr.io/superterran/bazzite:desktop

# Reboot to apply changes
sudo systemctl reboot
```

### Post-Rebase Setup
After rebasing and rebooting, run the setup script:

```bash
# Smart setup - automatically detects desktop vs handheld
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash
```

To force a specific target:

```bash
# Desktop-specific modules (runs common first)
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash -s -- desktop

# Handheld-specific modules (runs common first)
curl -sSL https://raw.githubusercontent.com/superterran/bazzite/main/setup.sh | bash -s -- handheld
```

**Common setup (all variants):**
- Install 1Password with SSH agent integration
- Install Warp Terminal
- Install Flatpak applications (Slack, Obsidian, GNOME Boxes, utilities)
- Configure shell environment

**Desktop-specific setup:**
- Configure OpenRGB with custom lighting profiles
- Set up Ollama AI with CUDA GPU acceleration
- Enable SSH services and agent forwarding
- Configure NFS exports for network sharing
- Apply system fixes (sleep/wake, display management)
- Set up VS Code tunnel for remote development

## Local Development

Build images locally using just commands:

```bash
# Build handheld variant (based on bazzite-deck-gnome)
just build-handheld

# Build desktop variant (based on bazzite-dx-nvidia-gnome)
just build-desktop

# Build both variants
just build-all
```

**Note:** The desktop variant inherits all DX features (VS Code, Docker, development tools) from the base image. The container build only adds repository configurations and GPG keys. All software installation happens via runtime setup scripts.

## Updating

Images are automatically built when changes are pushed to main. To update:

```bash
sudo rpm-ostree upgrade
sudo systemctl reboot
```
