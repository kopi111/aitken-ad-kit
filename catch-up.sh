#!/usr/bin/env bash
# Runs every hour from cron, so an ad missed at 6 AM is made once the laptop is back on.
set -euo pipefail

KIT=/home/kopi/projects/aitken-ad-kit
MAX_TRIES_PER_DAY=3

# Use one date for the whole run, so a run that crosses midnight stays on the same day.
TODAY="$(date +%F)"
TRIES_FILE="$KIT/logs/$TODAY.tries"
mkdir -p "$KIT/logs"

# If another run still holds the lock, leave quietly so two ads are never made at once.
exec 9>"$KIT/logs/catch-up.lock"
flock -n 9 || exit 0

# Stop after the daily limit, so a broken sign-in or render cannot burn usage all day.
tries_so_far="$(cat "$TRIES_FILE" 2>/dev/null || echo 0)"
if (( tries_so_far >= MAX_TRIES_PER_DAY )); then
  exit 0
fi
echo "$(( tries_so_far + 1 ))" > "$TRIES_FILE"

# daily.sh exits straight away, without using Claude, when today's ad already exists.
"$KIT/daily.sh" "$TODAY"
