#!/usr/bin/python3
"""Fullscreen view of the one persistent private Chrome desktop."""
import gi
import os
import signal
import subprocess
import ctypes
import argparse
gi.require_version('Gtk','3.0')
gi.require_version('GtkVnc','2.0')
from gi.repository import Gtk, GtkVnc, GLib
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--title',default='Chrome - TV & Automation')
parser.add_argument('--focus-helper',default='focus-chrome-tv.py')
args=parser.parse_args()
window=Gtk.Window(title=args.title)
window.set_default_size(1920,1080)
window.connect('destroy',Gtk.main_quit)
display=GtkVnc.Display.new()
display.set_shared_flag(True)
display.set_scaling(True)
display.set_force_size(False)
display.set_keyboard_grab(False)
display.set_pointer_grab(False)
display.set_pointer_force_visible(True)
display.connect('vnc-disconnected',lambda *_: Gtk.main_quit())
display.connect('vnc-initialized',lambda *_: display.grab_focus())
def focus_viewer():
    subprocess.Popen(['/usr/bin/python3',str(Path.home()/'repos/bazzite/bin'/args.focus_helper)])
    return False
display.connect('vnc-initialized',lambda *_: GLib.timeout_add(2000 if args.title=='1Password' else 500,focus_viewer))
window.add(display)
window.show_all()
window.fullscreen()
display.open_host('127.0.0.1','5905')
runtime=os.environ.get('XDG_RUNTIME_DIR',f'/run/user/{os.getuid()}')
parent_pid=os.getpid()
libc=ctypes.CDLL(None)
def stop_audio_with_viewer():
    # Steam may kill the viewer without allowing its Python cleanup to run.
    libc.prctl(1,signal.SIGTERM,0,0,0)  # PR_SET_PDEATHSIG
    if os.getppid()!=parent_pid:os._exit(1)
capture=subprocess.Popen(['/home/linuxbrew/.linuxbrew/bin/parec','--server=unix:'+runtime+'/chrome-private/pulse/native','--device=browser.monitor','--format=s16le','--rate=48000','--channels=2'],stdout=subprocess.PIPE,preexec_fn=stop_audio_with_viewer)
playback=subprocess.Popen(['/home/linuxbrew/.linuxbrew/bin/paplay','--server=unix:'+runtime+'/pulse/native','--raw','--format=s16le','--rate=48000','--channels=2'],stdin=capture.stdout,preexec_fn=stop_audio_with_viewer)
capture.stdout.close()
GLib.unix_signal_add(GLib.PRIORITY_DEFAULT,signal.SIGTERM,lambda: (Gtk.main_quit(),False)[1])
try:
    Gtk.main()
finally:
    display.close()
    for child in [capture,playback]:
        child.terminate()
    for child in [capture,playback]:
        try:child.wait(timeout=3)
        except subprocess.TimeoutExpired:child.kill();child.wait()
