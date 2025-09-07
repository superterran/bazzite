#!/bin/bash
# Shared customizations for both handheld and desktop variants

set -euo pipefail

echo "Installing shared software packages..."

# Import GPG keys for the repositories we added
# Note: Repository files are copied in the Containerfile before this script runs
rpm --import https://packages.microsoft.com/keys/microsoft.asc


# Install RPM packages that should be layered
rpm-ostree install \
    docker-compose \
    gnome-boxes

echo "Shared customizations complete."
