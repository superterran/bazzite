#!/usr/bin/python3
"""Build Steam capsules from the installed GNOME default and official logo."""
import base64
import json
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from steam_client import evaluate

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'config/secure-desktop-artwork'
OUTPUT.mkdir(parents=True, exist_ok=True)
background = Path('/usr/share/backgrounds/gnome/adwaita-l.jxl')
source = ET.parse('/usr/share/icons/gnome-logo-text.svg')
ns = {'s': 'http://www.w3.org/2000/svg'}
foot = next(element for element in source.iter() if element.get('id') == 'g3773')
svg = ET.Element('svg', xmlns=ns['s'], viewBox='0 0 100 120', width='1000', height='1200')
for path in foot.findall('s:path', ns):
    ET.SubElement(svg, 'path', d=path.attrib['d'], fill='white')
with tempfile.TemporaryDirectory(prefix='gnome-steam-art-') as directory:
    logo = Path(directory)/'foot.svg'
    logo.write_text(ET.tostring(svg, encoding='unicode'))
    for role, width, height, logo_height in [('landscape',920,430,310),('portrait',600,900,500),('icon',512,512,350)]:
        badge = Path(directory)/(role+'.png')
        subprocess.run(['magick','-background','none',str(logo),'-resize',f'x{logo_height}',str(badge)],check=True)
        subprocess.run(['magick',str(background),'-resize',f'{width}x{height}^','-gravity','center','-extent',f'{width}x{height}',str(badge),'-gravity','center','-composite',str(OUTPUT/(role+'.png'))],check=True)
subprocess.run(['magick',str(background),'-resize','1920x620^','-gravity','center','-extent','1920x620',str(OUTPUT/'hero.png')],check=True)
settings = json.loads((Path.home()/'.config/secure-desktop-tv.json').read_text())
appid = settings['appid']
for role, kind in [('portrait',0),('landscape',3),('hero',1)]:
    path = OUTPUT/(role+'.png')
    data = base64.b64encode(path.read_bytes()).decode()
    evaluate('SteamClient.Apps.SetCustomArtworkForApp('+str(appid)+','+json.dumps(data)+',"png",'+str(kind)+')')
evaluate('SteamClient.Apps.SetShortcutIcon('+str(appid)+','+json.dumps(str(OUTPUT/'icon.png'))+')')
# Keep standard grid files as well as Steam's live artwork update.
for config in (Path.home()/'.local/share/Steam/userdata').glob('*/config'):
    if not (config/'shortcuts.vdf').exists(): continue
    grid = config/'grid';grid.mkdir(exist_ok=True)
    for name, suffix in [('portrait','p'),('landscape',''),('hero','_hero'),('icon','_icon')]:
        (grid/(str(appid)+suffix+'.png')).write_bytes((OUTPUT/(name+'.png')).read_bytes())
print('Applied GNOME50 wide920x430, portrait600x900 and512px shortcut icon.')
