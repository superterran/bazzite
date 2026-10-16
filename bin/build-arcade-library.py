#!/usr/bin/env python3
"""Build artwork, metadata and gamelists for the shared arcade library.

Sources (all downloaded to a cache, none committed):
  FinalBurn Neo arcade DAT        titles, years, makers, parent/clone
  MAME 2003-Plus xml/history/catver   titles for MAME-only sets, descriptions, genres, players
  libretro-thumbnails (FBNeo, MAME)   flyers, snaps, title screens, logos

Outputs:
  <artwork>/es-de/media/arcade/{covers,screenshots,titlescreens,marquees,miximages}/<set>.png
  <artwork>/es-de/gamelists/arcade.xml   relative-path gamelist, portable across devices
  <artwork>/muos/Arcade/{box,preview,text}/<set>.{png,txt}
  ~/ES-DE/gamelists/arcade/gamelist.xml  merged, keeping play stats and favourites
"""
import argparse,concurrent.futures as cf,json,os,re,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter

CACHE=Path.home()/'.cache/arcade-library'
DATS={
 'fbneo.dat':'https://raw.githubusercontent.com/libretro/FBNeo/master/dats/FinalBurn%20Neo%20(ClrMame%20Pro%20XML,%20Arcade%20only).dat',
 'm2k3p.xml':'https://raw.githubusercontent.com/libretro/mame2003-plus-libretro/master/metadata/mame2003-plus.xml',
 'history.dat':'https://raw.githubusercontent.com/libretro/mame2003-plus-libretro/master/metadata/history.dat',
 'catver.ini':'https://raw.githubusercontent.com/libretro/mame2003-plus-libretro/master/metadata/catver.ini'}
# Sets FinalBurn Neo cannot run from the files we have; verified by headless boot test 2026-10-16.
# The Capcom ones are pre-2010 romset revisions that only MAME 2003-Plus still matches.
MAME2003PLUS={'bosco','polepos','btlecity','kingball','bombbee','dsaber',
 '1941','captcomm','kod','megaman','sf2ce','willow','wof','pang3j'}
ALT_LABEL='MAME 2003-Plus'
# Arcade originals only, in release order, for the Pac-Man collection on every frontend.
PACMAN=['pacman','mspacman','jrpacman','pacnpal','pacland','pacmania']
OVERRIDES=Path(__file__).resolve().parent.parent/'config/arcade-metadata-overrides.json'
THUMBS={'covers':'Named_Boxarts','screenshots':'Named_Snaps','titlescreens':'Named_Titles','marquees':'Named_Logos'}

def fetch(name,url):
 p=CACHE/name
 if not p.exists():
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(urllib.request.urlopen(url,timeout=120).read())
 return p

def load_meta():
 fb={m.get('name'):m for m in ET.parse(fetch('fbneo.dat',DATS['fbneo.dat'])).getroot().iter('game')}
 mp={m.get('name'):m for m in ET.parse(fetch('m2k3p.xml',DATS['m2k3p.xml'])).getroot().iter('game')}
 hist={}
 for block in fetch('history.dat',DATS['history.dat']).read_text(errors='replace').split('$end'):
  m=re.search(r'\$info=([^\n]*)\n\s*\$bio\s*\n(.*)',block,re.S)
  if not m:continue
  for n in filter(None,(x.strip() for x in m.group(1).split(','))):hist.setdefault(n,m.group(2))
 cat={}
 for line in fetch('catver.ini',DATS['catver.ini']).read_text(errors='replace').splitlines():
  if line.startswith('[') and line.strip()!='[Category]' and cat:break
  if '=' in line:k,v=line.split('=',1);cat[k.strip()]=v.strip()
 return fb,mp,hist,cat

def record(g,fb,mp):
 order=[mp,fb] if g in MAME2003PLUS else [fb,mp]
 m=next((d[g] for d in order if g in d),None)
 parent=m.get('cloneof') if m is not None else None
 return m,parent

def clean_title(desc):
 t=re.sub(r'\s*\([^)]*\)\s*$','',desc).strip()
 return re.sub(r'\s*\([^)]*\)\s*$','',t).strip() or desc

def bio(text):
 if not text:return '',None
 players=re.search(r'Players\s*:\s*(\d+)',text)
 body=re.split(r'\n- [A-Z][A-Z &]+ -\n',text)[0]
 paras=[p.strip() for p in re.split(r'\n\s*\n',body) if p.strip()]
 paras=[p for p in paras if not re.match(r'^.{0,80}\(c\)\s',p)]
 out=''
 for p in paras:
  if len(out)+len(p)>900 and out:break
  out+=('\n\n' if out else '')+p
 return out,int(players.group(1)) if players else None

