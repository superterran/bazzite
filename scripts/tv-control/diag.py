#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["androidtvremote2>=0.1.2"]
# ///
import asyncio, sys
from pathlib import Path
from androidtvremote2 import AndroidTVRemote

TV_HOST = "10.0.0.7"
CONFIG = Path.home() / ".config" / "tv-control"


async def main(action: str):
    r = AndroidTVRemote("bazzite-desktop", str(CONFIG / "cert.pem"), str(CONFIG / "key.pem"), TV_HOST)
    await r.async_connect()
    r.keep_reconnecting()

    print(f"is_on:        {r.is_on}")
    print(f"current_app:  {r.current_app}")
    print(f"device_info:  {r.device_info}")
    print(f"volume_info:  {r.volume_info}")
    print(f"app installed:{getattr(r, 'app_installed', '?')}")

    if action != "info":
        print(f"sending key:  {action}")
        r.send_key_command(action.upper())
        await asyncio.sleep(1.5)  # let the network buffer actually flush
        print("post-send state:")
        print(f"  is_on:       {r.is_on}")
        print(f"  current_app: {r.current_app}")

    r.disconnect()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "info"))
