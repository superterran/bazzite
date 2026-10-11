#!/usr/bin/env bash
# codex-remote-control.sh — keep the Codex app-server daemon up with remote control enabled.
#
# `codex remote-control start` spawns codex's own pid-managed daemon and exits, which gave
# systemd nothing to supervise: a failed start at boot or a daemon crash left the unit
# "active (exited)" with nothing running. This wrapper stays in the foreground as the
# unit's main process, starts the managed daemon (so the interactive `codex` TUI still
# finds it via ~/.codex/app-server-control/app-server-control.sock), then probes the
# daemon's control socket. If the probe fails repeatedly, it tears the daemon down and
# exits non-zero so systemd's Restart= brings everything back.
#
# `--no-daemon` was rejected on purpose: the embedded foreground server listens on a
# random /tmp socket the CLI tooling never discovers, so the TUI would launch a second daemon.
set -euo pipefail

CODEX="${CODEX_BIN:-$HOME/.local/bin/codex}"
PROBE_INTERVAL="${CODEX_PROBE_INTERVAL:-30}"   # seconds between control-socket probes
PROBE_FAILS_MAX="${CODEX_PROBE_FAILS_MAX:-3}"  # consecutive failures before restart

# Secrets for MCP servers referenced via bearer_token_env_var in ~/.codex/config.toml.
# ~/.env uses `export KEY=val` lines, which systemd's EnvironmentFile= silently drops.
if [[ -r "$HOME/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.env"
  set +a
fi

log() { printf '%s\n' "$*" >&2; }

stop_daemon() {
  timeout 20 "$CODEX" app-server daemon stop >/dev/null 2>&1 || true
}

on_term() {
  log "received stop signal; stopping app-server daemon"
  stop_daemon
  exit 0
}
trap on_term TERM INT

# codex writes {"pid":N,"processStartTime":"..."} pid files and hard-fails on a stale one from a
# previous boot ("failed to read start time for pid-managed app server N") instead of ignoring it.
# `codex app-server daemon stop` does not clean app-server-updater.pid either. Drop any pid file
# whose pid is gone or whose start time no longer matches the live process (>5s drift).
clear_stale_pidfile() {
  local f="$1" pid start actual rec_ts act_ts
  [[ -f "$f" ]] || return 0
  pid=$(grep -oE '"pid":[0-9]+' "$f" | head -1 | cut -d: -f2 || true)
  start=$(grep -oE '"processStartTime":"[^"]+"' "$f" | head -1 | cut -d'"' -f4 || true)
  if [[ -z "$pid" ]]; then
    log "removing unparseable pid file $f"
    rm -f "$f"; return 0
  fi
  actual=$(ps -o lstart= -p "$pid" 2>/dev/null | sed 's/^ *//' || true)
  if [[ -z "$actual" ]]; then
    log "removing stale pid file $f (pid $pid is not a running process)"
    rm -f "$f"; return 0
  fi
  if [[ -n "$start" ]]; then
    rec_ts=$(date -d "$start" +%s 2>/dev/null || echo 0)
    act_ts=$(date -d "$actual" +%s 2>/dev/null || echo 0)
    if (( rec_ts == 0 || act_ts == 0 || rec_ts - act_ts > 5 || act_ts - rec_ts > 5 )); then
      log "removing stale pid file $f (pid $pid reused: recorded '$start', live '$actual')"
      rm -f "$f"
    fi
  fi
}

DAEMON_DIR="$HOME/.codex/app-server-daemon"
clear_stale_pidfile "$DAEMON_DIR/app-server.pid"
clear_stale_pidfile "$DAEMON_DIR/app-server-updater.pid"

log "starting codex app-server daemon with remote control ($("$CODEX" --version 2>/dev/null || echo 'version unknown'))"
if ! "$CODEX" remote-control start; then
  log "codex remote-control start failed; exiting for systemd restart"
  stop_daemon
  exit 1
fi

fails=0
while :; do
  sleep "$PROBE_INTERVAL" & wait $! || true
  if timeout 15 "$CODEX" app-server daemon version >/dev/null 2>&1; then
    fails=0
  else
    fails=$((fails + 1))
    log "control-socket probe failed ($fails/$PROBE_FAILS_MAX)"
    if (( fails >= PROBE_FAILS_MAX )); then
      log "app-server daemon unresponsive; restarting via systemd"
      stop_daemon
      exit 1
    fi
  fi
done
