#!/usr/bin/python3
"""Read-only, controller-friendly sensor viewer for Steam/Gamescope."""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess


def read_sensors():
    devices = {}
    for h in sorted(Path('/sys/class/hwmon').glob('hwmon*')):
        try:
            name = (h / 'name').read_text().strip()
            values = {}
            for f in h.glob('*_input'):
                if not re.fullmatch(r'(temp|fan)\d+_input', f.name):
                    continue
                label = h / f.name.replace('_input', '_label')
                key = label.read_text().strip() if label.exists() else f.name
                values[key] = int(f.read_text())
            for key in ('pwm2', 'pwm2_enable'):
                if (h / key).exists():
                    values[key] = int((h / key).read_text())
            devices.setdefault(name, []).append(values)
        except (OSError, ValueError):
            continue
    try:
        out = subprocess.check_output(['nvidia-smi', '--query-gpu=name,temperature.gpu,fan.speed,power.draw', '--format=csv,noheader,nounits'], text=True, timeout=2).strip().split(',')
        gpu = {'name': out[0].strip(), 'temperature': float(out[1]), 'fan_percent': float(out[2]) if out[2].strip() not in ('N/A', '[N/A]') else None, 'power_w': float(out[3])}
    except (subprocess.SubprocessError, ValueError, IndexError, OSError):
        gpu = None
    try:
        cooler = read_coolercontrol()
    except (OSError, ValueError, KeyError, TypeError):
        cooler = None
    return {'cooler': cooler, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'bios': Path('/sys/class/dmi/id/bios_version').read_text().strip(), 'devices': devices, 'gpu': gpu}


def read_coolercontrol():
    """Read cached daemon telemetry; never open the cooler USB device."""
    import urllib.request
    token = (Path.home() / '.config/hardware-monitor/coolercontrol-token').read_text().strip()
    req = urllib.request.Request('http://127.0.0.1:11987/status',
        headers={'Authorization': 'Bearer ' + token})
    with urllib.request.urlopen(req, timeout=1) as response:
        payload = json.load(response)
    devices = {d['uid']: d.get('status_history', []) for d in payload.get('devices', [])}
    kraken = devices.get('fa4f791f8b63a9adc86f96b4acdb5936756e938f7d9d1bc04ef7facf5b364849', [])
    if not kraken:
        raise ValueError('Kraken telemetry missing')
    latest = kraken[-1]
    age = (datetime.datetime.now(datetime.timezone.utc) -
           datetime.datetime.fromisoformat(latest['timestamp'])).total_seconds()
    if age > 10:
        raise ValueError('Kraken telemetry stale')
    channels = {c['name']: c for c in latest.get('channels', [])}
    temps = {t['name']: t['temp'] for t in latest.get('temps', [])}
    cpu = devices.get('f98fcca0ec98fb32c1a40f148747c0d2308083af19eab157f32b777743c1c77c', [])
    cpu_channels = {c['name']: c for c in cpu[-1].get('channels', [])} if cpu else {}
    mb = devices.get('00a4da18625f56275c89e2fcd25a83c08c5ad3326452fa7e252fcc8a89c92493', [])
    mb_channels = {c['name']: c for c in mb[-1].get('channels', [])} if mb else {}
    return {'radiator1_percent': mb_channels.get('fan2', {}).get('duty'), 'radiator2_percent': mb_channels.get('fan7', {}).get('duty'), 'coolant_c': temps.get('liquid'), 'pump_rpm': channels.get('pump', {}).get('rpm'),
            'pump_percent': channels.get('pump', {}).get('duty'),
            'fan_rpm': channels.get('fan', {}).get('rpm'),
            'fan_percent': channels.get('fan', {}).get('duty'),
            'cpu_power_w': cpu_channels.get('power0', {}).get('watts'),
            'cpu_load_percent': cpu_channels.get('CPU Load', {}).get('duty')}


