# Multi-target Containerfile for custom Bazzite variants

# Handheld target (ROG Ally X)
FROM ghcr.io/ublue-os/bazzite-deck-gnome:latest AS handheld

# Copy repository configurations
COPY config/yum.repos.d/ /etc/yum.repos.d/

# No build-time customizations (runtime setup scripts handle installs)
RUN rpm-ostree cleanup -m && ostree container commit

# Desktop target (NVIDIA)
FROM ghcr.io/ublue-os/bazzite-deck-nvidia-gnome:latest AS desktop

# Copy repository configurations
COPY config/yum.repos.d/ /etc/yum.repos.d/

# No build-time customizations (runtime setup scripts handle installs)
RUN rpm-ostree cleanup -m && ostree container commit
