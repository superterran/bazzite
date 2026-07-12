#!/usr/bin/env bash
# dashboard-heartbeat.sh — white-box heartbeat for the bazzite desktop.
# POSTs systemd/GPU/temp state to the hatcher.ltd infra dashboard every minute (systemd timer).
# Reads HEARTBEAT_TOKEN from ~/.env; the dashboard shows this box red if the ping goes stale.
set -euo pipefail
source "$HOME/.env" 2>/dev/null || true
URL="${DASHBOARD_URL:-https://hatcher-dashboard.doug-hatcher.workers.dev/dashboard}/heartbeat"
TOKEN="${HEARTBEAT_TOKEN:?HEARTBEAT_TOKEN not set in ~/.env}"

# Services that should be active. Edit freely.
WATCH=(cloudflared opencode-web claude-remote-control obsidian-sync netdata task-dispatch-mcp-http)
svc_json=""
for s in "${WATCH[@]}"; do
  state=$(systemctl --user is-active "$s.service" 2>/dev/null || echo unknown)
  svc_json+="\"$s\":\"$state\","
done
svc_json="{${svc_json%,}}"

mapfile -t failing < <(systemctl --user list-units --state=failed --no-legend --no-pager 2>/dev/null | grep -oE '[^ ]+\.service' | sed 's/\.service$//')
failed=0; fjson=""
for u in "${failing[@]:-}"; do [ -n "$u" ] && { failed=$((failed+1)); fjson+="\"$u\","; }; done
fjson="${fjson%,}"

# GPU (nvidia) — nulls if absent.
read -r vram_used vram_total temp < <(nvidia-smi --query-gpu=memory.used,memory.total,temperature.gpu \
  --format=csv,noheader,nounits 2>/dev/null | head -1 | tr -d ',' || echo "")
vram_used=${vram_used:-null}; vram_total=${vram_total:-null}; temp=${temp:-null}

payload="{\"host\":\"bazzite\",\"failed\":$failed,\"failing\":[$fjson],\"services\":$svc_json,\"vramUsed\":${vram_used:-null},\"vramTotal\":${vram_total:-null},\"tempC\":${temp:-null}}"

curl -sS -m 10 -X POST "$URL" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$payload" >/dev/null
