#!/bin/bash
# Cure (and instrument) the idle hard-freeze on bazzite-desktop.
#
# Symptom: every few hours / overnight the box hard-locks — unresponsive to SSH,
# no video, COOL to the touch. Netdata + journald black-box (2026-06-06) showed it
# froze at ~0% CPU / 53 °C with NO panic, NO MCE, NO thermal event, NO suspend
# attempt, then sat dead 8h until a hard reset. That signature — cold, idle,
# log-less, no panic — is the classic AMD Zen idle C-state hang (9950X on a
# ROG STRIX B850-I, BIOS 1078 / Jul-2025, deep C3 enabled).
#
# Earlier fixes (fan curve, s2idle suspend, EDID kargs) were treating the wrong
# cause. This script does three things:
#   1. Arms the SP5100 hardware watchdog so a hard hang auto-reboots (~1 min)
#      instead of leaving the box dead — works regardless of root cause.
#   2. Turns soft lockups into capturable panics so the next hang isn't silent.
#   3. Limits CPU idle to C1 (processor.max_cstate=1), the known mitigation for
#      the idle hang — applied live now AND as a durable kernel karg.
#
# Real cure is a BIOS/AGESA update + "Power Supply Idle Control = Typical Current
# Idle"; until then max_cstate=1 is the bridge. Diagnosed 2026-06-06.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

install_dropin() {
    local src="$1" dst="$2"
    sudo mkdir -p "$(dirname "$dst")"
    if ! sudo cmp -s "$src" "$dst" 2>/dev/null; then
        sudo install -m 0644 "$src" "$dst"
        echo "✓ Installed $dst"
        return 0
    fi
    echo "✓ $dst already current"
    return 1
}

echo "1/3 Hardware watchdog (auto-reboot on hard hang)..."
if install_dropin "$REPO_ROOT/config/system.conf.d/10-watchdog.conf" \
                  /etc/systemd/system.conf.d/10-watchdog.conf; then
    sudo systemctl daemon-reexec
fi

echo "2/3 Hang capture (soft lockup -> panic -> auto-reboot + log)..."
if install_dropin "$REPO_ROOT/config/sysctl.d/99-hang-capture.conf" \
                  /etc/sysctl.d/99-hang-capture.conf; then
    sudo sysctl --system >/dev/null
fi

echo "3/3 C-state mitigation (limit idle to C1)..."
# Durable: kernel karg (takes effect on next boot, survives image updates).
if ! rpm-ostree kargs 2>/dev/null | grep -q 'processor.max_cstate=1'; then
    sudo rpm-ostree kargs --append-if-missing=processor.max_cstate=1
    echo "✓ Queued karg processor.max_cstate=1 (reboot to activate)"
else
    echo "✓ karg processor.max_cstate=1 already present"
fi
# Live: disable the deep ACPI C-states now so we don't have to wait for a reboot.
# State indices on this box: 0=POLL 1=C1 2=C2 3=C3 — disable 2 and 3 == max_cstate=1.
for st in 2 3; do
    for f in /sys/devices/system/cpu/cpu*/cpuidle/state$st/disable; do
        echo 1 | sudo tee "$f" >/dev/null
    done
done
echo "✓ Disabled C2/C3 live on all CPUs"

echo ""
echo "Verify:"
echo "  watchdog : $(systemctl show -p RuntimeWatchdogUSec --value) on $(systemctl show -p WatchdogDevice --value)"
echo "  panic    : softlockup_panic=$(cat /proc/sys/kernel/softlockup_panic) panic=$(cat /proc/sys/kernel/panic)"
echo "  cpu0 idle: $(for s in /sys/devices/system/cpu/cpu0/cpuidle/state*/; do echo -n "$(cat "$s"/name):$(cat "$s"/disable) "; done)"
echo ""
echo "✅ Stability fixes applied. Deep C-states disabled live; karg makes it durable on next reboot."
echo "   Next real cure: update B850-I BIOS (1078 is ~11mo old) + set Power Supply Idle = Typical Current Idle."
