"""Records the KYC ad clips from a neutral demo copy of the ID check, never the JCF-branded app.

    python3 capture_kyc.py <folder holding card1.jpg, face1.jpg, face3.jpg>

The demo must be running on :5310 with invented people only. The camera is a canvas showing the
sample card or the demo face, but every verdict on screen comes from the real checking engine.
"""
import asyncio
import base64
import os
import shutil
import sys

from playwright.async_api import async_playwright

from capture import KIT, ClipRecorder

DEMO = "http://127.0.0.1:5310"
PHONE = dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
DESKTOP = dict(viewport={"width": 960, "height": 600}, device_scale_factor=2)
CHECK_TIMEOUT_MS = 120_000
MAX_TAKES = 1

# Replaces the browser camera with a canvas, so the sample card and demo faces can be "photographed".
FAKE_CAMERA = """
(() => {
  const canvas = document.createElement('canvas'); canvas.width = 1280; canvas.height = 960;
  const ctx = canvas.getContext('2d');
  const pictures = {};
  window.__showToCamera = async (name, dataUrl, scale, sway) => {
    if (!pictures[name]) { const i = new Image(); i.src = dataUrl; await i.decode(); pictures[name] = i; }
    window.__shot = { picture: pictures[name], scale, sway };
  };
  const draw = () => {
    const s = window.__shot; ctx.fillStyle = '#4b5563'; ctx.fillRect(0, 0, 1280, 960);
    if (s) {
      const h = 960 * s.scale, w = h * s.picture.width / s.picture.height;
      const dx = s.sway ? Math.sin(performance.now() / 700) * 5 : 0;
      ctx.drawImage(s.picture, 640 - w / 2 + dx, 480 - h / 2, w, h);
    }
    requestAnimationFrame(draw);
  };
  draw();
  const stream = canvas.captureStream(30);
  navigator.mediaDevices.getUserMedia = async () => stream;
})();
"""


def data_url(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


def clip_dir(name):
    path = f"{KIT}/library/kyc/{name}"
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)
    return path


async def wait_for_verdict(page):
    await page.wait_for_function(
        "document.querySelector('#outcome .readout') || /Could not/.test(document.querySelector('#outcome').innerText)",
        timeout=CHECK_TIMEOUT_MS)


async def run_check(browser, assets, selfie, take_clips):
    context = await browser.new_context(**PHONE)
    await context.add_init_script(FAKE_CAMERA)
    page = await context.new_page()
    await page.goto(DEMO, wait_until="networkidle")
    await page.evaluate("document.fonts.ready")
    await page.click("#loadMember")
    await page.wait_for_selector("#camera")
    await page.evaluate("([d]) => __showToCamera('card', d, 0.62, false)", [data_url(f"{assets}/card1.jpg")])
    await page.evaluate("scrollTo(0,0)")
    await page.wait_for_timeout(600)

    # The blur note is advisory and comes from the canvas camera, so it stays out of the capture shots.
    await page.evaluate("document.querySelector('#outcome').style.visibility = 'hidden'")
    recorder = ClipRecorder(page, clip_dir("capture-card-phone") if take_clips else "/dev/null")
    if take_clips:
        await recorder.hold(1.8)
    await page.click("#capture")
    await page.evaluate("([d]) => __showToCamera('selfie', d, 0.62, true)", [data_url(f"{assets}/{selfie}")])
    await page.evaluate("scrollTo(0,0)")
    await page.wait_for_timeout(500)
    if take_clips:
        await recorder.hold(0.8)
        recorder = ClipRecorder(page, clip_dir("capture-selfie-phone"))
        await recorder.hold(1.8)
    await page.click("#capture")
    await page.evaluate("scrollTo(0,0)")
    await page.wait_for_timeout(300)
    if take_clips:
        await recorder.hold(0.9)
    return context, page


async def record_verdict(page, name):
    await page.evaluate("document.querySelector('#outcome').style.visibility = 'visible'")
    await page.click("#verify")
    await wait_for_verdict(page)
    print(name, (await page.inner_text("#outcome"))[:240].replace("\n", " | "))
    await page.evaluate("document.querySelector('#outcome').scrollIntoView({block:'start'}); scrollBy(0,-24)")
    await page.wait_for_timeout(300)
    recorder = ClipRecorder(page, clip_dir(name))
    await recorder.hold(5.0)


async def glide_decision_into_view(recorder, page, seconds):
    """Scroll whichever pane holds the decision form, one video frame at a time."""
    frames = round(seconds * 30)
    for i in range(frames):
        await page.evaluate("""k => {
          let box = document.querySelector('#reviewer');
          while (box && box.scrollHeight <= box.clientHeight + 4) box = box.parentElement;
          if (box) box.scrollTop = (box.scrollHeight - box.clientHeight) * k;
        }""", (i / (frames - 1)) ** 2 * (3 - 2 * i / (frames - 1)))
        await recorder.frame()


async def record_review(browser):
    context = await browser.new_context(**DESKTOP)
    page = await context.new_page()
    await page.goto(f"{DEMO}/admin", wait_until="networkidle")
    await page.wait_for_selector("#caselist .case")
    recorder = ClipRecorder(page, clip_dir("review-desktop"))
    await recorder.hold(1.0)
    await page.locator("#caselist .case").first.click()
    await page.wait_for_selector("#reviewer")
    await page.wait_for_timeout(500)
    await recorder.hold(1.4)
    await glide_decision_into_view(recorder, page, 1.4)
    await recorder.type("#reviewer", "Andre")
    await page.click(".btn--approve")
    await page.wait_for_selector("#toast:not([hidden])")
    await recorder.hold(1.6)
    await context.close()


async def main(assets):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for _ in range(MAX_TAKES):
            context, page = await run_check(browser, assets, "face3.jpg", False)
            await record_verdict(page, "result-rejected-phone")
            reason = await page.inner_text("#outcome")
            await context.close()
            if "not close enough" in reason:
                break
        context, page = await run_check(browser, assets, "face1.jpg", True)
        await record_verdict(page, "result-confirmed-phone")
        await context.close()
        await record_review(browser)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1]))
