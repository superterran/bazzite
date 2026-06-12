#!/usr/bin/env bash
# openclaw-auth-watch.sh — DM Doug on Slack when OpenClaw's claude-cli OAuth
# (Claude subscription) needs a manual re-login, so bots don't silently fall
# back to Codex / go quiet.
#
# Signal: the claude-cli ACCESS token rolls ~hourly and auto-refreshes via the
# refresh token. There is no clean "expires in N days" for the session, so we
# watch the two things that actually mean "you must reauth":
#   1. access-token `expires` is well in the PAST and not advancing (refresh chain broke)
#   2. recent 401 "Invalid authentication credentials" in the gateway log
# Delivery reuses the same Slack bot token + DM target that Netdata thermal
# alerts use (pulled at runtime from the gmail-watcher container — never stored here).
#
# Runs via openclaw-auth-watch.timer (systemd --user). Throttles repeat alerts.
set -uo pipefail

SSH="ssh -o ConnectTimeout=8 -o BatchMode=yes -i ${HOME}/.ssh/id_ed25519_truenas root@10.0.0.75"
OC=ix-openclaw-openclaw-1
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/openclaw-auth-watch.state"
THROTTLE_SECS=$((12 * 3600))   # re-alert at most every 12h while still broken
STALE_MIN_THRESHOLD=30         # access token this many min past expiry w/o refresh = broken

now_s=$(date +%s)
now_ms=$((now_s * 1000))

expires=$($SSH "docker exec $OC python3 -c \"import json,glob;d=json.load(open(glob.glob('/home/node/.openclaw/agents/main/agent/auth-profiles.json')[0]))['profiles']['anthropic:claude-cli'];print(d.get('expires',0))\"" 2>/dev/null) || expires=0
[[ "$expires" =~ ^[0-9]+$ ]] || expires=0
auth401=$($SSH "docker logs --since 6h $OC 2>&1 | grep -c 'Invalid authentication credentials'" 2>/dev/null) || auth401=0
[[ "$auth401" =~ ^[0-9]+$ ]] || auth401=0

reason=""
if [[ "$expires" -gt 0 && "$now_ms" -gt "$expires" ]]; then
    stale_min=$(((now_ms - expires) / 60000))
    if [[ "$stale_min" -gt "$STALE_MIN_THRESHOLD" ]]; then
        reason="claude-cli access token expired ${stale_min}min ago and is not refreshing"
    fi
fi
if [[ "$auth401" -gt 0 ]]; then
    reason="${reason:+$reason; }${auth401}x 401 auth errors in the last 6h"
fi

# --test forces an alert to verify Slack delivery end to end
if [[ "${1:-}" == "--test" ]]; then
    reason="TEST — ignore (verifying the OAuth watchdog Slack path works)"
fi

if [[ -z "$reason" ]]; then
    rm -f "$STATE"   # healthy: clear incident so the next break re-alerts immediately
    echo "ok: claude-cli auth healthy (expires=$expires, 401s=$auth401)"
    exit 0
fi

# throttle: don't re-DM more than once per THROTTLE_SECS while still broken
if [[ "${1:-}" != "--test" && -f "$STATE" ]]; then
    last=$(cat "$STATE" 2>/dev/null || echo 0)
    [[ "$last" =~ ^[0-9]+$ ]] || last=0
    if [[ $((now_s - last)) -lt "$THROTTLE_SECS" ]]; then
        echo "unhealthy ($reason) but within throttle window; not re-alerting"
        exit 0
    fi
fi

read -r token target < <($SSH "docker exec gmail-watcher sh -lc 'printf %s\" \"%s \"\$SLACK_BOT_TOKEN\" \"\$SLACK_TARGET\"'" 2>/dev/null)
if [[ -z "${token:-}" || -z "${target:-}" ]]; then
    echo "ERROR: could not read Slack creds from gmail-watcher; cannot alert" >&2
    exit 1
fi

msg="⚠️ *OpenClaw model auth needs you.* ${reason}.
Reauth the Claude subscription (claude-cli):
\`ssh closet docker exec -it ${OC} openclaw models auth login\`
Until then, agents fall back to Codex (which can cap) and may go silent."

http=$(curl -sS -m 10 -o /dev/null -w '%{http_code}' -X POST https://slack.com/api/chat.postMessage \
    --data-urlencode "token=${token}" \
    --data-urlencode "channel=${target}" \
    --data-urlencode "text=${msg}" \
    --data-urlencode "unfurl_links=false")
echo "alerted Doug (reason: $reason) http=$http"
mkdir -p "$(dirname "$STATE")"; echo "$now_s" > "$STATE"
