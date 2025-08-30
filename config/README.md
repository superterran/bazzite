# Configuration Files

This directory contains configuration files that are copied into the container images during build.

## Repository Configuration (`yum.repos.d/`)

Custom YUM repository configurations for additional software packages:

- **`1password.repo`** - 1Password password manager
- **`warp.repo`** - Warp Terminal
- **`vscode.repo`** - Visual Studio Code

These repository files are copied to `/etc/yum.repos.d/` during the container build process, before running the shared customizations script.

## Adding New Repositories

To add a new repository:

1. Create a `.repo` file in `config/yum.repos.d/`
2. Import the GPG key in `shared-customizations.sh`
3. Add the package to the `rpm-ostree install` command

## Notes

- GPG keys are imported during the build process to validate package signatures
- Repository files are copied before running the customization script
- All repositories should be stable/production channels for reliable builds
