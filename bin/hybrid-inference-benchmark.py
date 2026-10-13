#!/usr/bin/env python3
"""Reproducible, bounded CPU/GPU placement comparison for Doug's desktop."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

HOME = Path.home()
RUNTIME = HOME / '.local/opt/llama-b11588/llama-b11588'
MODEL = HOME / 'models/hybrid-test/Qwen3.5-35B-A3B-Q4_K_M.gguf'
OUT = HOME / '.local/state/hybrid-test'
EXPECTED_SHA = '3b46d1066bc91cc2d613e3bc22ce691dd77e6f0d33c9060690d24ce6de494375'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--skip-hash', action='store_true')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.skip_hash:
        with MODEL.open('rb') as f:
            actual = hashlib.file_digest(f, 'sha256').hexdigest()
        if actual != EXPECTED_SHA:
            raise SystemExit(f'Model checksum mismatch: {actual}')
    env = dict(os.environ)
    env['LD_LIBRARY_PATH'] = str(RUNTIME) + ':' + str(RUNTIME.parent / 'cuda-libs') + ':' + env.get('LD_LIBRARY_PATH', '')
    scenarios = [
        ('cpu-16', 16, ['-ngl', '0', '-dev', 'none']),
        ('layers-16', 16, ['-ngl', '16']),
        ('experts-32', 16, ['-ngl', '99', '-ncmoe', '32']),
        ('experts-24', 16, ['-ngl', '99', '-ncmoe', '24']),
        ('experts-24-threads8', 8, ['-ngl', '99', '-ncmoe', '24']),
    ]
    results = []
    for label, threads, placement in scenarios:
        cmd = [str(RUNTIME / 'llama-bench'), '-m', str(MODEL),
               '-p', '512', '-n', '128', '-b', '512', '-ub', '256',
               '-t', str(threads), '-fa', 'on', '-r', '2', '-o', 'json'] + placement
        print(f'START {label}', flush=True)
        started = time.time()
        with (OUT / (label + '.stderr')).open('w') as err:
            try:
                run = subprocess.run(cmd, env=env, stdout=subprocess.PIPE,
                                     stderr=err, text=True, timeout=600)
                (OUT / (label + '.json')).write_text(run.stdout)
                parsed = json.loads(run.stdout) if run.returncode == 0 else []
                entry = dict(label=label, threads=threads, placement=placement,
                             returncode=run.returncode, seconds=time.time()-started,
                             benchmarks=parsed)
            except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
                entry = dict(label=label, error=type(e).__name__)
        results.append(entry)
        (OUT / 'results.json').write_text(json.dumps(results, indent=2))
        print(json.dumps(entry), flush=True)
        time.sleep(3)
    metadata = dict(model=str(MODEL), model_sha256=EXPECTED_SHA,
                    source_revision='bc014a17be43adabd7066b7a86075ff935c6a4e2',
                    runtime='llama.cpp b11588 CUDA 12.8',
                    timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (OUT / 'metadata.json').write_text(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
