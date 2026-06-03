#!/bin/bash
# Apply quiet AIO radiator fan curve to the NCT6796D-S/NCT6799D-R Super I/O
# on this ASUS board (CPU_FAN header = pwm2). Pump (pwm7) is left alone.
#
# enable=5 = ASUS Smart Fan IV auto curve. We rewrite the 5 auto_points so the
# curve is gentler in the 50-75 C range where Zen 5 idle-boost spikes live.
# BIOS reprograms the SuperIO registers on power cycle, so this must run at
# every boot — see fan-curve.service.

set -euo pipefail

HWMON=""
for h in /sys/class/hwmon/hwmon*; do
    name=$(cat "$h/name" 2>/dev/null || true)
    case "$name" in
        nct67??) HWMON="$h"; break ;;
    esac
done

if [ -z "$HWMON" ]; then
    echo "fan-curve: nct6775-family hwmon not found (is the nct6775 module loaded?)" >&2
    exit 1
fi

echo "fan-curve: using $HWMON ($(cat "$HWMON/name"))"

# pwm2 = CPU_FAN header, AIO radiator fan, follows PECI CPU temp.
# Curve (temp C -> PWM /255):
#   30C -> 40  (16%)
#   50C -> 60  (24%)
#   70C -> 90  (35%)
#   85C -> 140 (55%)
#   95C -> 255 (100%)
write_point() {
    local pwm=$1 idx=$2 temp_c=$3 pwm_val=$4
    echo $((temp_c * 1000)) > "$HWMON/pwm${pwm}_auto_point${idx}_temp"
    echo "$pwm_val"          > "$HWMON/pwm${pwm}_auto_point${idx}_pwm"
}

write_point 2 1 30 40
write_point 2 2 50 60
write_point 2 3 70 90
write_point 2 4 85 140
write_point 2 5 95 255

echo "fan-curve: applied quiet curve to pwm2 (CPU_FAN / AIO radiator)"
