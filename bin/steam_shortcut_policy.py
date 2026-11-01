"""Honor this host's explicitly retired Steam shortcuts during setup."""
import json
import os
from pathlib import Path

def retired(title):
    if os.environ.get('BAZZITE_RESTORE_RETIRED_SHORTCUTS') == '1':
        return False
    path = Path.home()/'.config/retired-steam-shortcuts.json'
    return path.exists() and title in json.loads(path.read_text()).get('titles', [])
