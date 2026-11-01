#!/usr/bin/python3
"""Complete Steam art for installed GNOME Mahjongg and Aisleriot."""
import base64
import json
from pathlib import Path
import subprocess
from steam_client import evaluate
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'config/card-game-artwork';OUT.mkdir(parents=True,exist_ok=True)
icons = Path.home()/'.local/share/flatpak/exports/share/icons/hicolor'
font = '/usr/share/fonts/google-droid-sans-fonts/DroidSans-Bold.ttf'
for slug, appid, title, source in [
    ('mahjongg',3219622495,'MAHJONGG',icons/'scalable/apps/org.gnome.Mahjongg.svg'),
    ('solitaire',3865387876,'SOLITAIRE',icons/'256x256/apps/org.gnome.Aisleriot.png')]:
    paths={}
    for role,w,h in [('landscape',920,430),('portrait',600,900),('icon',512,512),('hero',1920,620)]:
        path=OUT/(slug+'-'+role+'.png');paths[role]=path
        logo=OUT/(slug+'-symbol.png')
        subprocess.run(['magick','-density','300','-background','none',str(source),'-resize','360x360',str(logo)],check=True)
        args=['magick','-size',f'{w}x{h}','gradient:#194f42-#092b25']
        if role=='landscape':
            args += [str(logo),'-gravity','west','-geometry','+45+0','-composite','-font',font,'-fill','white','-pointsize','50','-gravity','center','-annotate','+185+0',title]
        elif role=='portrait':
            args += [str(logo),'-gravity','center','-geometry','+0-80','-composite','-font',font,'-fill','white','-pointsize','54','-gravity','south','-annotate','+0+135',title]
        elif role=='hero':
            args += [str(logo),'-gravity','west','-geometry','+180+0','-composite','-font',font,'-fill','white','-pointsize','90','-gravity','center','-annotate','+200+0',title]
        else:
            args += [str(logo),'-gravity','center','-composite']
        subprocess.run(args+[str(path)],check=True)
    for role,kind in [('portrait',0),('landscape',3),('hero',1)]:
        data=base64.b64encode(paths[role].read_bytes()).decode()
        evaluate('SteamClient.Apps.SetCustomArtworkForApp('+str(appid)+','+json.dumps(data)+',"png",'+str(kind)+')')
    evaluate('SteamClient.Apps.SetShortcutIcon('+str(appid)+','+json.dumps(str(paths['icon']))+')')
    for grid in (Path.home()/'.local/share/Steam/userdata').glob('*/config/grid'):
        for role,suffix in [('portrait','p'),('landscape',''),('hero','_hero'),('icon','_icon')]:
            (grid/(str(appid)+suffix+'.png')).write_bytes(paths[role].read_bytes())
    print('Applied complete icon, wide capsule, portrait and hero:',title)
