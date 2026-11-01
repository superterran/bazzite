#!/usr/bin/python3
"""Binary SSH transport: prefer direct NAS, relay via Mini if no SSH banner.
Outer SSH still authenticates the NAS host key and keeps private keys locally.
"""
import os,select,socket,sys
try:
 server=socket.create_connection(('10.0.0.75',22),timeout=3)
 server.settimeout(3)
 if not server.recv(256,socket.MSG_PEEK):raise OSError('No server banner')
except OSError:
 try:server.close()
 except NameError:pass
 args=(['/usr/sbin/runuser','-u','me','--'] if os.getuid()==0 else [])+['/usr/bin/ssh','-o','BatchMode=yes','-o','ConnectTimeout=8','mac-mini','/usr/bin/nc','-G','8','10.0.0.75','22']
 print('Backup transport: NAS direct banner unavailable; using encrypted Mini relay.',file=sys.stderr)
 os.execv(args[0],args)
server.setblocking(False);os.set_blocking(0,False);os.set_blocking(1,False)
incoming=bytearray();outgoing=bytearray();stdin_open=True;server_open=True;half_closed=False
try:
 while server_open or outgoing:
  reads=([server] if server_open and len(outgoing)<1024*1024 else [])+([0] if stdin_open and len(incoming)<1024*1024 else [])
  writes=([server] if incoming else [])+([1] if outgoing else [])
  ready,write,_=select.select(reads,writes,[],30)
  if server in ready:
   data=server.recv(65536)
   if data:outgoing.extend(data)
   else:server_open=False
  if 0 in ready:
   data=os.read(0,65536)
   if data:incoming.extend(data)
   else:stdin_open=False
  if server in write:
   count=server.send(incoming);del incoming[:count]
  if 1 in write:
   count=os.write(1,outgoing);del outgoing[:count]
  if not stdin_open and not incoming and not half_closed:
   server.shutdown(socket.SHUT_WR);half_closed=True
finally:server.close()
