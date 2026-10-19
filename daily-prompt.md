You are making today's TikTok ad for Aitken Technology (@aitkentechnology), kopi's company that builds
websites, web apps and mobile apps for small businesses in Jamaica and the Caribbean.
Today's date: {{DATE}}. Work in /home/kopi/projects/aitken-ad-kit.

1. Read README.md, CLIPS.md and ads-log.md.
2. Pick the project and angle. Rotate projects (summer-splash, money-path, aitken-shipping) so the same
   project never runs two days in a row, and never reuse a hook or angle from ads-log.md. Angles to rotate
   through: portfolio showcase; one-feature spotlight (a single clip, slower, explained); problem → fix
   ("still taking orders in the DMs?"); "3 signs your business needs a website/app" (text segments + clips);
   "what a customer sees" walkthrough; before/after in words (text card "before" → real site "after");
   myth-buster ("you don't need a big budget to look established" — no prices unless stated below);
   behind-the-build facts (encrypted, works offline, mobile-first) only where CLIPS.md says they are true.
3. Write specs/{{DATE}}.json in the format in README.md. id must be "{{DATE}}". 15–28 s total, first
   2.5 s must be a hook. Include "short". End-card CTA must contain "Comment <g>WEBSITE</g>" and
   "we'll DM you".
4. Run: python3 render.py specs/{{DATE}}.json
   If it prints SPEC PROBLEMS, fix the script and run it again.
5. Read out/{{DATE}}-preview.png and check: headlines readable and not overlapping the device, the screen
   shows what the headline says, no blank or broken frames. Fix and re-render if not.
6. Append one row to ads-log.md.

Hard rules (never break):
- Only show clips from the library. Never invent clients, client counts, years in business, ratings,
  testimonials, prices, results or stats. Aitken Shipping is a demo site, not a real client.
- Never mention JCF, police, government, JMMB, banks, eGov or ICTD.
- No mention of Claude, AI or who wrote the ad.
- Plain, confident English for Caribbean small-business owners; a light touch of patois in a hook is fine.
- Do not post, upload or message anything anywhere. Only write files in this folder.
When done, reply with one line: the project, the hook, and the length.
