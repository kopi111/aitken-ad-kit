"""Records real screen clips of a website into the ad library.

Each clip is a list of steps. Every step writes one JPEG per video frame (30 fps), so
scrolls and typing come out at a steady speed no matter how slow the screenshots are.

    python3 capture.py <clip-set>     e.g. summer-splash, aitken-shipping
"""
import asyncio
import os
import shutil
import sys
import time

from playwright.async_api import async_playwright

FPS = 30
KIT = os.path.dirname(os.path.abspath(__file__))
DEVICES = {
    "phone": dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True),
    "desktop": dict(viewport={"width": 1440, "height": 900}, device_scale_factor=1),
}

SPLASH = "http://localhost:8765"
SHIP = "http://localhost:5274"

CLIP_SETS = {
    "summer-splash": [
        ("home-scroll", "phone", f"{SPLASH}/", [("hold", 1.0), ("scroll", 0, 2600, 5.0), ("hold", 0.6)]),
        ("home-scroll", "desktop", f"{SPLASH}/", [("hold", 1.0), ("scroll", 0, 2400, 5.0), ("hold", 0.6)]),
        ("services-scroll", "phone", f"{SPLASH}/services.html", [("hold", 0.8), ("scroll", 0, 2200, 4.5), ("hold", 0.5)]),
        ("testimonials-scroll", "phone", f"{SPLASH}/testimonials.html", [("hold", 0.8), ("scroll", 0, 1800, 4.0), ("hold", 0.5)]),
        ("quote-form", "phone", f"{SPLASH}/contact.html", [
            ("scroll_to", "#name", 1.2), ("type", "#name", "Marcia Brown"), ("type", "#email", "marcia@example.com"),
            ("type", "#phone", "876-555-0142"), ("select", "#service", 1), ("type", "#message", "Weekly cleaning for a home pool please"),
            ("check", "#gdpr"), ("hold", 1.0)]),
    ],
    "aitken-shipping": [
        ("home-hero", "phone", f"{SHIP}/", [("hold", 3.0), ("scroll", 0, 1800, 4.0), ("hold", 0.5)]),
        ("home-hero", "desktop", f"{SHIP}/", [("hold", 3.5), ("scroll", 0, 1400, 4.0), ("hold", 0.5)]),
        ("instant-quote", "phone", f"{SHIP}/Quote", [
            ("scroll_to", "#Request_OriginParish", 0.8), ("select", "#Request_OriginParish", "Kingston"),
            ("select", "#Request_DestinationParish", "Saint James"), ("type", "#Request_WeightKg", "4"),
            ("select", "#Request_Service", 1), ("click", "button[type=submit]", 1.0), ("scroll", None, "+1150", 3.0), ("hold", 1.2)]),
        ("track-parcel", "phone", f"{SHIP}/Track", [
            ("scroll_to", "main input", 0.8), ("type", "main input", "AS240001JM"), ("click", "main button[type=submit]", 1.2),
            ("scroll", None, "+900", 3.0), ("hold", 1.2)]),
        ("book-shipment", "phone", f"{SHIP}/Book", [
            ("scroll_to", "#Request_SenderName", 0.8), ("type", "#Request_SenderName", "Andre Campbell"),
            ("type", "#Request_RecipientName", "Keisha Grant"), ("select", "#Request_OriginParish", "Saint Catherine"),
            ("select", "#Request_DestinationParish", "Portland"), ("type", "#Request_WeightKg", "2"),
            ("click", "button[type=submit]", 1.4), ("hold", 2.0)]),
    ],
}


def smoothstep(x):
    return x * x * (3 - 2 * x)


class ClipRecorder:
    def __init__(self, page, out_dir):
        self.page = page
        self.out_dir = out_dir
        self.count = 0

    async def frame(self):
        self.count += 1
        await self.page.screenshot(path=f"{self.out_dir}/f{self.count:05d}.jpg", type="jpeg", quality=90)

    async def hold(self, seconds):
        for _ in range(round(seconds * FPS)):
            await self.frame()

    async def scroll(self, start, end, seconds):
        start = await self.page.evaluate("scrollY") if start is None else start
        end = start + int(end[1:]) if isinstance(end, str) else end
        end = min(end, await self.page.evaluate("document.documentElement.scrollHeight - innerHeight"))
        frames = round(seconds * FPS)
        for i in range(frames):
            y = start + (end - start) * smoothstep(i / (frames - 1))
            await self.page.evaluate(f"window.scrollTo(0,{y})")
            await self.frame()

    async def scroll_to(self, selector, seconds):
        top = await self.page.locator(selector).first.evaluate("e => e.getBoundingClientRect().top + scrollY - innerHeight * 0.3")
        await self.scroll(None, max(0, int(top)), seconds)

    async def type(self, selector, text):
        field = self.page.locator(selector).first
        await field.click()
        await field.fill("")
        await self.hold(0.15)
        for ch in text:
            await field.press_sequentially(ch)
            await self.frame()
        await self.hold(0.3)

    async def select(self, selector, option):
        field = self.page.locator(selector).first
        if isinstance(option, int):
            await field.select_option(index=option)
        else:
            await field.select_option(label=option)
        await self.hold(0.5)

    async def check(self, selector):
        await self.page.locator(selector).first.check()
        await self.hold(0.4)

    async def click(self, selector, seconds):
        await self.page.locator(selector).first.click()
        await self.page.wait_for_load_state("networkidle")
        await self.hold(seconds)

    async def run(self, steps):
        for name, *args in steps:
            await getattr(self, name)(*args)


async def slow_css_animations(page):
    """Screenshots take longer than 1/30 s, so slow the page's animations to match."""
    started = time.perf_counter()
    for _ in range(5):
        await page.screenshot(type="jpeg", quality=90)
    seconds_per_shot = (time.perf_counter() - started) / 5
    cdp = await page.context.new_cdp_session(page)
    await cdp.send("Animation.enable")
    await cdp.send("Animation.setPlaybackRate", {"playbackRate": min(1.0, (1 / FPS) / seconds_per_shot)})


async def record_clip_set(set_name):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for clip, device, url, steps in CLIP_SETS[set_name]:
            out_dir = f"{KIT}/library/{set_name}/{clip}-{device}"
            shutil.rmtree(out_dir, ignore_errors=True)
            os.makedirs(out_dir)
            page = await browser.new_page(**DEVICES[device])
            await page.goto(url, wait_until="networkidle")
            await page.evaluate("document.fonts.ready")
            await slow_css_animations(page)
            recorder = ClipRecorder(page, out_dir)
            await recorder.run(steps)
            print(f"{set_name}/{clip}-{device}: {recorder.count} frames")
            await page.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(record_clip_set(sys.argv[1]))
