"""Retrieve this desktop's authorized 1Password credential only in memory."""
import json
from pathlib import Path
import resource
import shlex
import subprocess


def credential():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    source = Path(__file__).with_name('productivity-1password.cjs').read_text()
    remote = shlex.join(['docker', 'exec', '-i', 'codex-rc', 'sh', '-c', 'ulimit -c 0; exec node -'])
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', 'closet', remote],
                            input=source, capture_output=True, text=True, check=True, timeout=120)
    return json.loads(result.stdout)
