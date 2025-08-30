#!/bin/bash
# Shared customizations for both handheld and desktop variants

set -euo pipefail

echo "Installing shared software packages..."

# Add Microsoft repository for VS Code
# rpm --import https://packages.microsoft.com/keys/microsoft.asc
# echo -e "[code]\nname=Visual Studio Code\nbaseurl=https://packages.microsoft.com/yumrepos/vscode\nenabled=1\ngpgcheck=1\ngpgkey=https://packages.microsoft.com/keys/microsoft.asc" > /etc/yum.repos.d/vscode.repo

# Install packages via rpm-ostree
# rpm-ostree install \
#     code \
#     https://downloads.1password.com/linux/rpm/stable/x86_64/1password-latest.rpm

echo "Shared customizations complete."
