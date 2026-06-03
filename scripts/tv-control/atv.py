#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyatv>=0.15"]
# ///
"""
Control the Living Room Apple TV via pyatv (Companion protocol).

Subcommands:
  pair         interactive pairing (Apple TV pops a PIN, you type it)
  sleep        put the Apple TV to sleep (releases CEC grip on TV input)
  wake         wake the Apple TV
  pause        pause whatever is playing (does not release CEC)
  play-pause   toggle play/pause
  state        print current state

Credentials persist at ~/.config/atv-control/companion.creds
"""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

import pyatv
from pyatv.const import Protocol, PowerState

HOST = "10.0.0.237"
IDENTIFIER = "3E:75:AA:71:AA:56"
CONFIG_DIR = Path.home() / ".config" / "atv-control"
CREDS_FILE = CONFIG_DIR / "companion.creds"


async def _scan_atv(loop, timeout: int = 4):
    atvs = await pyatv.scan(loop, identifier=IDENTIFIER, timeout=timeout)
    if not atvs:
        raise SystemExit(f"Apple TV {IDENTIFIER} not found on LAN")
    return atvs[0]


async def cmd_pair():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()
    atv = await _scan_atv(loop)
    pairing = await pyatv.pair(atv, Protocol.Companion, loop)
    await pairing.begin()
    print("Pairing started. Look at the Apple TV — it should show a 4-digit PIN.")
    pin = input("Enter the PIN: ").strip()
    pairing.pin(pin)
    await pairing.finish()
    if not pairing.has_paired:
        raise SystemExit("Pairing failed.")
    creds = pairing.service.credentials
    CREDS_FILE.write_text(creds)
    print(f"Paired. Credentials saved to {CREDS_FILE}")
    await pairing.close()


async def _connect(loop, scan_timeout: int = 4):
    if not CREDS_FILE.exists():
        raise SystemExit("Not paired — run: atv.py pair")
    atv = await _scan_atv(loop, timeout=scan_timeout)
    for svc in atv.services:
        if svc.protocol == Protocol.Companion:
            svc.credentials = CREDS_FILE.read_text().strip()
    return await pyatv.connect(atv, loop)


async def cmd_power(target: str):
    loop = asyncio.get_event_loop()
    conn = await _connect(loop)
    try:
        if target == "sleep":
            await conn.power.turn_off()
        elif target == "wake":
            await conn.power.turn_on()
        # Don't print state — power.turn_off returns immediately, state lags
    finally:
        conn.close()


async def cmd_media(action: str):
    loop = asyncio.get_event_loop()
    # Pause is fired from the orb listener — keep scan tight so the
    # whole call fits inside the listener's per-step budget.
    conn = await _connect(loop, scan_timeout=2)
    try:
        if action == "pause":
            await conn.remote_control.pause()
        elif action == "play-pause":
            await conn.remote_control.play_pause()
    finally:
        conn.close()


async def cmd_state():
    loop = asyncio.get_event_loop()
    conn = await _connect(loop)
    try:
        print(f"power_state: {conn.power.power_state.name}")
        print(f"device_info: {conn.device_info}")
    finally:
        conn.close()


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    sub = sys.argv[1]
    if sub == "pair":
        asyncio.run(cmd_pair())
    elif sub == "sleep":
        asyncio.run(cmd_power("sleep"))
    elif sub == "wake":
        asyncio.run(cmd_power("wake"))
    elif sub == "pause":
        asyncio.run(cmd_media("pause"))
    elif sub == "play-pause":
        asyncio.run(cmd_media("play-pause"))
    elif sub == "state":
        asyncio.run(cmd_state())
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
