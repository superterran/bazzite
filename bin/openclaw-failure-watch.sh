#!/usr/bin/env bash
# openclaw-failure-watch.sh — DM Doug when OpenClaw drops calls so failures stop
# being silent. Watches the gateway log for: model failovers, failed crons (after
# native retries), and undelivered subagent results. Count-delta based: alerts only
# on NEW failures since the last check. Runs via openclaw-failure-watch.timer (hourly).
set -uo pipefail

SSH="ssh -o ConnectTimeout=8 -o BatchMode=yes -i ${HOME}/.ssh/id_ed25519_truenas root@10.0.0.75"
OC=ix-openclaw-openclaw-1
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/openclaw-failure-watch.count"
PAT="FailoverError|job run returned error|Subagent announce give up|All models failed"

cur=$($SSH "docker exec $OC sh -c 'F=\$(ls -t /tmp/openclaw/openclaw-*.log 2>/dev/null | head -1); grep -hcE \"$PAT\" \"\$F\" 2>/dev/null || echo 0'" 2>/dev/null)
[[ "${cur:-}" =~ ^[0-9]+$ ]] || cur=0

last=$(cat "$STATE" 2>/dev/null || echo 0); [[ "$last" =~ ^[0-9]+$ ]] || last=0
mkdir -p "$(dirname "$STATE")"; echo "$cur" > "$STATE"

# new log file / day rollover -> rebaseline silently
if [[ "$cur" -lt "$last" ]]; then echo "rebaselined ($last -> $cur)"; exit 0; fi
delta=$((cur - last))
if [[ "${1:-}" == "--test" ]]; then delta=1; fi
[[ "$delta" -le 0 ]] && { echo "ok: no new failures ($cur total today)"; exit 0; }

sample=$($SSH "docker exec $OC sh -c 'F=\$(ls -t /tmp/openclaw/openclaw-*.log 2>/dev/null | head -1); grep -hoE \"($PAT)[^\\\"]{0,90}\" \"\$F\" 2>/dev/null | tail -3'" 2>/dev/null)

read -r token target < <($SSH "docker exec gmail-watcher sh -lc 'printf %s\" \"%s \"\$SLACK_BOT_TOKEN\" \"\$SLACK_TARGET\"'" 2>/dev/null)
if [[ -z "${token:-}" || -z "${target:-}" ]]; then echo "ERROR: no Slack creds from gmail-watcher" >&2; exit 1; fi

msg="⚠️ *OpenClaw dropped ${delta} call(s)* in the last hour (failover / failed cron / undelivered result). Latest:
${sample:-（check gateway logs)}
Bots auto-retry now, but flagging so it's not silent."
http=$(curl -sS -m 10 -o /dev/null -w '%{http_code}' -X POST https://slack.com/api/chat.postMessage \
    --data-urlencode "token=${token}" --data-urlencode "channel=${target}" \
    --data-urlencode "text=${msg}" --data-urlencode "unfurl_links=false")
echo "alerted Doug: $delta new failures (http=$http)"
