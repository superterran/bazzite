#!/usr/bin/python3
"""Resume only the previously recorded uploader, after validating its parent."""
import json,os,signal,subprocess
from pathlib import Path
path=Path('/var/lib/productivity-recovery/paused-baseline.json')
if path.exists():
 state=json.loads(path.read_text());current=int(subprocess.check_output(['systemctl','show','productivity-baseline.service','-p','MainPID','--value']))
 if current==state['main']:
  for value in state['restic_pids']:
   pid=int(value)
   try:
    status=Path(f'/proc/{pid}/status').read_text()
    parent=int(next(x.split()[1] for x in status.splitlines() if x.startswith('PPid:')))
    if parent==current and Path(f'/proc/{pid}/comm').read_text().strip()=='restic':os.kill(pid,signal.SIGCONT)
   except FileNotFoundError:pass
 path.unlink(missing_ok=True)
