#!/usr/bin/python3
"""Compare applied Steam art by title/role without copying shortcut IDs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def inventory():
    locations=[Path.home()/'.local/bin',Path.home()/'repos/bazzite/bin']
    for path in locations:sys.path.insert(0,str(path))
    helper=next(p/'steam-artwork-sync.py' for p in locations if (p/'steam-artwork-sync.py').exists())
    spec=importlib.util.spec_from_file_location('artwork_sync',helper)
    art=importlib.util.module_from_spec(spec);spec.loader.exec_module(art)
    result={}
    for source in (Path.home()/'.local/share/Steam/userdata').glob('*/config/shortcuts.vdf'):
        # Steam's user0 bootstrap cache can duplicate titles without any artwork.
        if source.parent.parent.name == '0':
            continue
        for entry in art.shortcuts(source):
            roles={}
            for role,suffix in art.ROLES.items():
                if role=='layout':continue
                files=[p for p in (source.parent/'grid').glob(str(entry['appid'])+suffix+'.*')
                       if p.suffix.lower() in ['.png','.jpg','.jpeg','.webp','.ico']]
                if files:
                    latest=max(files,key=lambda p:p.stat().st_mtime_ns)
                    roles[role]=hashlib.sha256(latest.read_bytes()).hexdigest()
            result[entry['AppName']]={'id':entry['appid'],'roles':roles}
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--peer',default='ally')
    parser.add_argument('--local-json',action='store_true')
    args=parser.parse_args()
    local=inventory()
    if args.local_json:
        print(json.dumps(local));return 0
    try:
        remote=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',
                                                   '-o','ServerAliveInterval=5','-o','ServerAliveCountMax=2',
                                                   args.peer,'python3 - --local-json'],
                                                  input=Path(__file__).read_bytes(),timeout=25))
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError,json.JSONDecodeError):
        print(json.dumps({'peer':args.peer,'verified':False,'status':'unavailable',
                          'message':'Wake/connect the peer and retry; queued artwork is not verified.'}))
        return 2
    matched=0;issues=[]
    shared=local.keys()&remote.keys()
    for title in sorted(shared):
        for role in local[title]['roles'].keys()|remote[title]['roles'].keys():
            a=local[title]['roles'].get(role);b=remote[title]['roles'].get(role)
            if a==b:matched+=1
            else:issues.append({'title':title,'role':role,'reason':'missing' if a is None or b is None else 'different'})
    print(json.dumps({'shared_titles':len(shared),'matching_role_hashes':matched,'issues':issues,
                      'local_only':sorted(local.keys()-remote.keys()),
                      'peer_only':sorted(remote.keys()-local.keys())},indent=2))
    return 1 if issues else 0

if __name__=='__main__':raise SystemExit(main())
