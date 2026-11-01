#!/usr/bin/bash
# Autonomous NCT6799 Smart Fan IV curves; installed from desktop IaC.
set -euo pipefail
HWMON=""
for h in /sys/class/hwmon/hwmon*; do
 if [[ "$(cat "$h/name")" == nct6799 ]]; then HWMON="$h"; break; fi
done
[[ -n "$HWMON" ]]
# Source8 = PECI/TSI Agent0 Calibration; NOT k10temp Tctl.
# It has read roughly10C below Tctl on this board. Full output by75C source.
for pwm in 2 7; do
 echo 1 > "$HWMON/pwm${pwm}_enable"
 echo 255 > "$HWMON/pwm${pwm}"
 echo 1 > "$HWMON/pwm${pwm}_mode"
 echo 8 > "$HWMON/pwm${pwm}_temp_sel"
 i=1
 for point in "30 64" "45 77" "60 153" "70 217" "75 255"; do
  read -r temp duty <<< "$point"
  echo "$((temp*1000))" > "$HWMON/pwm${pwm}_auto_point${i}_temp"
  echo "$duty" > "$HWMON/pwm${pwm}_auto_point${i}_pwm"
  i=$((i+1))
 done
 echo 5 > "$HWMON/pwm${pwm}_enable"
done
echo "Hardware Smart Fan IV active on CPU_FAN and CHA_FAN; Kraken pump remains USB controlled."
