"""Turns an ad script (JSON) into a TikTok video, a short cut, a caption file and a preview sheet.

    python3 render.py specs/2026-09-29.json [--out DIR]

See README.md for the script format.
"""
import argparse
import asyncio
import glob
import json
import os
import re
import shutil
import subprocess

from PIL import Image, ImageDraw
from playwright.async_api import async_playwright

FPS = 30
KIT = os.path.dirname(os.path.abspath(__file__))
PILL_TOP, PILL_BOTTOM = 700, 1480
HEADLINE_MAX_CHARS = 48


class SpecError(Exception):
    pass


def frame_count(clip):
    return len(glob.glob(f"{KIT}/library/{clip}/f*.jpg"))


def visible_text(html):
    return re.sub(r"<[^>]+>", "", html)


def validate(spec):
    problems = []
    for i, seg in enumerate(spec["segments"]):
        if seg.get("kind") == "text":
            continue
        frames = frame_count(seg["clip"])
        if frames == 0:
            problems.append(f"segment {i}: clip '{seg['clip']}' not in library")
            continue
        seg["frames"] = frames
        seg["web"] = Image.open(f"{KIT}/library/{seg['clip']}/f00001.jpg").width == 780
        last_second = seg.get("from", 0) + seg["dur"]
        if last_second * FPS > frames + 1:
            problems.append(f"segment {i}: needs {last_second:.1f}s but '{seg['clip']}' is {frames / FPS:.1f}s")
        if len(visible_text(seg.get("head", ""))) > HEADLINE_MAX_CHARS:
            problems.append(f"segment {i}: headline longer than {HEADLINE_MAX_CHARS} characters")
        for pill in seg.get("pills", []):
            if not PILL_TOP <= pill["y"] <= PILL_BOTTOM:
                problems.append(f"segment {i}: pill '{pill['text']}' y={pill['y']} outside {PILL_TOP}-{PILL_BOTTOM}")
            if pill["at"] >= seg["dur"]:
                problems.append(f"segment {i}: pill '{pill['text']}' appears after the segment ends")
    total = sum(s["dur"] for s in spec["segments"]) + spec["end"]["dur"]
    if not 12 <= total <= 32:
        problems.append(f"total length {total:.1f}s; keep it 12-32s")
    if problems:
        raise SpecError("\n".join(problems))
    return total


async def render_frames(spec, frames_dir):
    os.makedirs(frames_dir, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        await page.goto(f"file://{KIT}/scene.html")
        await page.evaluate("document.fonts.ready")
        total = await page.evaluate("s => setup(s)", spec)
        for i in range(round(total * FPS)):
            await page.evaluate(f"render({i / FPS})")
            await page.screenshot(path=f"{frames_dir}/f{i + 1:05d}.jpg", type="jpeg", quality=94)
        await browser.close()


def encode(frames_dir, out_path, trims=None):
    cmd = ["ffmpeg", "-v", "error", "-y", "-framerate", str(FPS), "-i", f"{frames_dir}/f%05d.jpg",
           "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    if trims:
        parts = "".join(f"[0:v]trim={a:.3f}:{b:.3f},setpts=PTS-STARTPTS[v{i}];" for i, (a, b) in enumerate(trims))
        joined = "".join(f"[v{i}]" for i in range(len(trims)))
        cmd += ["-filter_complex", f"{parts}{joined}concat=n={len(trims)}:v=1[v]", "-map", "[v]", "-map", "1:a"]
    cmd += ["-shortest", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)


def short_cut_ranges(spec):
    starts, t = [], 0.0
    for seg in spec["segments"]:
        starts.append((t, t + seg["dur"]))
        t += seg["dur"]
    ranges = [starts[i] for i in spec.get("short", [])]
    return ranges + [(t, t + min(2.6, spec["end"]["dur"]))] if ranges else None


def preview_sheet(spec, frames_dir, out_path):
    """Two frames from inside each segment plus the end card, so cut frames never mislead."""
    frames = sorted(glob.glob(f"{frames_dir}/*.jpg"))
    times, start = [], 0.0
    for seg in spec["segments"] + [spec["end"]]:
        times += [start + seg["dur"] * 0.35, start + seg["dur"] * 0.85]
        start += seg["dur"]
    sheet = Image.new("RGB", (len(times) * 270, 480), "white")
    for i, t in enumerate(times):
        thumb = Image.open(frames[min(len(frames) - 1, int(t * FPS))]).resize((270, 480))
        ImageDraw.Draw(thumb).text((6, 6), f"{t:.1f}s", fill="yellow")
        sheet.paste(thumb, (i * 270, 0))
    sheet.save(out_path)


def write_caption(spec, path):
    with open(path, "w") as f:
        f.write(f"{spec['title']}\nAdd a trending sound in TikTok before posting (video is silent).\n\n")
        f.write(f"CAPTION\n{spec['caption'].strip()}\n\nHASHTAGS\n{' '.join(spec['hashtags'])}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("spec")
    parser.add_argument("--out")
    args = parser.parse_args()
    spec = json.load(open(args.spec))
    total = validate(spec)
    out = args.out or f"{KIT}/out/{spec['id']}"
    frames_dir = f"{KIT}/out/.frames-{spec['id']}"
    shutil.rmtree(frames_dir, ignore_errors=True)
    os.makedirs(out, exist_ok=True)
    asyncio.run(render_frames(spec, frames_dir))
    encode(frames_dir, f"{out}/{spec['id']}.mp4")
    trims = short_cut_ranges(spec)
    if trims:
        encode(frames_dir, f"{out}/{spec['id']}-short.mp4", trims)
    write_caption(spec, f"{out}/{spec['id']}-caption.txt")
    preview_sheet(spec, frames_dir, f"{KIT}/out/{spec['id']}-preview.png")
    shutil.rmtree(frames_dir)
    print(f"OK {total:.1f}s -> {out}\npreview: {KIT}/out/{spec['id']}-preview.png")


if __name__ == "__main__":
    try:
        main()
    except SpecError as e:
        raise SystemExit(f"SPEC PROBLEMS:\n{e}")