def candidates(g,fb,mp):
 out=[]
 for d in ([mp,fb] if g in MAME2003PLUS else [fb,mp]):
  m=d.get(g)
  if m is None:continue
  out.append(m.findtext('description'))
  p=m.get('cloneof')
  if p and p in d:out.append(d[p].findtext('description'))
 return list(dict.fromkeys(out))

def thumbs(g,names,media):
 found={}
 for kind,folder in THUMBS.items():
  dest=media/kind/(g+'.png')
  if dest.exists() and dest.read_bytes()[:4]==b'\x89PNG':found[kind]=dest;continue
  for repo in ['FBNeo_-_Arcade_Games','MAME']:
   for n in names:
    url=f'https://raw.githubusercontent.com/libretro-thumbnails/{repo}/master/{folder}/'+urllib.parse.quote(re.sub(r'[&*/:`<>?\\|"]','_',n)+'.png')
    try:
     data=urllib.request.urlopen(url,timeout=30).read()
     if not data.startswith(b'\x89PNG') and len(data)<300:  # libretro-thumbnails stores aliases as git symlinks
      data=urllib.request.urlopen(url.rsplit('/',1)[0]+'/'+urllib.parse.quote(data.decode().strip()),timeout=30).read()
     if not data.startswith(b'\x89PNG'):continue
    except Exception:continue
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);found[kind]=dest;break
   if kind in found:break
 return found

def shadowed(im,radius=18,blur=14):
 im=im.convert('RGBA');mask=Image.new('L',im.size,0)
 ImageDraw.Draw(mask).rounded_rectangle([0,0,im.width-1,im.height-1],radius,fill=255)
 im.putalpha(mask);pad=blur*2
 shadow=Image.new('RGBA',(im.width+pad*2,im.height+pad*2),(0,0,0,0))
 shadow.paste((0,0,0,170),(pad+6,pad+8,pad+6+im.width,pad+8+im.height),mask)
 shadow=shadow.filter(ImageFilter.GaussianBlur(blur));shadow.alpha_composite(im,(pad,pad))
 return shadow,pad

