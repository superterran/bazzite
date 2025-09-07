#!/bin/bash
# Verify Warp Terminal installation
#
# NOTE: Warp Terminal must be installed at runtime (not container build)
# Despite having a simple postinstall script (desktop DB update + repo setup),
# it still fails during container build transaction phase (reason under investigation)
# Current approach: Runtime installation via rpm-ostree

set -euo pipefail

echo "Checking Warp Terminal installation..."

# Check if Warp Terminal is installed (should be from container build)
if rpm -q warp-terminal &>/dev/null; then
    echo "✓ Warp Terminal is installed and ready"
else
    echo "Warning: Warp Terminal not found. This usually means you need to reboot after the container update."
    echo "Warp Terminal is installed during container build - reboot required for availability."
fi

echo "Warp Terminal check completed"
