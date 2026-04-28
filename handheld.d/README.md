# Handheld Setup Scripts (ROG Ally X)

Scripts in this directory run only on handheld systems (detected via DMI product name).

## Scripts

| Script | Purpose |
|--------|---------|
| `syncthing.sh` | Handheld-specific Syncthing configuration (shared folders with desktop) |

## Notes

- The ROG Ally X runs `bazzite-deck-gnome` as its base image
- Common scripts (`common.d/`) run first, providing 1Password, Syncthing, and Flatpak apps
- SSH access from desktop: `ssh ally` (configured in desktop's `~/.ssh/config`)
- Syncthing keeps game saves and configs in sync over LAN
