#!/usr/bin/python3
"""Create matching Steam covers and apply them to Hardware Monitor."""
import base64,json,shutil,time
from pathlib import Path
import gi
gi.require_version('GdkPixbuf','2.0')
from gi.repository import GdkPixbuf
from steam_client import evaluate
root=Path(__file__).resolve().parent.parent
assets=root/'config/hardware-monitor-artwork'
assets.mkdir(parents=True,exist_ok=True)
appid=json.loads((Path.home()/'.config/hardware-monitor.json').read_text())['appid']
# Prefer the user's illustrated set; do not regenerate the retired flat covers.
reviewed=root/'config/illustrated-steam-artwork/hardware-monitor'
if (reviewed/'portrait.png').exists():
    import runpy
    apply_art=runpy.run_path(str(root/'bin/apply-library-artwork.py'))['apply']
    for role in ['portrait','landscape','hero','icon','logo']:
        if (reviewed/(role+'.png')).exists():
            apply_art(appid,role,reviewed/(role+'.png'))
    print('Applied reviewed illustrated Hardware Monitor artwork.')
    raise SystemExit(0)
roles={'portrait':(600,900,0,'p'),'landscape':(920,430,3,''),'hero':(1920,620,1,'_hero'),'icon':(256,256,None,'_icon')}
for role,(w,h,kind,suffix) in roles.items():
    portrait=role=='portrait';icon=role=='icon';u=min(w,h)
    x=w*.5 if portrait or icon else w*.22;y=h*.32 if portrait else h*.48;r=u*.19
    tx=w*.5 if portrait else w*.44;ty=h*.59 if portrait else h*.4;fs=w*.095 if portrait else h*.105
    text='' if icon else f'<g font-family="DejaVu Sans,sans-serif" text-anchor="{"middle" if portrait else "start"}"><text x="{tx}" y="{ty}" font-size="{fs}" font-weight="bold" fill="#e5edf8">HARDWARE</text><text x="{tx}" y="{ty+fs*1.25}" font-size="{fs}" font-weight="bold" fill="#e5edf8">MONITOR</text><text x="{tx}" y="{h*.84 if portrait else h*.76}" font-size="{fs*.28}" fill="#68e0ce">TEMPERATURES / FANS / MEMORY</text></g>'
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}"><rect width="100%" height="100%" fill="#101722"/><rect x="{w*.04}" y="{h*.05}" width="{w*.92}" height="{h*.9}" rx="20" fill="none" stroke="#294453" stroke-width="3"/><path d="M {x-r},{y} A {r},{r} 0 0 1 {x+r},{y}" fill="none" stroke="#68e0ce" stroke-width="{u*.035}"/><path d="M {x},{y} L {x+r*.6},{y-r*.6}" stroke="#e5edf8" stroke-width="{u*.015}"/><circle cx="{x}" cy="{y}" r="{u*.025}" fill="#68e0ce"/>{text}</svg>'
    src=assets/(role+'.svg');src.write_text(svg)
    png=assets/(role+'.png');GdkPixbuf.Pixbuf.new_from_file(str(src)).savev(str(png),'png',[],[])
    for config in (Path.home()/'.local/share/Steam/userdata').glob('*/config'):
        if not (config/'shortcuts.vdf').exists():continue
        grid=config/'grid';grid.mkdir(exist_ok=True)
        dest=grid/(str(appid)+suffix+'.png')
        if dest.exists():
            backup=Path.home()/'.local/state/hardware-monitor/artwork-backup'/str(time.time_ns());backup.mkdir(parents=True);shutil.copy2(dest,backup/dest.name)
        shutil.copy2(png,dest)
    if kind is None:
        evaluate(f'SteamClient.Apps.SetShortcutIcon({appid},{json.dumps(str(png))})')
    else:
        data=base64.b64encode(png.read_bytes()).decode()
        evaluate(f'SteamClient.Apps.SetCustomArtworkForApp({appid},{json.dumps(data)},"png",{kind})')
    print(role,w,h)
