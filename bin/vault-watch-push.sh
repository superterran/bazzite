#!/usr/bin/env bash
#
# watch-and-push.sh — inotifywait-based watcher for Obsidian vault git backup
#
# Watches ~/Documents/Cloud Vault/ for filesystem changes, debounces them,
# then stages, commits, and pushes to the backup remote.
#
# Designed to run as a systemd user service (always-on, not a timer).
#

set -euo pipefail

VAULT_DIR="${VAULT_DIR:-$HOME/Documents/Cloud Vault}"
DEBOUNCE_SECS="${DEBOUNCE_SECS:-30}"
BRANCH="${BRANCH:-main}"

# Ensure vault directory exists and is a git repo
if [[ ! -d "$VAULT_DIR/.git" ]]; then
    echo "ERROR: $VAULT_DIR is not a git repository" >&2
    exit 1
fi

# Ensure inotifywait is available
if ! command -v inotifywait &>/dev/null; then
    echo "ERROR: inotifywait not found. Install inotify-tools." >&2
    exit 1
fi

commit_and_push() {
    cd "$VAULT_DIR"

    # Stage all changes
    git add -A

    # Check if there's anything to commit
    if git diff --cached --quiet; then
        echo "[$(date -Iseconds)] No staged changes to commit."
        return 0
    fi

    # Count changes for commit message
    local added deleted modified
    added=$(git diff --cached --numstat | wc -l)
    modified=$(git diff --cached --diff-filter=M --numstat | wc -l)
    deleted=$(git diff --cached --diff-filter=D --numstat | wc -l)

    local msg="vault backup: ${added} file(s) changed"
    if [[ "$modified" -gt 0 ]]; then
        msg+=", ${modified} modified"
    fi
    if [[ "$deleted" -gt 0 ]]; then
        msg+=", ${deleted} deleted"
    fi
    msg+=" [$(date '+%Y-%m-%d %H:%M')]"

    echo "[$(date -Iseconds)] Committing: $msg"
    git commit -m "$msg"

    # Pull-rebase before pushing so commits from elsewhere (CI, other machines)
    # land in the working tree. --autostash protects in-flight edits across rebase.
    echo "[$(date -Iseconds)] Pulling origin/$BRANCH (rebase)..."
    if ! git pull --rebase --autostash origin "$BRANCH" 2>&1; then
        echo "[$(date -Iseconds)] WARNING: Pull-rebase failed (likely conflict). Aborting and skipping push." >&2
        git rebase --abort 2>/dev/null || true
        return 0
    fi

    echo "[$(date -Iseconds)] Pushing to origin/$BRANCH..."
    if git push origin "$BRANCH" 2>&1; then
        echo "[$(date -Iseconds)] Push successful."
    else
        echo "[$(date -Iseconds)] WARNING: Push failed. Will retry on next change." >&2
    fi
}

echo "[$(date -Iseconds)] Starting vault watcher on: $VAULT_DIR"
echo "[$(date -Iseconds)] Debounce: ${DEBOUNCE_SECS}s"

# Pull at startup so we pick up any commits pushed from CI / other machines
# while this watcher was offline. --autostash protects any uncommitted edits.
echo "[$(date -Iseconds)] Initial pull from origin/$BRANCH..."
(cd "$VAULT_DIR" && git pull --rebase --autostash origin "$BRANCH" 2>&1) || \
    echo "[$(date -Iseconds)] WARNING: Initial pull failed. Continuing." >&2

# Do an initial commit of any pending changes (e.g., from downtime)
echo "[$(date -Iseconds)] Checking for pending changes..."
commit_and_push

# Watch for changes. inotifywait -m (monitor mode) emits events continuously.
# We read events, then wait for the debounce period with no new events before acting.
#
# --exclude: skip .git internals and sync lock
# -r: recursive
# -e: events to watch
# --format: just output the event type and path for logging

LAST_EVENT_TIME=0

inotifywait -m -r \
    --exclude '(\.git/|\.obsidian/\.sync\.lock)' \
    -e create -e modify -e delete -e move -e attrib \
    --format '%T %e %w%f' \
    --timefmt '%s' \
    "$VAULT_DIR" 2>&1 | while read -r TIMESTAMP EVENT FILEPATH; do

    # Skip .git directory events that leak through
    if [[ "$FILEPATH" == *"/.git/"* ]]; then
        continue
    fi

    echo "[$(date -Iseconds)] Event: $EVENT on $FILEPATH"
    LAST_EVENT_TIME=$(date +%s)

    # Drain additional events for the debounce period
    # Use read with timeout to wait for more events
    while read -r -t "$DEBOUNCE_SECS" TIMESTAMP EVENT FILEPATH; do
        if [[ "$FILEPATH" == *"/.git/"* ]]; then
            continue
        fi
        echo "[$(date -Iseconds)] Event: $EVENT on $FILEPATH (debouncing...)"
        LAST_EVENT_TIME=$(date +%s)
    done

    echo "[$(date -Iseconds)] Debounce period elapsed. Committing changes..."
    commit_and_push
done

echo "[$(date -Iseconds)] ERROR: inotifywait exited unexpectedly" >&2
exit 1
