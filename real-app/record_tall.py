# This script records the real KYC app in a tall window, so the TikTok video is filled edge to edge.
import asyncio, json, os, shutil, sys
sys.path.insert(0, "/tmp/claude-1000/-home-kopi/726ac2f3-a51f-4239-8279-79f9ba7c4f39/scratchpad/rec")
sys.path.insert(0, "/home/kopi/projects/aitken-ad-kit")
from capture_kyc import FAKE_CAMERA, data_url
import record_full as base
from playwright.async_api import async_playwright

base.OUT = OUT = "/tmp/claude-1000/-home-kopi/726ac2f3-a51f-4239-8279-79f9ba7c4f39/scratchpad/rec/frames-tall"
TALL = dict(viewport={"width": 540, "height": 960}, device_scale_factor=2)
FIND_SCROLLER = """e => { let b = e.parentElement;
  while (b && !(b.scrollHeight > b.clientHeight + 4 && /(auto|scroll)/.test(getComputedStyle(b).overflowY))) b = b.parentElement;
  return b || document.scrollingElement; }"""

# This class adds smooth scrolling that follows the action down the tall page.
class TallRecorder(base.Recorder):
    async def glide(self, selector, offset=24, seconds=0.8):
        element = self.page.locator(selector).first
        start, end = await element.evaluate(f"""e => {{ const b = ({FIND_SCROLLER})(e);
            const top = e.getBoundingClientRect().top - (b === document.scrollingElement ? 0 : b.getBoundingClientRect().top);
            window.__scroller = b; return [b.scrollTop, Math.max(0, Math.min(b.scrollTop + top - {offset}, b.scrollHeight - b.clientHeight))]; }}""")
        steps = round(seconds * base.FPS)
        for i in range(1, steps + 1):
            k = i / steps; k = k * k * (3 - 2 * k)
            await self.page.evaluate(f"__scroller.scrollTop = {start + (end - start) * k}")
            await self.frame()

    async def click(self, selector, seconds=0.7, real_click=True):
        box = await self.page.locator(selector).first.bounding_box()
        if box["y"] < 60 or box["y"] + box["height"] > 900:
            await self.glide(selector, offset=520, seconds=0.6)
        await super().click(selector, seconds, real_click)

async def new_page(browser, path=""):
    context = await browser.new_context(**TALL)
    await context.add_init_script(FAKE_CAMERA)
    await context.add_init_script(base.CURSOR.replace("left:640px;top:600px", "left:300px;top:760px"))
    page = await context.new_page()
    await page.goto(base.APP + path, wait_until="networkidle")
    await page.evaluate("document.fonts.ready")
    return context, page

async def capture_both(rec, selfie, narrate):
    page = rec.page
    if narrate:
        rec.mark("start"); await rec.hold(1.0); await rec.glide(".sheet", 16, 1.0); await rec.hold(0.4)
    else:
        await rec.glide(".sheet", 16, 0.4)
    await rec.click("#loadMember")
    await page.wait_for_selector("#camera")
    await base.show(page, "card", "card1.jpg", False)
    await page.evaluate("document.querySelector('#outcome').style.visibility='hidden'")
    await page.wait_for_timeout(700)
    if narrate: rec.mark("card")
    await rec.glide("#memberCard", 16, 0.7)
    await rec.hold(1.4 if narrate else 0.2)
    await rec.click("#capture")
    await base.show(page, "selfie", selfie, True)
    await page.wait_for_timeout(500)
    if narrate: rec.mark("selfie")
    await rec.glide("#cameraBox", 120, 0.6)
    await rec.hold(1.6 if narrate else 0.5)
    await rec.click("#capture")
    await rec.hold(0.5)

async def verdict(rec, label):
    page = rec.page
    await page.evaluate("document.querySelector('#outcome').style.visibility='visible'")
    await rec.click("#verify")
    await rec.hold(0.4)
    await page.wait_for_function("document.querySelector('#outcome .readout') || /Could not/.test(document.querySelector('#outcome').innerText)", timeout=180000)
    print(label, (await page.inner_text("#outcome"))[:120].replace("\n", " | "))
    rec.mark(label)
    await rec.glide("#outcome", 30, 0.9)
    await rec.hold(4.2)

async def review(rec, browser):
    context, rec.page = await new_page(browser, "/admin")
    page = rec.page
    await page.wait_for_selector("#caselist .case")
    rec.mark("review")
    await rec.glide("#caselist", 140, 0.8)
    await rec.hold(0.4)
    await rec.click("#caselist .case >> nth=1")
    await page.wait_for_selector("#reviewer")
    await rec.glide("#detail", 20, 0.9)
    await rec.hold(1.6)
    await rec.glide("#detail .panel >> nth=1", 20, 1.0)
    await rec.hold(1.6)
    await rec.glide(".decision", 200, 0.9)
    await rec.click("#reviewer")
    for ch in "Andre":
        await page.locator("#reviewer").press_sequentially(ch); await rec.frame(); await rec.frame()
    await rec.hold(0.3)
    await rec.click(".btn--approve")
    await page.wait_for_selector("#toast:not([hidden])")
    await rec.hold(2.4)
    await context.close()

async def main():
    rec = TallRecorder()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context, rec.page = await new_page(browser)
        await capture_both(rec, "face1.jpg", True); await verdict(rec, "confirmed"); await context.close()
        context, rec.page = await new_page(browser)
        rec.mark("wrong")
        await capture_both(rec, "face3.jpg", False); await verdict(rec, "rejected"); await context.close()
        await review(rec, browser)
        await browser.close()
    rec.mark("end")
    json.dump(rec.marks, open(OUT + "/../marks-tall.json", "w"))
    print(rec.marks)

asyncio.run(main())
