#!/bin/bash
set -euo pipefail

# Syncthing on the handheld (ROG Ally) keeps game saves, configs, and shared
# folders in sync with the desktop over LAN.
# The common.d/syncthing.sh handles installation and service creation.
# This script handles handheld-specific shared folder setup.

echo "Configuring Syncthing for handheld..."

# Syncthing should already be installed and running via common.d/syncthing.sh
if ! systemctl --user is-active syncthing.service >/dev/null 2>&1; then
    echo "WARNING: Syncthing service not running. Run common.d/syncthing.sh first."
    exit 0
fi

echo "Syncthing is running on handheld."
echo ""
echo "Configure shared folders via the web UI: http://localhost:8384"
echo "Connect to desktop device to sync game saves and configurations."
echo ""
echo "Handheld Syncthing setup completed"