def miximage(found,dest):
 snap=found.get('screenshots') or found.get('titlescreens')
 if not snap:return False
 W,H=1280,960;canvas=Image.new('RGBA',(W,H),(0,0,0,0))
 s=Image.open(snap).convert('RGBA');area=(150,80,1220,900)
 scale=min((area[2]-area[0])/s.width,(area[3]-area[1])/s.height)
 s=s.resize((int(s.width*scale),int(s.height*scale)),Image.Resampling.NEAREST if scale>=2 else Image.Resampling.LANCZOS)
 framed=Image.new('RGBA',(s.width+16,s.height+16),(205,205,205,255));framed.alpha_composite(s,(8,8))
 framed,pad=shadowed(framed,14)
 x=area[2]-s.width-16+(0 if s.width>s.height else -60);y=area[1]+(area[3]-area[1]-s.height)//2
 canvas.alpha_composite(framed,(max(0,x-pad),max(0,y-pad)))
 if found.get('covers'):
  b=Image.open(found['covers']).convert('RGBA');b.thumbnail((470,620),Image.Resampling.LANCZOS)
  b,pad=shadowed(b,8,10);canvas.alpha_composite(b,(0,H-b.height+pad//2 if H-b.height+pad//2>0 else 0))
 if found.get('marquees'):
  l=Image.open(found['marquees']).convert('RGBA');l.thumbnail((600,230),Image.Resampling.LANCZOS)
  canvas.alpha_composite(l,(W-l.width-10,10))
 dest.parent.mkdir(parents=True,exist_ok=True);canvas.save(dest);return True

def muos(found,desc,root,g):
 for kind,src,bounds in [('box',found.get('covers') or found.get('titlescreens'),(250,220)),('preview',found.get('screenshots'),(250,188))]:
  if not src:continue
  d=root/kind/(g+'.png');d.parent.mkdir(parents=True,exist_ok=True)
  im=Image.open(src).convert('RGBA');im.thumbnail(bounds,Image.Resampling.LANCZOS);im.save(d)
 if desc:
  (root/'text').mkdir(parents=True,exist_ok=True);(root/'text'/(g+'.txt')).write_text(desc+'\n')

def gamelist(entries,path_prefix,existing=None):
 keep={}
 if existing and existing.exists():
  for n in ET.parse(existing).getroot().findall('game'):
   keep[Path(n.findtext('path','')).stem]={c.tag:c.text for c in n if c.tag in ['playcount','lastplayed','favorite','hidden','kidgame','rating','completed','broken','nogamecount','nomultiscrape','hidemetadata']}
 root=ET.Element('gameList')
 for e in entries:
  n=ET.SubElement(root,'game')
  for tag,val in [('path',path_prefix+e['set']+'.zip'),('name',e['name']),('desc',e['desc']),('releasedate',e['year']+'0101T000000' if e['year'].isdigit() else ''),('developer',e['maker']),('publisher',e['maker']),('genre',e['genre']),('players',e['players'])]:
   if val:ET.SubElement(n,tag).text=val
  if e['set'] in MAME2003PLUS:ET.SubElement(n,'altemulator').text=ALT_LABEL
  for tag,val in keep.get(e['set'],{}).items():
   if val:ET.SubElement(n,tag).text=val
 ET.indent(root);return '<?xml version="1.0"?>\n'+ET.tostring(root,encoding='unicode')+'\n'

def main():
 a=argparse.ArgumentParser();a.add_argument('--library',default='/var/mnt/fast/rom-library');a.add_argument('--artwork',default='/var/mnt/fast/rom-artwork')
 a.add_argument('--esde',default=str(Path.home()/'ES-DE'));a=a.parse_args()
 lib=Path(a.library)/'systems/arcade';art=Path(a.artwork);media=art/'es-de/media/arcade';mroot=art/'muos/Arcade'
 fb,mp,hist,cat=load_meta();overrides=json.loads(OVERRIDES.read_text()) if OVERRIDES.exists() else {}
 sets=sorted(p.stem for p in lib.glob('*.zip'))
 def one(g):
  m,parent=record(g,fb,mp);desc_name=m.findtext('description') if m is not None else g
  text,players=bio(hist.get(g) or hist.get(parent or '',''))
  found=thumbs(g,candidates(g,fb,mp)+overrides.get(g,{}).get('art_names',[]),media)
  mix=media/'miximages'/(g+'.png')
  if not mix.exists():miximage(found,mix)
  muos(found,text,mroot,g)
  e={'set':g,'name':clean_title(desc_name),'desc':text,'year':(m.findtext('year') if m is not None else '') or '','maker':(m.findtext('manufacturer') if m is not None else '') or '',
   'genre':cat.get(g) or cat.get(parent or '',''),'players':f'1-{players}' if players and players>1 else ('1' if players else ''),'media':sorted(found),'miximage':mix.exists()}
  e.update({k:v for k,v in overrides.get(g,{}).items() if k in ['name','desc','genre','players','year','maker']})
  if e['desc']:(mroot/'text').mkdir(parents=True,exist_ok=True);(mroot/'text'/(g+'.txt')).write_text(e['desc']+'\n')
  return e
 with cf.ThreadPoolExecutor(12) as ex:entries=sorted(ex.map(one,sets),key=lambda e:e['name'].casefold())
 (art/'muos/arcade-cores.json').write_text(json.dumps({'mame2003_plus':sorted(set(sets)&MAME2003PLUS),'pacman_collection':[g for g in PACMAN if g in sets]},indent=1))
 shared=art/'es-de/gamelists/arcade.xml';shared.parent.mkdir(parents=True,exist_ok=True);shared.write_text(gamelist(entries,'./'))
 local=Path(a.esde)/'gamelists/arcade/gamelist.xml'
 if local.parent.exists():local.write_text(gamelist(entries,'./',local))
 report={'games':len(entries),'with_description':sum(bool(e['desc']) for e in entries),'with_genre':sum(bool(e['genre']) for e in entries),
  'with_players':sum(bool(e['players']) for e in entries),'with_miximage':sum(e['miximage'] for e in entries),
  **{'with_'+k:sum(k in e['media'] for e in entries) for k in THUMBS},
  'gaps':{e['set']:[k for k in ['desc','genre','players'] if not e[k]]+[k for k in THUMBS if k not in e['media']] for e in entries if not (e['desc'] and e['genre'] and e['players'] and len(e['media'])==len(THUMBS))}}
 (art/'es-de/arcade-coverage.json').write_text(json.dumps(report,indent=1));print(json.dumps(report,indent=1))

if __name__=='__main__':main()
