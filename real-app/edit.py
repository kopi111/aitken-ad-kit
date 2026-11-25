# This script cuts the full-screen recording into a narrated ad, in 16:9 and 9:16, with subtitles.
import json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W_DIR = "/tmp/claude-1000/-home-kopi/726ac2f3-a51f-4239-8279-79f9ba7c4f39/scratchpad/rec"
REAL = W_DIR + "/../real"
FPS = 30
marks = json.load(open(W_DIR + "/marks.json"))
words = json.load(open(W_DIR + "/words.json"))
voice = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f"{W_DIR}/s{i}.mp3"],
         capture_output=True, text=True).stdout) for i in range(9)]
cuts = [marks[k] for k in ["start", "card", "selfie", "confirmed", "wrong", "rejected", "review", "end"]]
RECORDED = [(cuts[i], cuts[i + 1]) for i in range(7)]
REVIEW_START = marks["review"]
SUB_FONT = {"wide": ImageFont.truetype(REAL + "/Inter-ExtraBold.ttf", 56), "tall": ImageFont.truetype(REAL + "/Inter-ExtraBold.ttf", 60)}
STICKER = ImageFont.truetype(REAL + "/Inter-Bold.ttf", 34)
LAYOUT = {"wide": dict(size=(1920, 1080), sub_y=940, sticker=(1458, 40)), "tall": dict(size=(1080, 1920), sub_y=1590, sticker=(48, 190))}

# This function returns one recorded frame by its time in the recording.
def recorded(seconds):
    return cv2.imread(f"{W_DIR}/frames/f{max(1, min(int(seconds * FPS) + 1, int(cuts[-1] * FPS))):05d}.jpg")

# This function frames the recording for a vertical screen, following the action on the review page.
def tall_view(frame, seconds):
    if seconds < REVIEW_START:
        x0 = 1315
    else:
        k = min(max((seconds - REVIEW_START - 2.0) / 1.0, 0), 1); k = k * k * (3 - 2 * k)
        x0 = int(700 + (1611 - 700) * k)
    crop = cv2.resize(frame[:, x0:x0 + 1150], (1080, 1521), interpolation=cv2.INTER_AREA)
    canvas = np.zeros((1920, 1080, 3), np.uint8); canvas[:] = (24, 14, 10)
    canvas[160:1681] = crop
    return canvas

def wide_view(frame, seconds):
    return cv2.resize(frame, (1920, 1080), interpolation=cv2.INTER_AREA)

# This function shows an app-style card (who it's for, or the offer) on the brand background.
def card_view(image_path, shape):
    card = cv2.imread(image_path)[60:1460, 20:760]
    w, h = shape
    height = int(h * (0.86 if h > w else 0.9)); width = int(card.shape[1] * height / card.shape[0])
    canvas = np.zeros((h, w, 3), np.float32)
    ys = np.linspace(0, 1, h)[:, None]; xs = np.linspace(0, 1, w)[None, :]
    canvas[..., 0] = 24 + 120 * np.exp(-((xs - 0.85) ** 2 + (ys - 0.1) ** 2) * 6)
    canvas[..., 1] = 11 + 20 * np.exp(-((xs - 0.1) ** 2 + (ys - 0.9) ** 2) * 6)
    canvas[..., 2] = 7 + 70 * np.exp(-((xs - 0.85) ** 2 + (ys - 0.1) ** 2) * 6)
    canvas = canvas.astype(np.uint8)
    x, y = (w - width) // 2, (h - height) // 2 - (40 if h > w else 30)
    canvas[y:y + height, x:x + width] = cv2.resize(card, (width, height), interpolation=cv2.INTER_AREA)
    return canvas

def who_path(t):
    triggers = ["lenders", "credit", "car", "money", "landlords", "online"]
    shown = sum(1 for w in words[7] if w[2].lower().strip(",.") in triggers and w[0] <= t)
    return f"{REAL}/who{shown}.png"

def subtitle_groups(scene_words):
    groups, current = [], []
    for word in scene_words:
        current.append(word)
        if len(current) == 4 or word[2].endswith((".", "?", ",", ":")):
            groups.append(current); current = []
    return groups + ([current] if current else [])

# This function draws the subtitle with the spoken word in cyan, plus the offer sticker.
def overlay(image, scene_words, t, form):
    lay = LAYOUT[form]; font = SUB_FONT[form]
    draw = ImageDraw.Draw(image)
    sx, sy = lay["sticker"]
    draw.rounded_rectangle([sx, sy, sx + 422, sy + 64], 32, fill=(124, 58, 237, 235))
    draw.text((sx + 24, sy + 10), "30% OFF · ends 15 Dec", font=STICKER, fill="white")
    live = next((g for g in subtitle_groups(scene_words) if g[0][0] - 0.05 <= t <= g[-1][1] + 0.25), None)
    if not live:
        return
    spoken = [w for w in live if w[0] - 0.05 <= t]
    widths = [draw.textlength(w[2] + " ", font=font) for w in live]
    x = (lay["size"][0] - sum(widths)) / 2; y = lay["sub_y"]
    draw.rounded_rectangle([x - 24, y - 14, x + sum(widths) - 8 + 24, y + 82], 24, fill=(8, 11, 24, 215))
    for w, width in zip(live, widths):
        draw.text((x, y), w[2], font=font, fill=(34, 211, 238) if spoken and w is spoken[-1] else (255, 255, 255))
        x += width

def finish(frame, scene_words, t, form):
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", image.size); overlay(layer, scene_words, t, form)
    return cv2.cvtColor(np.asarray(Image.alpha_composite(image, layer).convert("RGB")), cv2.COLOR_RGB2BGR).tobytes()

def encoder(path, size):
    return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{size[0]}x{size[1]}", "-r", str(FPS),
                             "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)

def main():
    outs = {"wide": encoder(W_DIR + "/wide-video.mp4", (1920, 1080)), "tall": encoder(W_DIR + "/tall-video.mp4", (1080, 1920))}
    starts, clock = [], 0.0
    for i in range(9):
        starts.append(clock)
        if i < 7:
            a, b = RECORDED[i]; rec_len = b - a
            length = max(rec_len, voice[i] + 0.4)
            lead = length - rec_len if i == 0 else 0
        else:
            length = voice[i] + (0.5 if i == 7 else 1.8)
        for n in range(round(length * FPS)):
            t = n / FPS
            if i < 7:
                seconds = a + min(max(t - lead, 0), rec_len - 1 / FPS)
                frame = recorded(seconds)
                views = {"wide": wide_view(frame, seconds), "tall": tall_view(frame, seconds)}
            else:
                path = who_path(t) if i == 7 else REAL + "/offer.png"
                views = {"wide": card_view(path, (1920, 1080)), "tall": card_view(path, (1080, 1920))}
            for form, process in outs.items():
                process.stdin.write(finish(views[form], words[i], t, form))
        clock += length
    for process in outs.values():
        process.stdin.close(); process.wait()
    json.dump(starts, open(W_DIR + "/starts.json", "w"))
    print("length", round(clock, 2), [round(s, 2) for s in starts])

main()
