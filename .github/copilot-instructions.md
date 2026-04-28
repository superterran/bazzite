# Bazzite Custom OS Build Repository

This repository builds custom Bazzite OS variants (desktop and handheld) using container-based immutable Linux distribution techniques. Bazzite is based on Universal Blue and uses rpm-ostree for system management.

## Project Structure and Conventions

### Architecture Overview
- **Base OS**: Universal Blue Bazzite (Fedora-based immutable OS)
- **Build System**: Multi-stage Dockerfile with Just automation
- **Variants**: Desktop (NVIDIA-optimized) and Handheld (ROG Ally X)
- **Deployment**: rpm-ostree rebase to container images hosted on GitHub Container Registry
- **Customization**: Modular bash scripts executed post-installation

### Directory Structure
```
common.d/        # Scripts run on all system types (1Password, Syncthing, Claude CLI, Flatpaks)
desktop.d/       # Desktop-specific scripts (OpenCode, LiteLLM, Cloudflare, Ollama, SSH, OpenRGB, MCP)
handheld.d/      # Handheld-specific scripts (ROG Ally X Syncthing config)
config/          # Configuration files and templates
├── cloudflared/ # Cloudflare Tunnel config template
├── litellm/     # LiteLLM proxy config (cost-tiered AI routing)
├── opencode/    # OpenCode config (Ollama providers + MCP servers)
├── openrgb/     # RGB lighting profiles
├── systemd/user/# Systemd service unit templates
└── yum.repos.d/ # Third-party repository configurations (1Password)
bin/             # Utility scripts (display switching, session toggling)
.github/         # CI/CD workflows
```

### Script Naming and Execution Order
Scripts use numeric prefixes to control execution order:
- `01-*`: System package installations (RPM packages)
- `10-*`: Early user configuration
- `20-*`: Application-specific configurations
- `90-*`: Final setup tasks
- `100-*`: System-level fixes and optimizations

### Code Style Guidelines

#### Shell Scripts
- Always use `#!/bin/bash` shebang
- Include `set -euo pipefail` for error handling
- Use descriptive variable names in UPPER_CASE for constants
- Make scripts idempotent (check existing state before making changes)
- Include echo statements for progress indication
- Follow this template pattern:

```bash
#!/bin/bash
set -euo pipefail

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

#### Container Build Philosophy
- **Minimal container builds**: Only add repository configs and GPG keys
- **Runtime customization**: Use modular setup scripts for complex installations requiring user session context
- **Package hierarchy**: RPMs in container build > Flatpaks > Homebrew > rpm-ostree install (requires reboot)

### Key Technologies and Tools
- **Container Runtime**: Podman with Docker CLI compatibility
- **Package Managers**: rpm-ostree (system), Flatpak (user apps), Linuxbrew (CLI tools)
- **Build Automation**: Just (justfile) for command automation
- **AI Tools**: OpenCode (web UI), Claude CLI, LiteLLM (routing proxy), Ollama (local models)
- **MCP Servers**: mcpvault, basic-memory, phpstan, context7, playwright, commerce-extensibility
- **File Sync**: Syncthing (desktop ↔ ROG Ally)
- **Tunneling**: Cloudflare Tunnel (opencode.superterran.net)
- **Security**: 1Password with SSH agent integration
- **Hardware Support**: NVIDIA GPUs (desktop), OpenRGB, ROG Ally X (handheld)

### Common Commands and Workflows

#### Building and Testing
```bash
just build-desktop
just build-handheld
just build-all
just run-desktop
just run-handheld
just test-desktop-packages
just test-handheld-packages
just rebase-desktop-local
just rebase-handheld-local
```

#### Setup and Configuration
```bash
./setup.sh              # Auto-detect and setup
just setup              # Same via just
just desktop-setup      # Desktop only
just handheld-setup     # Handheld only
just setup-ally         # Run setup on ROG Ally via SSH
just backup-config      # Backup current configuration
```

### Development Patterns

#### Adding New Software
1. **Determine installation method**:
   - RPM packages with simple postinstall → Add to Dockerfile
   - Complex packages requiring user session → Create runtime setup script
   - User applications → Prefer Flatpak installation in setup scripts
   - CLI tools → Prefer Linuxbrew (avoids rpm-ostree layering and reboots)

2. **Create modular script** in appropriate directory (common.d/, desktop.d/, handheld.d/)

3. **Add config templates** to `config/` if the tool needs configuration files

4. **Add systemd units** to `config/systemd/user/` if the tool runs as a persistent service

#### Configuration Management
- Config templates live in `config/` subdirectories
- Setup scripts deploy configs to `~/.config/` on the target machine
- Secrets (API keys) use environment files (e.g., `proxy.env`) not committed to git
- Cloudflare Tunnel credentials are per-machine (not in repo)

### Error Handling Philosophy
- Scripts should be safe to re-run (idempotent design)
- Individual script failures don't stop overall setup process
- Graceful degradation when optional features fail
- Use `set -euo pipefail` for strict error handling in individual scripts

### AI Assistant Guidelines
When suggesting code changes or new features:
- Follow the modular script pattern
- Consider the container vs runtime installation decision
- Use existing script templates as reference for style
- Account for hardware-specific requirements (desktop vs handheld)
- Make scripts idempotent and include progress feedback
- Config templates go in `config/`, not inline in scripts
- Systemd units go in `config/systemd/user/`
- Never commit secrets or API keys
