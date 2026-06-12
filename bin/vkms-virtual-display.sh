#!/usr/bin/env bash
# vkms-virtual-display.sh — load (or unload) the VKMS virtual display on demand.
#
# Phase 2 of the EDID/streaming work (Handoffs/2026-06-04-edid-force-headless-streaming.md).
# VKMS provides `card2-Virtual-1`: a real, KMS-capturable DRM connector that exists
# independent of the physical TV on HDMI-A-2 — so Sunshine can stream ultrawide / iPad
# aspect ratios the 16:9 TV EDID can't express.
#
# Why on-demand and not /etc/modules-load.d: a connected phantom display at boot can
# confuse the gamescope session pick (this box has a history of boot-display fragility),
# and vkms loads live with zero reboot. Commit it to boot only once vkms is the chosen
# path — then deploy config/modules-load.d/vkms.conf.
#
# IMPORTANT (kernel 6.17.7-ba29): this vkms build has NO configfs interface and ignores
# edid_override / edid_firmware — it reports a 0-byte EDID and generates a generic mode
# list (no 3440x1440 / 2388x1668). That's fine: vkms accepts ARBITRARY modes via atomic
# modeset, so the streaming resolution is driven by the COMPOSITOR, not the EDID. To put
# content on it + stream:
#   1. OUTPUT_CONNECTOR=Virtual-1 + SCREEN_WIDTH/HEIGHT=<target> in the gamescope env
#      (see bin/sunshine-stream-mode.sh — extend it to switch the connector, not just res).
#   2. Sunshine: capture=kms, output_name=Virtual-1  (~/.config/sunshine/sunshine.conf).
# Trade-off vs the all-NVIDIA DP-2 path: vkms is a software CRTC, so the pipeline is
# NVIDIA-render -> system RAM -> nvenc (functional, some copy overhead).

set -euo pipefail

case "${1:-load}" in
    load)
        if lsmod | grep -q '^vkms'; then
            echo "vkms already loaded."
        else
            echo "Loading vkms..."
            sudo modprobe vkms
            sleep 1
        fi
        conn=$(ls -d /sys/class/drm/card*-Virtual-1 2>/dev/null | head -1 || true)
        if [ -n "$conn" ]; then
            echo "Virtual connector: $(basename "$conn")  status=$(cat "$conn/status")"
            echo "Capturable by Sunshine via: capture=kms, output_name=Virtual-1"
        else
            echo "WARNING: vkms loaded but no Virtual-1 connector found." >&2
            exit 1
        fi
        ;;
    unload)
        sudo modprobe -r vkms && echo "vkms unloaded." || { echo "rmmod failed (in use?)" >&2; exit 1; }
        ;;
    status)
        if lsmod | grep -q '^vkms'; then
            conn=$(ls -d /sys/class/drm/card*-Virtual-1 2>/dev/null | head -1 || true)
            echo "vkms: loaded; connector $( [ -n "$conn" ] && basename "$conn" || echo none )"
        else
            echo "vkms: not loaded"
        fi
        ;;
    *)
        echo "Usage: $0 [load|unload|status]" >&2
        exit 1
        ;;
esac
