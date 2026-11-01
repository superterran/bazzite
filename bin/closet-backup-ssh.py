#!/usr/bin/python3
"""Pinned-key Closet SSH/SFTP, with an explicit Mini relay for path recovery.
Private NAS keys remain on desktop; Mini carries only the encrypted SSH stream.
"""
import os,sys
args=sys.argv[1:];via='--via-mini' in args;sftp='--sftp' in args;auto='--auto-route' in args
args=[x for x in args if x not in {'--via-mini','--sftp','--auto-route'}]
if args and args[0]=='--':args=args[1:]
base=['ssh','-F','/dev/null','-i','/home/me/.ssh/id_ed25519_truenas','-o','IdentitiesOnly=yes','-o','StrictHostKeyChecking=yes','-o','HostKeyAlias=closet.local','-o','UserKnownHostsFile=/home/me/.ssh/known_hosts','-o','BatchMode=yes','-o','ConnectTimeout=12','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=3']
if via:
 proxy=('/usr/sbin/runuser -u me -- ' if os.getuid()==0 else '')+'/usr/bin/ssh -o BatchMode=yes -o ConnectTimeout=8 mac-mini /usr/bin/nc -G 8 10.0.0.75 22'
 base+=['-o','ProxyCommand='+proxy]
if auto:base+=['-o','ProxyCommand=/usr/bin/python3 /home/me/repos/bazzite/bin/closet-backup-route.py']
if sftp:base+=['-s','root@10.0.0.75','sftp']
else:base+=['root@10.0.0.75',*args]
os.execvp(base[0],base)