def sensor(data, device, key, index=0):
    ds = data['devices'].get(device, [])
    return ds[index].get(key) if len(ds) > index else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--snapshot', action='store_true')
    args = parser.parse_args()
    if args.snapshot:
        print(json.dumps(read_sensors(), indent=2))
        return
    memory_status = 'RAM configured speed: unavailable'
    try:
        dmi = subprocess.check_output(['sudo', '-n', 'dmidecode', '--type', '17'], text=True, stderr=subprocess.DEVNULL, timeout=3)
        speeds = re.findall(r'Configured Memory Speed:\s*(\d+) MT/s', dmi)
        if speeds:
            memory_status = 'RAM configured speed: ' + ' / '.join(dict.fromkeys(speeds)) + ' MT/s (firmware report)'
    except (OSError, subprocess.SubprocessError):
        pass
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('GdkX11', '3.0')
    from gi.repository import Gtk, Gdk, GdkX11, GLib
    css = Gtk.CssProvider()
    css.load_from_data(b'''
      window { background: #101722; color: #e5edf8; }
      label { font-family: Sans; font-size: 32px; }
      .title { font-size: 54px; font-weight: bold; color: #68e0ce; }
      .subtitle { font-size: 22px; color: #a3b3c8; }
      .value { font-size: 38px; font-weight: bold; }
      progressbar trough { min-height: 18px; background: #25344a; border: 0; }
      progressbar progress { min-height: 18px; background: #53d7b7; border: 0; }
      .warm progress { background: #e5b751; }
      .hot progress { background: #ed7777; }
      button { font-size: 22px; padding: 10px 22px; background: #25344a; color: #e5edf8; }
    ''')
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    win = Gtk.Window(title='Hardware Monitor')
    win.set_default_size(1600, 900)
    win.connect('destroy', Gtk.main_quit)
    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    outer.set_border_width(32)
    win.add(outer)

    def label(text, cls=None):
        w = Gtk.Label(label=text, xalign=0)
        if cls:
            w.get_style_context().add_class(cls)
        if cls == 'subtitle':
            w.set_line_wrap(True)
            w.set_max_width_chars(110)
        return w

    top = Gtk.Box(spacing=20)
    top.pack_start(label('Hardware Monitor', 'title'), True, True, 0)
    close = Gtk.Button(label='Close  ·  Esc')
    close.connect('clicked', lambda *_: win.destroy())
    top.pack_end(close, False, False, 0)
    outer.pack_start(top, False, False, 0)
    status = label('', 'subtitle')
    outer.pack_start(status, False, False, 0)
    grid = Gtk.Grid(column_spacing=32, row_spacing=12)
    outer.pack_start(grid, True, True, 0)
    definitions = [
        ('CPU Tctl', 'k10temp', 'Tctl', 0, 85, 94),
        ('Kraken coolant', 'kraken', 'coolant', 0, 45, 55),
        ('CPU CCD 1', 'k10temp', 'Tccd1', 0, 85, 94),
        ('CPU CCD 2', 'k10temp', 'Tccd2', 0, 85, 94),
        ('Motherboard', 'asusec', 'Motherboard', 0, 65, 80),
        ('VRM', 'asusec', 'VRM', 0, 80, 95),
        ('DIMM sensor 1', 'spd5118', 'temp1_input', 0, 55, 75),
        ('DIMM sensor 2', 'spd5118', 'temp1_input', 1, 55, 75),
        ('NVMe sensor 1', 'nvme', 'Composite', 0, 70, 85),
        ('NVMe sensor 2', 'nvme', 'Composite', 1, 70, 85),
        ('GPU', None, None, 0, 80, 88),
    ]
    rows = []
    for i, (title, *_) in enumerate(definitions):
        name = label(title)
        value = label('—', 'value')
        bar = Gtk.ProgressBar()
        bar.set_hexpand(True)
        grid.attach(name, 0, i, 1, 1)
        grid.attach(value, 1, i, 1, 1)
        grid.attach(bar, 2, i, 1, 1)
        rows.append((value, bar))
    fans = label('')
    gpu_label = label('', 'subtitle')
    info = label('', 'subtitle')
    outer.pack_start(fans, False, False, 0)
    outer.pack_start(gpu_label, False, False, 0)
    outer.pack_start(info, False, False, 0)
    outer.pack_start(label('Read-only sensors · Unmapped AUX channels omitted · Esc closes', 'subtitle'), False, False, 0)

    def refresh():
        try:
            data = read_sensors()
            for definition, (value, bar) in zip(definitions, rows):
                _, dev, key, index, warning, hot = definition
                raw = (data['cooler'].get('coolant_c') * 1000 if data.get('cooler') and data['cooler'].get('coolant_c') is not None else None) if dev == 'kraken' else sensor(data, dev, key, index) if dev else None
                temp = raw / 1000 if raw is not None else data['gpu']['temperature'] if dev is None and data['gpu'] else None
                value.set_text(f'{temp:.1f} °C' if temp is not None else 'Unavailable')
                bar.set_fraction(max(0, min(1, temp / 100)) if temp is not None else 0)
                style = bar.get_style_context()
                for cls in ('warm', 'hot'):
                    style.remove_class(cls)
                if temp is not None and temp >= warning:
                    style.add_class('hot' if temp >= hot else 'warm')
            cooler = data.get('cooler')
            rpm = lambda v: f'{v:,.0f} RPM' if v is not None else 'unavailable'
            fan1 = sensor(data, 'nct6799', 'fan2_input')
            fan2 = sensor(data, 'nct6799', 'fan7_input')
            pump = cooler.get('pump_rpm') if cooler else sensor(data, 'nct6799', 'fan6_input')
            fan_text = f'CPU_FAN: {rpm(fan1)} · CHA_FAN: {rpm(fan2)} · Kraken pump: {rpm(pump)}'
            if cooler and cooler.get('radiator1_percent') is not None and cooler.get('radiator2_percent') is not None:
                fan_text += f" · Commands: {cooler['radiator1_percent']:.0f}% / {cooler['radiator2_percent']:.0f}%"
            fans.set_text(fan_text)
            gpu = data['gpu']
            if gpu:
                reading = f"{gpu['fan_percent']:.0f}%" if gpu['fan_percent'] is not None else 'unavailable'
                gpu_label.set_text(f"{gpu['name']} · {gpu['power_w']:.1f} W · Fan report: {reading} (telemetry only; 0% may not reflect physical fans)")
            else:
                gpu_label.set_text('NVIDIA telemetry unavailable')
            available = next((int(l.split()[1])/1024/1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')), 0)
            cpu_extra = ''
            if cooler and cooler.get('cpu_power_w') is not None and cooler.get('cpu_load_percent') is not None:
                cpu_extra = f"CPU {cooler['cpu_power_w']:.1f} W · Load {cooler['cpu_load_percent']:.1f}% · "
            info.set_text(cpu_extra + f'Available RAM: {available:.1f} GiB · Load average: {Path("/proc/loadavg").read_text().split()[0]} · CPU_FAN / CHA_FAN: motherboard hardware curve · Kraken pump: CoolerControl')
            status.set_text(f'BIOS {data["bios"]} · {memory_status} · Updated {datetime.datetime.now().strftime("%H:%M:%S")}')
        except Exception as exc:
            status.set_text('Sensor refresh failed: ' + type(exc).__name__)
        return True

    win.connect('key-press-event', lambda _, event: (win.destroy(), True)[1] if event.keyval == Gdk.KEY_Escape else False)
    win.show_all()
    appid = os.environ.get('SteamAppId', '')
    if appid.isdigit():
        xid = GdkX11.X11Window.get_xid(win.get_window())
        subprocess.run(['xprop', '-id', str(xid), '-f', 'STEAM_GAME', '32c', '-set', 'STEAM_GAME', appid], check=True)
    win.fullscreen()
    if appid.isdigit():
        def focus_monitor():
            from steam_client import evaluate
            evaluate(f'(()=>{{SteamUIStore.SetRunningApp({int(appid)});SteamUIStore.NavigateToRunningApp();return true;}})()')
            subprocess.run(['xprop', '-display', ':0', '-root', '-f', 'GAMESCOPECTRL_BASELAYER_APPID', '32c', '-set', 'GAMESCOPECTRL_BASELAYER_APPID', f'{appid}, 769'], check=True)
            return False
        GLib.timeout_add(700, focus_monitor)
    refresh()
    GLib.timeout_add_seconds(2, refresh)
    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (Gtk.main_quit(), False)[1])
    Gtk.main()


if __name__ == '__main__':
    main()
