# Multi-target Containerfile for custom Bazzite variants

# Handheld target (ROG Ally X)
FROM ghcr.io/ublue-os/bazzite-deck-gnome:latest AS handheld

# Copy and run shared customizations
COPY shared-customizations.sh /tmp/shared-customizations.sh
RUN chmod +x /tmp/shared-customizations.sh && \
    /tmp/shared-customizations.sh && \
    rm /tmp/shared-customizations.sh && \
    rpm-ostree cleanup -m && \
    ostree container commit

# Desktop target (NVIDIA)
FROM ghcr.io/ublue-os/bazzite-deck-nvidia-gnome:latest AS desktop

# Copy and run shared customizations  
COPY shared-customizations.sh /tmp/shared-customizations.sh
RUN chmod +x /tmp/shared-customizations.sh && \
    /tmp/shared-customizations.sh && \
    rm /tmp/shared-customizations.sh && \
    rpm-ostree cleanup -m && \
    ostree container commit
