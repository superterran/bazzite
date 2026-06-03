#!/bin/bash
# Switch the Livingroom TCL Google TV to a specific HDMI input via TIF intent.
# androidtvremote2 KEYCODE_TV_INPUT_HDMI_* are stubbed by TCL; only the TIF
# passthrough URI works. ADB Network Debugging must be enabled on the TV.
#
# Usage:  tv-switch.sh hdmi1 | hdmi2 | hdmi3 | hdmi4
# Env:    TV_HOST (default 10.0.0.7)
set -euo pipefail

TV_HOST="${TV_HOST:-10.0.0.7}"
ADB_PORT="${ADB_PORT:-5555}"
ADB_TARGET="${TV_HOST}:${ADB_PORT}"

# TIF inputId map — captured 2026-05-31 from `dumpsys tv_input` on this TV.
# HW IDs are derived from stable hardware device IDs and persist across reboots.
declare -A INPUTS=(
    [hdmi1]="com.tcl.tvinput/.passthroughinput.TvPassThroughService/HW1413744128"
    [hdmi2]="com.tcl.tvinput/.passthroughinput.TvPassThroughService/HW1413744384"
    [hdmi3]="com.tcl.tvinput/.passthroughinput.TvPassThroughService/HW1413744640"
    [hdmi4]="com.tcl.tvinput/.passthroughinput.TvPassThroughService/HW1413745664"
)

target="${1:-}"
target="${target,,}"
if [[ -z "${INPUTS[$target]:-}" ]]; then
    echo "Usage: $0 {hdmi1|hdmi2|hdmi3|hdmi4}" >&2
    exit 2
fi

input_id="${INPUTS[$target]}"
# URL-encode the slashes in the input id (only / -> %2F is needed)
input_id_enc="${input_id//\//%2F}"
uri="content://android.media.tv/passthrough/${input_id_enc}"

# Re-attach ADB if needed (TV may have dropped after sleep).
if ! adb devices | grep -q "^${ADB_TARGET}[[:space:]]*device"; then
    adb connect "${ADB_TARGET}" >/dev/null
fi

exec adb -s "${ADB_TARGET}" shell am start -a android.intent.action.VIEW -d "${uri}"
