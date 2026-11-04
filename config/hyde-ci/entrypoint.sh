#!/usr/bin/env bash
set -euo pipefail
cd /runner
if [[ ! -x ./config.sh ]]; then cp -a /opt/actions/. /runner/; fi
if [[ ! -f .runner ]]; then
  echo 'Waiting for repository-scoped runner enrollment'
  exec sleep infinity
fi
exec ./run.sh
