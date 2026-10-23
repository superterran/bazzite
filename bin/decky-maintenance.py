#!/usr/bin/python3
"""Daily stable Decky/plugin updates. Defer during games; verify and back up first."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
import zipfile
from datetime import datetime, timezone

BASE = Path('/home/me/homebrew')
STATE = Path('/var/lib/decky-maintenance')
STORE = 'https://plugins.deckbrew.xyz/plugins/versions'
CDN = 'https://cdn.tzatzikiweeb.moe/file/steam-deck-homebrew/versions/'


def fetch(url, version='v3.3.0'):
    req = urllib.request.Request(url, headers={'User-Agent': 'bazzite-decky-maintenance', 'X-Decky-Version': version})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def version_key(value):
    # Stable store versions only; never downgrade or select a preview build.
    match = re.fullmatch(r'v?(\d+)\.(\d+)\.(\d+)', value)
    return tuple(map(int, match.groups())) if match else None


def busy_reason():
    for p in Path('/proc').glob('[0-9]*'):
        try:
            env = p.joinpath('environ').read_bytes().split(b'\0')
            for item in env:
                if item.startswith((b'SteamAppId=', b'SteamGameId=')):
                    app = item.split(b'=', 1)[1]
                    if app not in (b'', b'0', b'769', b'413090', b'443510'):
                        return 'A Steam game/application is running'
        except (OSError, ProcessLookupError):
            continue
    if subprocess.run(['pgrep', '-x', 'gamescope'], capture_output=True).returncode == 0:
        result = subprocess.run(['runuser', '-u', 'me', '--', 'env', 'DISPLAY=:0', 'xprop', '-root', 'GAMESCOPE_FOCUSED_APP'], capture_output=True, text=True)
        match = re.search(r'=\s*(\d+)', result.stdout)
        if not match or match[1] not in ('0', '769'):
            return 'A game has focus, or Game Mode focus cannot be verified'
    return None


def extract_plugin(data, name, version, destination):
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for info in archive.infolist():
            target = (destination / info.filename).resolve()
            if not target.is_relative_to(destination.resolve()) or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Unsafe plugin archive member')
        archive.extractall(destination)
    matches = []
    for meta in destination.rglob('plugin.json'):
        package = meta.with_name('package.json')
        if package.exists() and json.loads(meta.read_text()).get('name') == name:
            if json.loads(package.read_text()).get('version') == version:
                matches.append(meta.parent)
    if len(matches) != 1:
        raise ValueError(f'Plugin metadata does not match {name} {version}')
    plugin = matches[0]
    for binary in json.loads((plugin / 'package.json').read_text()).get('remote_binary', []):
        filename = binary['name']
        if Path(filename).name != filename or filename in ('.', '..'):
            raise ValueError('Unsafe remote binary filename')
        content = fetch(binary['url'])
        if digest(content) != binary['sha256hash']:
            raise ValueError('Remote binary SHA-256 mismatch')
        (plugin / 'bin').mkdir(exist_ok=True)
        dest = plugin / 'bin' / filename
        dest.write_bytes(content)
        dest.chmod(0o755)
    return plugin


def plugin_permissions(target):
    flags = json.loads((target / 'plugin.json').read_text()).get('flags', [])
    owner = 'root' if 'root' in flags else 'me'
    for path in target.rglob('*'):
        shutil.chown(path, user=owner, group=owner)
    shutil.chown(target, user='root', group='root')
    shutil.chown(target / 'plugin.json', user='root', group='root')
    target.chmod(0o755)
    (target / 'plugin.json').chmod(0o755)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Check only; never install or restart')
    args = parser.parse_args()
    reason = busy_reason()
    if reason and not args.check:
        print('Deferred:', reason, flush=True)
        return
    release = json.loads(fetch('https://api.github.com/repos/SteamDeckHomebrew/decky-loader/releases/latest'))
    if release.get('prerelease') or not version_key(release['tag_name']):
        raise ValueError('Expected stable Decky release')
    latest = release['tag_name']
    versions = json.loads(fetch(STORE, latest))
    asset = next(a for a in release['assets'] if a['name'] == 'PluginLoader')
    expected = asset.get('digest', '').removeprefix('sha256:')
    if not re.fullmatch(r'[a-f0-9]{64}', expected):
        raise ValueError('Decky release has no SHA-256 digest')
    loader = BASE / 'services/PluginLoader'
    loader_update = digest(loader.read_bytes()) != expected
    jobs = []
    for meta in (BASE / 'plugins').glob('*/plugin.json'):
        name = json.loads(meta.read_text())['name']
        current = json.loads(meta.with_name('package.json').read_text())['version']
        remote = versions.get(name)
        if not remote and name == 'Bazzite Buddy':
            buddy = json.loads(fetch('https://api.github.com/repos/ublue-os/decky-bazzite-buddy/releases/latest'))
            if not buddy.get('prerelease') and version_key(buddy['tag_name']):
                bundle = next(a for a in buddy['assets'] if a['name'] == 'Bazzite.Buddy.zip')
                remote = [buddy['tag_name'].removeprefix('v'), bundle.get('digest', '').removeprefix('sha256:'), bundle['browser_download_url']]
                receipt = STATE / 'buddy-artifact.sha256'
                if receipt.exists() and receipt.read_text().strip() == remote[1]:
                    # Upstream v1.3.0 zip still reports 1.2.0 in package.json.
                    # A verified installed-artifact receipt avoids reinstall loops.
                    current = remote[0]
        if not remote:
            print(f'{name}: not in stable store; left unchanged', flush=True)
            continue
        old_key, new_key = version_key(current), version_key(remote[0])
        if old_key and new_key and new_key > old_key:
            jobs.append((meta.parent, name, current, remote))
    print(json.dumps({'stable_loader': latest, 'loader_update': loader_update, 'plugin_updates': [{'name': n, 'from': old, 'to': remote[0]} for _, n, old, remote in jobs], 'busy': reason}), flush=True)
    if args.check or not (loader_update or jobs):
        return
    STATE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='stage-', dir=STATE) as temp:
        stage = Path(temp)
        if loader_update:
            data = fetch(asset['browser_download_url'])
            if digest(data) != expected:
                raise ValueError('Decky binary SHA-256 mismatch')
            (stage / 'PluginLoader').write_bytes(data)
        staged = []
        for i, (target, name, old, remote) in enumerate(jobs):
            ver, sha = remote[:2]
            if not re.fullmatch(r'[a-f0-9]{64}', sha):
                raise ValueError('Invalid store SHA-256')
            data = fetch(remote[2] if len(remote) > 2 and remote[2] else CDN + sha + '.zip', latest)
            if digest(data) != sha:
                raise ValueError(f'{name}: archive SHA-256 mismatch')
            root = stage / str(i)
            root.mkdir()
            staged.append((target, extract_plugin(data, name, ver, root)))
        reason = busy_reason()
        if reason:
            print('Deferred before install:', reason, flush=True)
            return
        backup = STATE / 'backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup.mkdir(parents=True)
        shutil.copytree(BASE / 'settings', backup / 'settings')
        shutil.copy2(loader, backup / 'PluginLoader')
        for target, _ in staged:
            shutil.copytree(target, backup / target.name)
        print('Backup:', backup, flush=True)
        subprocess.run(['systemctl', 'stop', 'plugin_loader.service'], check=True)
        try:
            if loader_update:
                shutil.copy2(stage / 'PluginLoader', loader)
                loader.chmod(0o755)
                subprocess.run(['restorecon', str(loader)], check=True)
            for target, source in staged:
                shutil.rmtree(target)
                shutil.copytree(source, target)
                plugin_permissions(target)
            subprocess.run(['systemctl', 'start', 'plugin_loader.service'], check=True)
            time.sleep(5)
            subprocess.run(['systemctl', 'is-active', '--quiet', 'plugin_loader.service'], check=True)
            for _, name, _, remote in jobs:
                if name == 'Bazzite Buddy':
                    (STATE / 'buddy-artifact.sha256').write_text(remote[1] + '\n')
        except Exception:
            print('Install failed; restoring previous files', flush=True)
            subprocess.run(['systemctl', 'stop', 'plugin_loader.service'], check=False)
            shutil.copy2(backup / 'PluginLoader', loader)
            for target, _ in staged:
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(backup / target.name, target)
                plugin_permissions(target)
            subprocess.run(['restorecon', str(loader)], check=False)
            subprocess.run(['systemctl', 'start', 'plugin_loader.service'], check=False)
            raise
        print('Update installed. Frontend changes load on the next Steam interface reload.', flush=True)


if __name__ == '__main__':
    main()
