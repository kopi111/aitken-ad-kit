#!/usr/bin/env bash
# Makes one TikTok ad for the given date (default today). Cron calls this through catch-up.sh.
set -euo pipefail
export PATH="/home/kopi/.local/bin:/home/kopi/.nvm/versions/node/v24.13.1/bin:/usr/local/bin:/usr/bin:/bin"
KIT=/home/kopi/projects/aitken-ad-kit
DAY="${1:-$(date +%F)}"
DELIVERY="/home/kopi/Desktop/ready to deploy/Marketing/$DAY"
LOG="$KIT/logs/$DAY.log"
mkdir -p "$KIT/logs"
cd "$KIT"

# Only ask Claude for an ad when this day has none. A finished ad still goes on to the
# copy step below, so a run that died just before delivery gets delivered next time.
if [[ -f "specs/$DAY.json" && -f "out/$DAY/$DAY.mp4" ]]; then
  echo "$(date) $DAY already made" >> "$LOG"
else
  sed "s/{{DATE}}/$DAY/g" daily-prompt.md | claude -p \
    --allowedTools "Read,Write,Edit,Glob,Grep,Bash(python3 render.py:*)" \
    --permission-mode acceptEdits >> "$LOG" 2>&1
fi

test -f "out/$DAY/$DAY.mp4" || { echo "$(date) FAILED: no video for $DAY" >> "$LOG"; exit 1; }
mkdir -p "$DELIVERY"
cp "out/$DAY/"* "$DELIVERY/"
echo "$(date) delivered to $DELIVERY" >> "$LOG"
