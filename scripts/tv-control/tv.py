#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["androidtvremote2>=0.1.2"]
# ///
"""
Control the Livingroom TCL Google TV via the Android TV Remote v2 protocol.

Subcommands:
  pair                              one-time pairing (TV shows a PIN, you type it)
  on                                wake the TV
  off                               standby the TV
  input <HDMI_1|HDMI_2|...>         switch input
  switch-to-pc                      wake + switch to PC HDMI input (default for orb button)
  key <KEYNAME>                     send any androidtvremote2 key (see lib docs)

Cert/key persists at ~/.config/tv-control/ — created on first pair.
"""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

from androidtvremote2 import AndroidTVRemote, CannotConnect, ConnectionClosed, InvalidAuth

TV_HOST = "10.0.0.7"
TV_NAME = "Livingroom TV"
CLIENT_NAME = "bazzite-desktop"

# Which HDMI port the PC is plugged into on the TV.
# Override with env var TV_PC_INPUT (e.g. "HDMI_2") if HDMI_1 turns out wrong.
PC_INPUT = os.environ.get("TV_PC_INPUT", "HDMI_1")

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "tv-control"
CERT = CONFIG_DIR / "cert.pem"
KEY = CONFIG_DIR / "key.pem"


def _remote() -> AndroidTVRemote:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return AndroidTVRemote(CLIENT_NAME, str(CERT), str(KEY), TV_HOST)


async def cmd_pair() -> int:
    r = _remote()
    if await r.async_generate_cert_if_missing():
        print(f"Generated new cert at {CERT}")
    name = await r.async_start_pairing()
    print(f"Pairing started with: {name}")
    pin = input("Enter the 6-digit PIN shown on the TV: ").strip()
    await r.async_finish_pairing(pin)
    print("Paired.")
    return 0


async def _connected_remote() -> AndroidTVRemote:
    r = _remote()
    if not CERT.exists():
        raise SystemExit("Not paired yet — run: tv.py pair")
    await r.async_connect()
    r.keep_reconnecting()
    return r


async def cmd_power(target: str) -> int:
    r = await _connected_remote()
    is_on = bool(r.is_on)
    if (target == "on" and not is_on) or (target == "off" and is_on):
        r.send_key_command("POWER")
    r.disconnect()
    return 0


async def cmd_input(name: str) -> int:
    key = name.upper()
    if not key.startswith("TV_INPUT_") and key.startswith("HDMI"):
        key = f"TV_INPUT_{key}"
    r = await _connected_remote()
    r.send_key_command(key)
    r.disconnect()
    return 0


async def cmd_switch_to_pc() -> int:
    r = await _connected_remote()
    if not r.is_on:
        r.send_key_command("POWER")
        await asyncio.sleep(2.5)  # let the panel come up before sending input switch
    key = PC_INPUT.upper()
    if not key.startswith("TV_INPUT_"):
        key = f"TV_INPUT_{key}"
    r.send_key_command(key)
    r.disconnect()
    return 0


async def cmd_key(name: str) -> int:
    r = await _connected_remote()
    r.send_key_command(name.upper())
    r.disconnect()
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    sub = sys.argv[1]
    try:
        if sub == "pair":
            return asyncio.run(cmd_pair())
        if sub == "on":
            return asyncio.run(cmd_power("on"))
        if sub == "off":
            return asyncio.run(cmd_power("off"))
        if sub == "input" and len(sys.argv) >= 3:
            return asyncio.run(cmd_input(sys.argv[2]))
        if sub == "switch-to-pc":
            return asyncio.run(cmd_switch_to_pc())
        if sub == "key" and len(sys.argv) >= 3:
            return asyncio.run(cmd_key(sys.argv[2]))
        print(__doc__)
        return 2
    except (CannotConnect, ConnectionClosed) as e:
        print(f"TV unreachable: {e}", file=sys.stderr)
        return 1
    except InvalidAuth as e:
        print(f"Auth failed (re-pair?): {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
