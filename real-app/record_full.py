# This script records the real KYC app full screen, with a visible mouse pointer, one frame at a time.
import asyncio, json, os, shutil, sys
sys.path.insert(0, "/home/kopi/projects/aitken-ad-kit")
from capture_kyc import FAKE_CAMERA, data_url
from playwright.async_api import async_playwright

APP = "http://127.0.0.1:5310"
ASSETS = "/tmp/claude-1000/-home-kopi/726ac2f3-a51f-4239-8279-79f9ba7c4f39/scratchpad/demo-assets"
OUT = "/tmp/claude-1000/-home-kopi/726ac2f3-a51f-4239-8279-79f9ba7c4f39/scratchpad/rec/frames"
FPS = 30
SCREEN = dict(viewport={"width": 1280, "height": 720}, device_scale_factor=2.25)
WIDE = dict(viewport={"width": 1600, "height": 900}, device_scale_factor=1.8)

CURSOR = """
(() => {
  const add = () => {
    const c = document.createElement('div'); c.id = '__cursor';
    c.innerHTML = '<svg width="28" height="28" viewBox="0 0 24 24"><path d="M4 2l16 9-7 2-3 7z" fill="#111" stroke="#fff" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    c.style.cssText = 'position:fixed;left:640px;top:600px;z-index:99999;pointer-events:none;transform:translate(-4px,-2px)';
    const r = document.createElement('div'); r.id = '__ripple';
    r.style.cssText = 'position:fixed;width:34px;height:34px;margin:-17px 0 0 -17px;border-radius:50%;border:3px solid #22d3ee;z-index:99998;pointer-events:none;opacity:0';
    document.body.append(c, r);
  };
  document.readyState === 'loading' ? addEventListener('DOMContentLoaded', add) : add();
})();
"""

# This class saves frames and remembers where each part of the story starts.
class Recorder:
    def __init__(self):
        shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
        self.count, self.marks, self.page = 0, {}, None

    async def frame(self):
        self.count += 1
        await self.page.screenshot(path=f"{OUT}/f{self.count:05d}.jpg", type="jpeg", quality=92)

    async def hold(self, seconds):
        for _ in range(round(seconds * FPS)):
            await self.frame()

    def mark(self, name):
        self.marks[name] = self.count / FPS

    # This function glides the pointer to an element and clicks it, like a person would.
    async def click(self, selector, seconds=0.7, real_click=True):
        box = await self.page.locator(selector).first.bounding_box()
        tx, ty = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        sx, sy = await self.page.evaluate("[parseFloat(__cursor.style.left), parseFloat(__cursor.style.top)]")
        steps = round(seconds * FPS)
        for i in range(1, steps + 1):
            k = i / steps; k = k * k * (3 - 2 * k)
            await self.page.evaluate(f"__cursor.style.left='{sx + (tx - sx) * k}px';__cursor.style.top='{sy + (ty - sy) * k}px'")
            await self.frame()
        await self.page.evaluate(f"Object.assign(__ripple.style,{{left:'{tx}px',top:'{ty}px',opacity:1}})")
        await self.frame()
        if real_click:
            await self.page.click(selector)
        await self.frame()
        await self.page.evaluate("__ripple.style.opacity=0")

    async def scroll_into(self, selector, seconds=0.9):
        start = await self.page.evaluate("document.querySelector('.portal__scroll')?.scrollTop ?? scrollY")
        end = await self.page.locator(selector).first.evaluate(
            "e => { const s = document.querySelector('.portal__scroll'); const top = e.getBoundingClientRect().top; return (s ? s.scrollTop : scrollY) + top - 70; }")
        steps = round(seconds * FPS)
        for i in range(1, steps + 1):
            k = i / steps; k = k * k * (3 - 2 * k); y = start + (end - start) * k
            await self.page.evaluate(f"const s=document.querySelector('.portal__scroll'); s ? s.scrollTop={y} : scrollTo(0,{y})")
            await self.frame()

async def new_page(browser):
    context = await browser.new_context(**SCREEN)
    await context.add_init_script(FAKE_CAMERA)
    await context.add_init_script(CURSOR)
    page = await context.new_page()
    await page.goto(APP, wait_until="networkidle")
    await page.evaluate("document.fonts.ready")
    return context, page

async def show(page, name, picture, sway):
    await page.evaluate("([n, d, s]) => __showToCamera(n, d, 0.62, s)", [name, data_url(f"{ASSETS}/{picture}"), sway])

async def capture_both(rec, selfie_picture, narrate):
    page = rec.page
    if narrate: rec.mark("start")
    await rec.hold(1.2 if narrate else 0.3)
    await rec.click("#loadMember")
    await page.wait_for_selector("#camera")
    await show(page, "card", "card1.jpg", False)
    await page.evaluate("document.querySelector('#outcome').style.visibility='hidden'")
    await page.wait_for_timeout(700)
    if narrate: rec.mark("card")
    await rec.hold(1.6 if narrate else 0.2)
    await rec.click("#capture")
    await show(page, "selfie", selfie_picture, True)
    await page.wait_for_timeout(500)
    if narrate: rec.mark("selfie")
    await rec.hold(1.8 if narrate else 0.6)
    await rec.click("#capture")
    await rec.hold(0.6)

async def verdict(rec, label):
    page = rec.page
    await page.evaluate("document.querySelector('#outcome').style.visibility='visible'")
    await rec.click("#verify")
    await rec.hold(0.5)
    await page.wait_for_function("document.querySelector('#outcome .readout') || /Could not/.test(document.querySelector('#outcome').innerText)", timeout=180000)
    print(label, (await page.inner_text("#outcome"))[:200].replace("\n", " | "))
    rec.mark(label)
    await rec.scroll_into("#outcome")
    await rec.hold(4.5)

async def review(rec, browser):
    context = await browser.new_context(**WIDE)
    await context.add_init_script(CURSOR)
    rec.page = page = await context.new_page()
    await page.goto(f"{APP}/admin", wait_until="networkidle")
    await page.wait_for_selector("#caselist .case")
    rec.mark("review")
    await rec.hold(1.0)
    await rec.click("#caselist .case >> nth=1")
    await page.wait_for_selector("#reviewer")
    await rec.hold(2.0)
    await page.locator("#reviewer").scroll_into_view_if_needed()
    await rec.hold(0.6)
    await rec.click("#reviewer")
    for ch in "Andre":
        await page.locator("#reviewer").press_sequentially(ch); await rec.frame(); await rec.frame()
    await rec.hold(0.4)
    await rec.click(".btn--approve")
    await page.wait_for_selector("#toast:not([hidden])")
    await rec.hold(2.5)
    await context.close()

async def main():
    rec = Recorder()
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context, rec.page = await new_page(browser)
        await capture_both(rec, "face1.jpg", True)
        await verdict(rec, "confirmed")
        await context.close()
        context, rec.page = await new_page(browser)
        rec.mark("wrong")
        await capture_both(rec, "face3.jpg", False)
        await verdict(rec, "rejected")
        await context.close()
        await review(rec, browser)
        await browser.close()
    rec.mark("end")
    json.dump(rec.marks, open(OUT + "/../marks.json", "w"))
    print(rec.marks)

asyncio.run(main())
