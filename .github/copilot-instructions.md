# Bazzite Custom OS Build Repository

This repository builds custom Bazzite OS variants (desktop and handheld) using container-based immutable Linux distribution techniques. Bazzite is based on Universal Blue and uses rpm-ostree for system management.

## Project Structure and Conventions

### Architecture Overview
- **Base OS**: Universal Blue Bazzite (Fedora-based immutable OS)
- **Build System**: Multi-stage Dockerfile with Just automation
- **Variants**: Desktop (NVIDIA-optimized) and Handheld (ROG Ally X-optimized)
- **Deployment**: rpm-ostree rebase to container images hosted on GitHub Container Registry
- **Customization**: Modular bash scripts executed post-installation

### Directory Structure
```
common.d/        # Scripts run on all system types
desktop.d/       # Desktop-specific scripts (OpenRGB, SSH, development tools)
handheld.d/      # Handheld-specific scripts (future use)
config/          # Configuration files and templates
├── openrgb/     # RGB lighting profiles
├── systemd/     # Systemd service files
└── yum.repos.d/ # Third-party repository configurations
bin/             # Utility scripts
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
- **Minimal container builds**: Only add repository configs and core packages with simple postinstall scripts
- **Runtime customization**: Use modular setup scripts for complex installations requiring user session context
- **Package hierarchy**: RPMs in container build > Flatpaks > Homebrew > rpm-ostree install (requires reboot)

### Key Technologies and Tools
- **Container Runtime**: Podman with Docker CLI compatibility
- **Package Managers**: rpm-ostree (system), Flatpak (user apps), RPM (container builds)
- **Build Automation**: Just (justfile) for command automation
- **Hardware Support**: NVIDIA GPUs (desktop), OpenRGB for RGB devices, ROG Ally X (handheld)
- **Development**: VS Code with remote development, SSH tunneling, container development

### Common Commands and Workflows

#### Building and Testing
```bash
# Build variants
just build-desktop
just build-handheld
just build-all

# Interactive testing
just run-desktop
just run-handheld

# Package verification
just test-desktop-packages
just test-handheld-packages

# Local deployment testing
just rebase-desktop-local
just rebase-handheld-local
```

#### Setup and Configuration
```bash
# Run modular setup (auto-detects system type)
./setup.sh
just setup

# Force specific target
./setup.sh desktop
./setup.sh handheld
just desktop-setup

# Backup current configuration
just backup-config
```

### Development Patterns

#### Adding New Software
1. **Determine installation method**:
   - RPM packages with simple postinstall → Add to Dockerfile
   - Complex packages requiring user session → Create runtime setup script
   - User applications → Prefer Flatpak installation in setup scripts

2. **Create modular script**:
   - Place in appropriate directory (common.d/, desktop.d/, handheld.d/)
   - Use numeric prefix for execution order
   - Follow idempotent pattern with existence checks
   - Include progress logging and error handling

3. **Testing workflow**:
   - Test script individually: `./desktop.d/XX-feature-name.sh`
   - Test via orchestrator: `./setup.sh desktop`
   - Test container build: `just build-desktop`
   - Test on actual hardware: `just rebase-desktop-local`

#### Configuration Management
- Add configuration files to appropriate `config/` subdirectory
- Create corresponding setup script to deploy configuration
- Handle both initial setup and configuration updates
- Consider hardware-specific requirements (desktop vs handheld)

### Error Handling Philosophy
- Scripts should be safe to re-run (idempotent design)
- Individual script failures don't stop overall setup process
- Provide clear progress indication and error reporting
- Graceful degradation when optional features fail
- Use `set -euo pipefail` for strict error handling in individual scripts

### Hardware-Specific Considerations
- **Desktop**: NVIDIA drivers, OpenRGB support, multi-monitor setups, development environment
- **Handheld**: Gaming optimizations, power management, portable form factor considerations
- **Auto-detection**: System type detected via DMI information in `setup.sh`

### AI Assistant Guidelines
When suggesting code changes or new features:
- Follow the modular script pattern with numeric prefixes
- Consider the container vs runtime installation decision
- Use existing script templates as reference for style and error handling
- Account for hardware-specific requirements (desktop vs handheld)
- Make scripts idempotent and include progress feedback
- Update relevant README.md files when adding new functionality
- Respect the execution order system and existing conventions
