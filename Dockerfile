# Multi-target Dockerfile for custom Bazzite variants

# Handheld target (ROG Ally X)
FROM ghcr.io/ublue-os/bazzite-deck-gnome:latest AS handheld

# Copy repository configurations
COPY config/yum.repos.d/ /etc/yum.repos.d/

# Import GPG keys for third-party repositories
RUN rpm --import https://releases.warp.dev/linux/keys/warp.asc && \
    rpm --import https://downloads.1password.com/linux/keys/1password.asc

RUN ostree container commit

# Desktop target (NVIDIA)
FROM ghcr.io/ublue-os/bazzite-dx-nvidia-gnome:latest AS desktop

# Copy repository configurations
COPY config/yum.repos.d/ /etc/yum.repos.d/

# Import GPG keys for third-party repositories
RUN rpm --import https://packages.microsoft.com/keys/microsoft.asc && \
    rpm --import https://releases.warp.dev/linux/keys/warp.asc && \
    rpm --import https://downloads.1password.com/linux/keys/1password.asc

RUN ostree container commit
