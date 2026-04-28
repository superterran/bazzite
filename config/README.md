# Configuration Files

This directory contains configuration files and templates deployed during setup.

## Repository Configuration (`yum.repos.d/`)

Custom YUM repository configurations for additional software packages:

- **`1password.repo`** - 1Password password manager

These repository files are copied to `/etc/yum.repos.d/` during the container build process.

## OpenRGB Configuration (`openrgb/`)

RGB lighting configuration for desktop systems:

- **`Ideal.orp`** - OpenRGB profile that turns off all RGB lighting
- **`OpenRGB.json`** - OpenRGB application configuration

Deployed via `desktop.d/openrgb.sh` to `~/.config/OpenRGB/`.

## OpenCode Configuration (`opencode/`)

AI coding web UI configuration:

- **`opencode.json`** - OpenCode config with Ollama providers and MCP server definitions

Deployed via `desktop.d/opencode.sh` to `~/.config/opencode/`.

## LiteLLM Configuration (`litellm/`)

AI routing proxy configuration:

- **`config.yaml`** - Cost-tiered model routing (nano/fast/mid/smart/max/apex) via Poe, OpenAI, Anthropic, and local Ollama

Deployed via `desktop.d/litellm.sh` to `~/.config/litellm/`. API keys are stored in a separate `proxy.env` file (not in repo).

## Cloudflare Tunnel (`cloudflared/`)

- **`config.yml.example`** - Template for Cloudflare Tunnel config (replace TUNNEL_ID)

Copy to `~/.cloudflared/config.yml` after creating a tunnel. See `desktop.d/cloudflared.sh`.

## Systemd User Services (`systemd/user/`)

User-level systemd service file templates:

- **`openrgb.service`** - Auto-start OpenRGB with Ideal profile on login
- **`syncthing.service`** - Continuous file synchronization
- **`opencode-web.service`** - OpenCode Web UI on port 3333
- **`cloudflared.service`** - Cloudflare Tunnel
- **`litellm-proxy.service`** - LiteLLM AI routing proxy on port 4000

Setup scripts deploy these to `~/.config/systemd/user/`.

## Adding New Repositories

1. Create a `.repo` file in `config/yum.repos.d/`
2. Add the GPG key import to the Dockerfile
3. Add the package installation to the appropriate setup script

## Notes

- GPG keys are imported during the build process to validate package signatures
- Config templates contain no secrets — API keys use environment files
- All repositories should be stable/production channels for reliable builds
