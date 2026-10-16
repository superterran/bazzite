#!/bin/bash
set -euo pipefail
A=(ssh -o HostName=10.0.0.79 -o ConnectTimeout=6 ally)
"${A[@]}" 'pgrep -x retroarch >/dev/null' && { echo "Ally: RetroArch running, not applying"; exit 3; }
R=/home/bazzite/.var/app/org.libretro.RetroArch/config/retroarch
"${A[@]}" "mkdir -p '$R/overlay/ArcadeBezels' '$R/config/FinalBurn Neo'"
scp -q -o HostName=10.0.0.79 ~/repos/bazzite/config/retroarch/overlay/ArcadeBezels/* "ally:$R/overlay/ArcadeBezels/"
for f in ~/repos/bazzite/config/retroarch/config/"FinalBurn Neo"/*.cfg; do sed "s|/home/me/|/home/bazzite/|" "$f" | "${A[@]}" "cat > '$R/config/FinalBurn Neo/$(basename "$f")'"; done
sed "s|@RA_DIR@|$R|" ~/repos/bazzite/config/retroarch/family-controls.cfg | "${A[@]}" "cat > '$R/family-controls.cfg'"
scp -q -o HostName=10.0.0.79 ~/repos/bazzite/bin/launch-shared-retroarch.py ally:/home/bazzite/Applications/launch-shared-retroarch.py
"${A[@]}" "chmod 755 ~/Applications/launch-shared-retroarch.py; rm -rf '$R/autoconfig-family.tmp'; flatpak run --command=sh org.libretro.RetroArch -c \"cp -r /app/share/libretro/autoconfig '$R/autoconfig-family.tmp'\" && grep -rl '^input_menu_toggle_btn' '$R/autoconfig-family.tmp' | while read f; do sed -i '/^input_menu_toggle_btn/d' \"\$f\"; done; rm -rf '$R/autoconfig-family'; mv '$R/autoconfig-family.tmp' '$R/autoconfig-family'; grep -c appendconfig ~/Applications/launch-shared-retroarch.py; ls '$R/config/FinalBurn Neo/' | grep -c pac"
echo "Ally: applied"
