#!/usr/bin/env bash
set -euo pipefail
# GitHub job secrets and rendered deployment state must not persist between jobs.
case "${GITHUB_WORKSPACE:-}" in
  /runner/_work/hyde/hyde) rm -rf -- "$GITHUB_WORKSPACE/.deploy";;
  *) echo 'No deployment scratch directory to clean';;
esac
if [[ "${GITHUB_WORKSPACE:-}" == /runner/_work/hyde/hyde ]]; then
  rm -f -- "$GITHUB_WORKSPACE/infra/terraform/deployment.plan" "$GITHUB_WORKSPACE/infra/jabber/jabber.plan"
fi
