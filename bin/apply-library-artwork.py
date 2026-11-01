#!/usr/bin/python3
"""Apply reviewed Steam artwork with backups and no destructive crops."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import time
from steam_client import evaluate
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'config/illustrated-steam-artwork'
BACKUP=Path.home()/'.local/state/steam-artwork-refresh'/time.strftime('%Y%m%d-%H%M%S')
ROLES={'portrait':(0,'p'),'landscape':(3,''),'hero':(1,'_hero'),'icon':(None,'_icon'),'logo':(2,'_logo')}

def apply(appid,role,path):
    kind,suffix=ROLES[role]
    for grid in (Path.home()/'.local/share/Steam/userdata').glob('*/config/grid'):
        for existing in list(grid.glob(str(appid)+suffix+'.*')):
            target=BACKUP/grid.parents[1].name/existing.name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(existing,target)
            if existing.suffix.lower() != '.png': existing.unlink()
        (grid/(str(appid)+suffix+'.png')).write_bytes(path.read_bytes())
    if kind is None:
        evaluate('SteamClient.Apps.SetShortcutIcon('+str(appid)+','+json.dumps(str(path))+')')
    else:
        data=base64.b64encode(path.read_bytes()).decode()
        evaluate('SteamClient.Apps.SetCustomArtworkForApp('+str(appid)+','+json.dumps(data)+',"png",'+str(kind)+')')

if __name__=='__main__':
    for slug,appid,crop in [('adventure-log',3911467097,'650x650+60+530'),('aisle-be-back',2725390766,'900x900+0+600'),('hardware-monitor',4235516157,'800x800+140+450')]:
        folder=ART/slug
        for source,dest,size in [('portrait-source.png','portrait.png','600x900'),('landscape-source.png','landscape.png','920x430')]:
            subprocess.run(['magick',str(folder/source),'-resize',size+'!',str(folder/dest)],check=True)
        subprocess.run(['magick',str(folder/'landscape-source.png'),'-resize','1920x620^','-gravity','center','-extent','1920x620',str(folder/'hero.png')],check=True)
        subprocess.run(['magick',str(folder/'portrait-source.png'),'-crop',crop,'+repage','-resize','512x512!',str(folder/'icon.png')],check=True)
        subprocess.run(['magick','-size','512x128','xc:none',str(folder/'logo.png')],check=True)
        for role in ROLES: apply(appid,role,folder/(role+'.png'))
        print('Applied illustrated artwork:',slug)
    fitted=ROOT/'config/fitted-library-artwork';fitted.mkdir(exist_ok=True)
    for name,appid,source,color in [
        ('moon-mission',3937440644,Path.home()/'.local/share/Steam/userdata/35894255/config/grid/3937440644p.png','black'),
        ('24-games',3616716904,Path('/mnt/fast/shared-games/24-games-windows95/cover.png'),'white')]:
        original=fitted/(name+'-original.png')
        if not original.exists():shutil.copy2(source,original)
        output=fitted/(name+'-portrait.png')
        revised=fitted/'24-games-recomposed-source.png'
        if name=='24-games' and revised.exists():
            subprocess.run(['magick',str(revised),'-resize','600x900!',str(output)],check=True)
        else:
            subprocess.run(['magick',str(original),'-filter','point' if name=='moon-mission' else 'Lanczos','-resize','560x840','-background',color,'-gravity','center','-extent','600x900',str(output)],check=True)
        apply(appid,'portrait',output)
        print('Applied fitted title-safe portrait:',name)
    print('Artwork backup:',BACKUP)
