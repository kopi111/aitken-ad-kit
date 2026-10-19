# Aitken Technology ad kit

Makes TikTok ads (1080×1920, 30 fps, silent) for Aitken Technology from real screen recordings.

- `library/` — recorded clips (see `CLIPS.md`)
- `capture.py <set>` — re-records the website clip sets (needs the sites running: Summer Splash
  `python3 -m http.server 8765` in `~/projects/summer-splash`, Aitken Shipping `dotnet run --urls http://localhost:5274`)
- `render.py specs/<id>.json` — renders an ad script into `out/<id>/`: `<id>.mp4`, `<id>-short.mp4`,
  `<id>-caption.txt`, plus `out/<id>-preview.png` (one frame every 2 s)
- `daily.sh [YYYY-MM-DD]` — the 6 AM job: Claude writes that day's script, renders it, and the files
  are copied to `~/Desktop/ready to deploy/Marketing/<date>/`. Skips a date that already has a script.
- `ads-log.md` — every ad made so far (project, angle, hook). The daily job reads it to avoid repeats.

Money Path clips were recorded on the Android emulator (`signal_test` AVD, demo data); see the
`aitken-software-tiktok-ads` memory for how.

## Ad script format (`specs/<id>.json`)

```json
{
  "id": "2026-09-29",
  "project": "aitken-shipping",
  "angle": "one line: what this ad is about",
  "title": "Short name for the caption file",
  "segments": [
    {"kind": "text", "dur": 2.5, "head": "3 signs your business<br>needs a <g>website</g><small>Number 3 costs you the most</small>"},
    {"clip": "aitken-shipping/home-hero-phone", "device": "phone", "from": 0, "dur": 3.0, "enter": "rise",
     "head": "Still taking orders on <g>WhatsApp?</g>",
     "pills": [{"at": 1.0, "text": "Instant quotes", "icon": "$", "y": 1100}]},
    {"clip": "money-path/today-static", "device": "phone", "from": 0, "dur": 2.3, "dim": true,
     "head": "Private <g>by design</g>", "pills": [...]}
  ],
  "end": {"dur": 4.0, "cta": "Run a business?<br>Comment <g>WEBSITE</g><br>and we'll DM you"},
  "short": [0, 1],
  "caption": "Caption text, line breaks as \\n",
  "hashtags": ["#jamaica", "#aitkentechnology"]
}
```

- `head`: at most 48 visible characters; wrap a word or two in `<g>` for the brand gradient.
- `kind: "text"`: a full-screen statement with no device (hooks, tips, "3 signs…"); `<small>` adds a subline.
- `from` + `dur` must fit inside the clip (the renderer refuses otherwise).
- `enter: "rise"` slides the device up (use on the first segment); `dim: true` darkens it so pills stand out.
- Pills: `at` seconds into the segment, `y` between 700 and 1480; `icon` is one character.
- `short`: segment numbers for the 7–12 s cut; the end card is added automatically.
- Total length 12–32 s. Keep text out of TikTok's UI: the renderer already keeps it in the safe area.
