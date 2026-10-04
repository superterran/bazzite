#!/usr/bin/env bash
#
# ============================== RETIRED 2026-10-03 ==============================
# Timer disabled and units moved to config/systemd/user/.retired/. Script kept
# for reference only; it is NOT scheduled and NOT deployed (just deploy-services
# globs config/systemd/user/*.{service,timer} and does not descend into .retired/).
#
# Retired for three independent reasons:
#
#  1. THE SENSOR IS GONE AND IT FAILS OPEN. It read the `anthropic:claude-cli`
#     profile from the openclaw container's auth-profiles.json. That file no
#     longer exists at that path (the glob below raises IndexError). The lookup
#     swallows the error via `|| expires=0`, and the health test is
#     `[[ $expires -gt 0 && ... ]]`, so missing data falls through to the healthy
#     branch. It reported `ok: claude-cli auth healthy (expires=0, 401s=0)`
#     unconditionally — a watchdog that can only say "fine" is worse than none.
#
#  2. DELIVERY HAD BEEN BROKEN SINCE AN OPENCLAW UPGRADE. `openclaw message send`
#     renamed `--to` to `-t, --target`. The journal shows it correctly detecting a
#     genuinely expired token for ~48h straight while every alert bounced with
#     `Missing required option "-t, --target <dest>"`.
#
#  3. WRONG HOST, AND SUPERSEDED. Scheduled automation belongs on closet, the
#     always-on host (see apps/corpus/docker-compose.yml in the closet repo:
#     "so automation doesn't depend on bazzite"). bazzite sleeps and has a
#     freeze history. The live replacement is closet's
#     /mnt/storage/scripts/cliproxy-auth-health.sh (TrueNAS cron id=12, hourly
#     at :25), which checks cliproxy — the leg that actually carries OpenClaw
#     inference now that the container-local Claude/Codex credentials are
#     vestigial — and is silent unless something is really broken.
#
# If you ever revive this: fix the --target flag, make a failed read FLAG rather
# than pass, and point it at whatever credential actually serves inference.
# ================================================================================
# openclaw-auth-watch.sh — post to pathfinderbros #my-projects when OpenClaw's
# claude-cli OAuth (Claude subscription) needs a manual re-login, so bots don't
# silently go quiet.
#
# Signal: the claude-cli ACCESS token rolls ~hourly and auto-refreshes via the
# refresh token. There is no clean "expires in N days" for the session, so we
# watch the two things that actually mean "you must reauth":
#   1. access-token `expires` is well in the PAST and not advancing (refresh chain broke)
#   2. recent 401 "Invalid authentication credentials" in the gateway log
# Delivery goes through OpenClaw's own hobbs_pb Slack connection to #my-projects
# (no token stored here; Slack send is independent of the broken model auth).
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

# Alerts post into pathfinderbros #my-projects via OpenClaw's own hobbs_pb Slack
# connection. Sending a Slack message uses the bot token, not model auth, so this
# still delivers even when claude-cli auth is the thing that's broken — the gateway
# process just has to be up.
CHANNEL="${OPENCLAW_ALERT_CHANNEL:-C0B4CGVBGN6}"   # pathfinderbros #my-projects
ACCOUNT="${OPENCLAW_ALERT_ACCOUNT:-hobbs_pb}"

msg="⚠️ *OpenClaw model auth needs you.* ${reason}.
Reauth the Claude subscription (claude-cli):
\`ssh closet docker exec -it ${OC} openclaw models auth login\`
The fallback chain is all-Claude now, so until this is fixed *every* bot is down — there is no non-Claude model to fall back to."

b64=$(printf '%s' "$msg" | base64 -w0)
out=$($SSH "docker exec $OC sh -c 'm=\$(echo $b64 | base64 -d); openclaw message send --account $ACCOUNT --channel slack --to $CHANNEL --text \"\$m\"'" 2>&1 | tail -2)
echo "alerted #my-projects (reason: $reason) -> ${out:-sent}"
mkdir -p "$(dirname "$STATE")"; echo "$now_s" > "$STATE"
