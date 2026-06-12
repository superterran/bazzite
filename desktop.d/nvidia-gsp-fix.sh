#!/bin/bash
# Disable the NVIDIA GSP firmware to cure the remaining hard-lock on bazzite-desktop.
#
# Saga recap: the recurring hard-locks were chased through thermal, s2idle suspend,
# forced-EDID kargs, RAM timing, and an AMD Zen idle C-state theory. As of
# 2026-06-07 the surviving suspects had been narrowed down hard:
#   - Memory ruled out: EXPO off (running 4400 MT/s), stress-ng clean x3, ZERO
#     EDAC/MCE errors — still froze.
#   - Idle C-state theory WEAKENED: the 2026-06-07 12:32 freeze happened with
#     processor.max_cstate=1 confirmed active in the crashed boot's cmdline, AND
#     it hit under light-active load (incoming SSH / ob sync / netdata), not cold
#     idle. max_cstate=1 did not prevent it.
#   - That freeze's signature (active load, ~1-2 hr cadence, log-less hard hang,
#     no panic/MCE, only the SP5100 TCO watchdog recovered it in ~2 min) matches
#     the 2026-06-05 NVIDIA GSP-hang theory better than the idle theory.
#
# The 2026-06-05 "fix" rebased the driver to nvidia 610.43.02 but never actually
# disabled GSP — `GPU Firmware: 610.43.02` was still loaded. This script disables
# the GSP firmware path entirely, the canonical workaround for GSP-induced hard
# hangs, independent of driver version.
#
# Mechanism: nvidia loads early via nvidia-drm.modeset=1, so a /etc/modprobe.d
# drop wouldn't reliably reach it without an initramfs rebuild. On this ostree box
# the robust, image-update-surviving way to set a module param is a kernel karg:
# nvidia.NVreg_EnableGpuFirmware=0. Matches the existing processor.max_cstate=1
# karg pattern. REBOOT-ONLY — GSP can't be toggled live without unloading the
# nvidia module (which would kill the display). Diagnosed 2026-06-07.
#
# Reversal: sudo rpm-ostree kargs --delete-if-present=nvidia.NVreg_EnableGpuFirmware=0

set -euo pipefail

KARG='nvidia.NVreg_EnableGpuFirmware=0'

echo "Disabling NVIDIA GSP firmware via kernel karg..."
if ! rpm-ostree kargs 2>/dev/null | grep -q "$KARG"; then
    sudo rpm-ostree kargs --append-if-missing="$KARG"
    echo "✓ Queued karg $KARG (reboot to activate)"
else
    echo "✓ karg $KARG already present"
fi

echo ""
echo "Current GSP state (until reboot it stays loaded):"
echo "  driver   : $(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null || echo '?')"
echo "  firmware : $(cat /proc/driver/nvidia/gpus/*/information 2>/dev/null | grep -i firmware || echo 'n/a')"
echo ""
echo "After reboot, confirm GSP is OFF with:"
echo "  cat /proc/driver/nvidia/gpus/*/information | grep -i firmware   # expect: GPU Firmware: N/A (or no line)"
echo ""
echo "⚠  REBOOT REQUIRED to activate. The HW watchdog + max_cstate=1 stack stays in"
echo "   place as a safety net; if a hard-lock recurs AFTER this with GSP confirmed"
echo "   off, GSP is exonerated and the next lever is BIOS Power Supply Idle Control"
echo "   = Typical Current Idle (independent of the OS max_cstate karg)."
