"""Get/create authorized recovery keys through Closet; never print raw results."""
import importlib.util
import json
from pathlib import Path
import resource
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def recovery_keys(existing_only=True):
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    spec=importlib.util.spec_from_file_location('volume_runtime',ROOT/'bin/productivity-secret-runtime.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    material={}
    if not existing_only:
        password=module.credential()['password']
        generated=subprocess.run(['/home/linuxbrew/.linuxbrew/bin/age-keygen'],capture_output=True,text=True,check=True)
        identity=next(line for line in generated.stdout.splitlines() if line.startswith('AGE-SECRET-KEY-'))
        uuid=subprocess.check_output(['sudo','/usr/bin/cryptsetup','luksUUID','/var/lib/productivity-volume/desktop-secure.luks'],text=True).strip()
        material={'identity':identity,'password':password,'uuid':uuid}
    base=(ROOT/'bin/productivity-1password.cjs').read_text().split("const title = 'Desktop Encrypted GNOME';")[0]
    body=(ROOT/'bin/productivity-recovery-key.cjs').read_text().replace('__RECOVERY_MATERIAL__',json.dumps(material))
    remote=shlex.join(['docker','exec','-i','codex-rc','sh','-c','ulimit -c 0; exec node -'])
    result=subprocess.run(['ssh','-o','BatchMode=yes','closet',remote],input=base+body,
                          capture_output=True,text=True,check=True,timeout=120)
    record=json.loads(result.stdout)
    recipient=subprocess.run(['/home/linuxbrew/.linuxbrew/bin/age-keygen','-y'],input=record['identity'],capture_output=True,text=True,check=True).stdout.strip()
    record['recipient']=recipient
    return record
