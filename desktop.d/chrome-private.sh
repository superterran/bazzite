#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
private_root="$HOME/.local/opt/chrome-private"
rpm_cache="$HOME/.cache/chrome-private-rpms"
mkdir -p "$private_root" "$rpm_cache" "$HOME/.config/sunshine-browser" "$HOME/.config/systemd/user" "$HOME/.local/bin"
chmod 700 "$HOME/.config/sunshine-browser"
if [[ ! -x "$private_root/usr/bin/openbox" || ! -x "$private_root/usr/bin/x11vnc" || ! -f "$private_root/usr/lib64/xorg/modules/drivers/dummy_drv.so" ]]; then
    dnf download --disablerepo='*' --enablerepo=fedora --enablerepo=updates --resolve --destdir "$rpm_cache" openbox xorg-x11-drv-dummy x11vnc
    python3 - "$rpm_cache" "$private_root" <<'PY'
from pathlib import Path
import subprocess,sys
for p in Path(sys.argv[1]).glob('*.rpm'):
    process=subprocess.Popen(['rpm2cpio',str(p)],stdout=subprocess.PIPE)
    subprocess.run(['cpio','-idmu','--quiet'],stdin=process.stdout,cwd=sys.argv[2],check=True)
    process.stdout.close()
    if process.wait()!=0:raise SystemExit('RPM extraction failed')
PY
fi
for executable in Xorg xauth xprop; do command -v "$executable" >/dev/null; done
if ! command -v pulseaudio >/dev/null; then HOMEBREW_NO_AUTO_UPDATE=1 brew install pulseaudio; fi
/usr/bin/python3 -c 'import gi; gi.require_version("GtkVnc","2.0")'
temporary_rule=$(mktemp)
trap 'rm -f "$temporary_rule"' EXIT
sed "s/@USER@/$(id -un)/g" "$repo_root/config/udev/72-chrome-private-seat.rules" > "$temporary_rule"
sudo install -m 644 "$temporary_rule" /etc/udev/rules.d/72-chrome-private-seat.rules
sudo udevadm control --reload-rules
sudo install -m 644 "$repo_root/config/firewalld/services/chrome-browser.xml" /etc/firewalld/services/chrome-browser.xml
if systemctl is-active --quiet firewalld; then
    sudo firewall-cmd --reload
    zone=$(firewall-cmd --get-default-zone)
    sudo firewall-cmd --zone="$zone" --permanent --add-service=chrome-browser
    sudo firewall-cmd --zone="$zone" --add-service=chrome-browser
fi
sed "s|@CONFIG@|$HOME/.config/sunshine-browser|g" "$repo_root/config/chrome-private/sunshine.conf" > "$HOME/.config/sunshine-browser/sunshine.conf"
python3 - "$repo_root" <<'PY'
from pathlib import Path
import json,shutil,sys,uuid
root=Path(sys.argv[1]);target=Path.home()/'.config/sunshine-browser';old=Path.home()/'.config/sunshine'
if not (target/'sunshine_state.json').exists() and (old/'sunshine_state.json').exists():
    data=json.loads((old/'sunshine_state.json').read_text())
    data.setdefault('root',{})['uniqueid']=str(uuid.uuid4()).upper()
    (target/'sunshine_state.json').write_text(json.dumps(data,indent=2)+'\n')
    (target/'sunshine_state.json').chmod(0o600)
    if (old/'credentials').exists():shutil.copytree(old/'credentials',target/'credentials',dirs_exist_ok=True)
cover=root/'assets/chrome-tv-cover.png'
apps=json.loads((root/'config/chrome-private/apps.json').read_text().replace('@COVER@',str(cover)))
(target/'apps.json').write_text(json.dumps(apps,indent=2)+'\n')
for path in (target/'credentials').glob('*') if (target/'credentials').exists() else []:path.chmod(0o600)
PY
for unit in "$repo_root"/config/systemd/user/chrome-private-*.service; do install -m 644 "$unit" "$HOME/.config/systemd/user/"; done
install -m 755 "$repo_root/bin/launch-chrome-tv.sh" "$HOME/.local/bin/launch-chrome-tv.sh"
systemctl --user daemon-reload
systemctl --user enable chrome-private-display.service chrome-private-wm.service chrome-private-audio.service chrome-private-browser.service chrome-private-vnc.service chrome-private-sunshine.service
if [[ "${1:-}" == --stage ]]; then
    echo 'Private Chrome units staged; stop the previous browser before starting them.'
else
    if curl -fsS --max-time 2 http://127.0.0.1:9223/json/version >/dev/null && ! systemctl --user is-active --quiet chrome-private-browser.service; then
        echo 'Previous Chrome is still running. Close it once before starting chrome-private-browser.service.'
        exit 0
    fi
    systemctl --user start chrome-private-display.service chrome-private-wm.service chrome-private-audio.service chrome-private-browser.service chrome-private-vnc.service chrome-private-sunshine.service
fi
