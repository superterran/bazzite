#!/usr/bin/python3
"""Install the reviewed GNOME50 bottom-edge extension in encrypted GNOME."""
import hashlib
import io
import json
import os
from pathlib import Path
import urllib.request
import zipfile
from gi.repository import Gio

home = Path.home()
if home != Path('/var/home/desktop-secure') or not os.path.ismount(home):
    raise SystemExit('Run as desktop-secure while its encrypted home is unlocked.')
uuid = 'bottom-overview@fthx'
data = urllib.request.urlopen('https://extensions.gnome.org/download-extension/bottom-overview@fthx.shell-extension.zip?version_tag=77092', timeout=30).read()
if hashlib.sha256(data).hexdigest() != '1fc42c73e727adcb94eb4d4046071215c350e8f82779a067e94d3fd29a9fffa5':
    raise SystemExit('Extension checksum changed; review before updating.')
destination = home / '.local/share/gnome-shell/extensions' / uuid
with zipfile.ZipFile(io.BytesIO(data)) as archive:
    metadata = json.loads(archive.read('metadata.json'))
    if metadata['uuid'] != uuid or '50' not in metadata['shell-version']:
        raise SystemExit('Extension metadata does not match this GNOME version.')
    for member in archive.infolist():
        if not (destination / member.filename).resolve().is_relative_to(destination.resolve()):
            raise SystemExit('Unsafe extension archive path')
        if (member.external_attr >> 16) & 0o170000 == 0o120000:
            raise SystemExit('Extension symlinks are not allowed')
    destination.mkdir(parents=True, exist_ok=True)
    archive.extractall(destination)
settings = Gio.Settings.new('org.gnome.shell')
enabled = settings.get_strv('enabled-extensions')
if uuid not in enabled:
    settings.set_strv('enabled-extensions', enabled + [uuid])
Gio.Settings.sync()
print('Bottom Overview19 installed and enabled for the next GNOME session.')
