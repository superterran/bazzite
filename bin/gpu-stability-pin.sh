#!/usr/bin/env bash
# gpu-stability-pin.sh — pin the RTX 4070 off its ragged boost edge to test/avoid
# Xid 109 "CTX SWITCH TIMEOUT" -> Forza "Video Card Crash FHC00".
#
# Context (2026-06-19): Forza Horizon 6 crashed twice with Xid 109 during LOCAL
# SDR play. Ruled out: the GPU AI stack (off for crash #2), Sunshine/NVENC (idle,
# no Moonlight client connected during either crash), and HDR (session already SDR).
# Remaining suspect: unstable GPU boost — this is a factory-OC card that boosts to
# 3105 MHz (reference ~2475). Capping the boost is the classic Xid-109 stability fix.
#
# Privileged (nvidia-smi -pm/-lgc need root). Non-persistent across reboot by design.
#   gpu-stability-pin.sh on   # cap boost @ 2550 MHz (stability test)
#   gpu-stability-pin.sh off  # restore default boost (up to 3105 MHz)
#   gpu-stability-pin.sh status
set -euo pipefail

CAP="${GPU_CLOCK_CAP:-2550}"   # MHz; dial up later to find the stable ceiling
FLOOR=510                      # keep a sane floor, well above deep-idle 210 MHz

case "${1:-status}" in
  on)
    sudo nvidia-smi -pm 1 >/dev/null
    sudo nvidia-smi -lgc "${FLOOR},${CAP}" >/dev/null
    echo "GPU graphics clock locked ${FLOOR}-${CAP} MHz (boost capped for stability)"
    ;;
  off)
    sudo nvidia-smi -rgc >/dev/null
    echo "GPU clock lock reset — default boost restored (up to 3105 MHz)"
    ;;
  status) ;;
  *) echo "usage: $0 {on|off|status}" >&2; exit 1 ;;
esac

nvidia-smi --query-gpu=clocks.gr,clocks.max.gr --format=csv,noheader
