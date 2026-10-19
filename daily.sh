#!/usr/bin/env bash
# Makes one TikTok ad per day. Cron: 0 6 * * * /home/kopi/projects/aitken-ad-kit/daily.sh
set -euo pipefail
export PATH="/home/kopi/.local/bin:/home/kopi/.nvm/versions/node/v24.13.1/bin:/usr/local/bin:/usr/bin:/bin"
KIT=/home/kopi/projects/aitken-ad-kit
DAY="${1:-$(date +%F)}"
DELIVERY="/home/kopi/Desktop/ready to deploy/Marketing/$DAY"
LOG="$KIT/logs/$DAY.log"
mkdir -p "$KIT/logs"
cd "$KIT"

if [[ -f "specs/$DAY.json" && -f "out/$DAY/$DAY.mp4" ]]; then
  echo "$(date) $DAY already made" >> "$LOG"; exit 0
fi

sed "s/{{DATE}}/$DAY/g" daily-prompt.md | claude -p \
  --allowedTools "Read,Write,Edit,Glob,Grep,Bash(python3 render.py:*)" \
  --permission-mode acceptEdits >> "$LOG" 2>&1

test -f "out/$DAY/$DAY.mp4" || { echo "$(date) FAILED: no video for $DAY" >> "$LOG"; exit 1; }
mkdir -p "$DELIVERY"
cp "out/$DAY/"* "$DELIVERY/"
echo "$(date) delivered to $DELIVERY" >> "$LOG"
