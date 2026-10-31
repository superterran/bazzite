#!/usr/bin/env python3
"""Merge managed session entries into native Sunshine, preserving other apps."""
from datetime import datetime
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
target = Path.home() / '.config/sunshine/apps.json'
template = json.loads((root / 'config/sunshine/apps.json').read_text())
data = json.loads(target.read_text()) if target.exists() else template.copy()
managed = {app['name'] for app in template['apps']} | {'Desktop'}
data['apps'] = template['apps'] + [app for app in data.get('apps', [])
                                if app.get('name') not in managed]
content = json.dumps(data, indent=2) + '\n'
if not target.exists() or target.read_text() != content:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.copy2(target, target.with_name('apps.json.before-session-entries-' +
                                            datetime.now().strftime('%Y%m%d-%H%M%S')))
    temporary = target.with_suffix('.json.tmp')
    temporary.write_text(content)
    temporary.replace(target)
print('Configured passive Display Mode and Steam Big Picture entries; session switching disabled.')
