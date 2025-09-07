# Multi-target Containerfile for custom Bazzite variants

# Handheld target (ROG Ally X)
FROM ghcr.io/ublue-os/bazzite-deck-gnome:latest AS handheld

# Copy repository configurations
COPY config/yum.repos.d/ /etc/yum.repos.d/

# Import GPG keys for third-party repositories
RUN rpm --import https://packages.microsoft.com/keys/microsoft.asc && \
    rpm --import https://releases.warp.dev/linux/keys/warp.asc && \
    rpm --import https://downloads.1password.com/linux/keys/1password.asc

# Install packages that work well in container builds
# These packages have simple postinstall scripts with no user-session dependencies:
# - code: VS Code for development with full host access (needed for devcontainers)
# - podman-docker: Docker CLI compatibility for VS Code devcontainer support
# 
# NOTE: Packages with complex user-session requirements (like 1Password GUI)
# are installed via setup scripts at runtime when user context is available
RUN rpm-ostree install \
    code \
    podman-docker && \
    rpm-ostree cleanup -m && \
    ostree container commit

# Desktop target (NVIDIA)
FROM ghcr.io/ublue-os/bazzite-deck-nvidia-gnome:latest AS desktop

# Copy repository configurations
COPY config/yum.repos.d/ /etc/yum.repos.d/

# Import GPG keys for third-party repositories
RUN rpm --import https://packages.microsoft.com/keys/microsoft.asc && \
    rpm --import https://releases.warp.dev/linux/keys/warp.asc && \
    rpm --import https://downloads.1password.com/linux/keys/1password.asc

# Install packages that work well in container builds
# These packages have simple postinstall scripts with no user-session dependencies:
# - code: VS Code for development with full host access (needed for devcontainers)
# - podman-docker: Docker CLI compatibility for VS Code devcontainer support
# 
# NOTE: Packages with complex user-session requirements (like 1Password GUI)
# are installed via setup scripts at runtime when user context is available
RUN rpm-ostree install \
    code \
    podman-docker && \
    rpm-ostree cleanup -m && \
    ostree container commit
