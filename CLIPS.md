# Clip library

Real screen recordings, 30 fps, one JPEG per frame in `library/<project>/<clip>/`.
"device" is what to put in the ad script: `phone` for phone clips, `laptop` for desktop clips.
Times below are seconds from the start of the clip; use them for `from` and pill `at` values.

## money-path — Money Path (kopi's own Flutter budgeting app; say "we built", never "for a client")

Facts you may state: PIN lock with optional fingerprint, database encrypted on the phone, works with no
internet (nothing leaves the phone), savings goals with on-track/behind, monthly budget with category
limits and overspend alerts, month-end summary, reports compared to last month. Android app.
Amounts on screen are demo data in JMD-style dollars.

| clip | device | length | what happens |
|---|---|---|---|
| money-path/lock-unlock | phone | 3.7s | PIN lock screen; dots fill 1.0–2.5; unlocks into Today at ~2.8 |
| money-path/today-scroll | phone | 7.5s | Today: "Left for September $38,710", red/amber limit alerts; scrolls down to goals and bills 2.5–4.5, back up 5.5–6.5 |
| money-path/log-spending | phone | 6.0s | Spend sheet opens 0–0.8; types $1,500 1.0–2.5; taps "Eating out" ~3.6; back on Today showing $37,210 and a new "limit reached" alert from ~4.0 |
| money-path/goals-scroll | phone | 5.6s | Goals: Christmas and School fees covers with "Behind" badges; scrolls 1.9–2.9 to Car fund "On track" |
| money-path/month-view | phone | 3.3s | Month page: money in, spent, into goals, left; "Carry to October" button |
| money-path/reports-scroll | phone | 4.5s | Reports: spending-by-category bars; scrolls ~0.9–1.9 to "Against August" comparison |
| money-path/today-static | phone | 2.3s | Today screen, still |

## summer-splash — Summer Splash Pool Services website (real client, Florida pool company)

Facts you may state: we built their website; mobile-first; services pages; reviews on the page; free-quote
request form. The site shows the client's own numbers (500+ pools, 15+ years); never repeat them as
Aitken Technology's numbers.

| clip | device | length | what happens |
|---|---|---|---|
| summer-splash/home-scroll-phone | phone | 6.6s | Hero "Dive into Crystal Clear Pool Care" 0–1; scrolls through stats, services, why choose us, reviews |
| summer-splash/home-scroll-desktop | laptop | 6.6s | Same page on desktop: hero 0–1, then services photos, why choose us, reviews |
| summer-splash/services-scroll-phone | phone | 5.8s | Services page: Commercial/Residential tabs, pool management, maintenance, renovation, emergency repairs with photos |
| summer-splash/testimonials-scroll-phone | phone | 5.3s | Testimonials page: star reviews with names |
| summer-splash/quote-form-phone | phone | 7.5s | Free-quote form filled in live: name ~0.8, email, phone, service, message, consent box ~6.5 (not submitted) |

## aitken-shipping — Aitken Shipping courier website (demo site we built to show what a courier site can do)

It is NOT a real client. Say "a courier website we built" or "imagine this for your business"; never
"for a client", never imply it is a real company taking orders.

| clip | device | length | what happens |
|---|---|---|---|
| aitken-shipping/home-hero-phone | phone | 7.5s | Hero "Put your parcel on the board" with animated route map 0–3; then scrolls lanes and services |
| aitken-shipping/home-hero-desktop | laptop | 8.0s | Desktop hero with the track console and route map 0–3.5; scrolls to "Three moves, no surprises" |
| aitken-shipping/instant-quote-phone | phone | 8.0s | Picks Kingston → Saint James 0.8–2.3, weight 4 kg, "Calculate manifest" ~4.3, scrolls to the itemised price, total $2,040.00 visible ~7.0 |
| aitken-shipping/track-parcel-phone | phone | 7.0s | Types AS240001JM 0.8–1.6, taps Track; result card "In transit" ~2.8; journey log 3.5–5.4; footer after ~5.6 (avoid) |
| aitken-shipping/book-shipment-phone | phone | 7.4s | Fills sender, recipient, parishes, weight 0.8–4.1; "Booking confirmed" with waybill number from ~5.5 |
