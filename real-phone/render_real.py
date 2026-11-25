# This script builds the "real" KYC ad: app recordings on a hand-held phone photo, Ava's voice, word-by-word subtitles.
import json, subprocess, glob
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W_DIR = "/tmp/claude-1000/-home-kopi/726ac2f3-a51f-4239-8279-79f9ba7c4f39/scratchpad/real"
STOCK = W_DIR + "/../stock/"
LIB = "/home/kopi/projects/aitken-ad-kit/library/kyc/"
OUT = W_DIR + "/kyc-real.mp4"
FPS, WIDTH, HEIGHT = 30, 1080, 1920
CROP_X, CROP_Y, SCALE = 315, 300, 0.8
SCREEN = np.float32([[650, 859], [1328, 863], [1321, 2319], [648, 2319]])
GAP, TAIL = 0.45, 1.6

# This function loads the hand photo and the screen mask, cropped to the 9:16 frame.
def load_backdrop():
    photo = cv2.imread(STOCK + "hand-holds-a-cell-phone-over-a-black-background.jpg")
    mask = cv2.imread(STOCK + "screenmask.png", 0)
    mask = cv2.GaussianBlur(cv2.dilate(mask, np.ones((5, 5), np.uint8)), (5, 5), 0)
    box = (slice(CROP_Y, CROP_Y + 2400), slice(CROP_X, CROP_X + 1350))
    size = (WIDTH, HEIGHT)
    return cv2.resize(photo[box], size, interpolation=cv2.INTER_AREA), cv2.resize(mask[box], size)[..., None] / 255.0

# This function puts one app screen onto the phone in the photo.
def phone_frame(backdrop, mask, screen_image):
    h, w = screen_image.shape[:2]
    quad = (SCREEN - [CROP_X, CROP_Y]) * SCALE
    warp = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), np.float32(quad))
    placed = cv2.warpPerspective(screen_image, warp, (WIDTH, HEIGHT), flags=cv2.INTER_AREA)
    placed = (placed * 0.96).astype(np.float32)
    return (backdrop * (1 - mask) + placed * mask).astype(np.uint8)

# This function shows the laptop recording tilted slightly on the dark backdrop.
def laptop_frame(backdrop, screen_image):
    shade = np.linspace(38, 12, HEIGHT, dtype=np.float32)[:, None, None]
    dark = np.broadcast_to(shade * np.float32([1.0, 0.8, 0.75]), (HEIGHT, WIDTH, 3)).astype(np.uint8)
    h, w = screen_image.shape[:2]
    quad = np.float32([[70, 560], [1010, 600], [1010, 1190], [70, 1230]])
    warp = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), quad)
    placed = cv2.warpPerspective(screen_image, warp, (WIDTH, HEIGHT), flags=cv2.INTER_AREA)
    area = cv2.warpPerspective(np.ones((h, w), np.float32), warp, (WIDTH, HEIGHT))[..., None]
    return (dark * (1 - area) + placed * area).astype(np.uint8)

# This function slowly pushes the camera in, so still moments still feel alive.
def push_in(frame, progress, centre_y=1030):
    zoom = 1.0 + 0.05 * progress
    cw, ch = WIDTH / zoom, HEIGHT / zoom
    x0 = (WIDTH - cw) / 2
    y0 = min(max(centre_y - ch / 2, 0), HEIGHT - ch)
    crop = frame[int(y0):int(y0 + ch), int(x0):int(x0 + cw)]
    return cv2.resize(crop, (WIDTH, HEIGHT), interpolation=cv2.INTER_LINEAR)

# This function lists the frame files of one recorded clip.
def clip_frames(name):
    return sorted(glob.glob(LIB + name + "/f*.jpg"))

# This function picks the clip frame for a moment in the scene, holding the last frame when the clip runs out.
def frame_at(files, start_second, t):
    index = min(int((start_second + t) * FPS), len(files) - 1)
    return cv2.imread(files[index])

FONT = ImageFont.truetype(W_DIR + "/Inter-ExtraBold.ttf", 62)
STICKER_FONT = ImageFont.truetype(W_DIR + "/Inter-Bold.ttf", 34)

# This function groups the spoken words into short subtitle lines of up to four words.
def subtitle_groups(words):
    groups, current = [], []
    for word in words:
        current.append(word)
        if len(current) == 4 or word[2].endswith((".", "?", ",")):
            groups.append(current); current = []
    return groups + ([current] if current else [])

# This function draws the subtitle line with the word being spoken in cyan.
def draw_subtitle(image, words, t, y):
    groups = subtitle_groups(words)
    live = next((g for g in groups if g[0][0] - 0.05 <= t <= g[-1][1] + 0.25), None)
    if not live:
        return
    draw = ImageDraw.Draw(image)
    texts = [w[2] for w in live]
    widths = [draw.textlength(s + " ", font=FONT) for s in texts]
    x = (WIDTH - sum(widths)) / 2
    pad = 22
    draw.rounded_rectangle([x - pad, y - 14, x + sum(widths) - 10 + pad, y + 84], 24, fill=(8, 11, 24, 200))
    spoken = [w for w in live if w[0] - 0.05 <= t]
    current = spoken[-1] if spoken else None
    for word, text, width in zip(live, texts, widths):
        colour = (34, 211, 238) if word is current else (255, 255, 255)
        draw.text((x, y), text, font=FONT, fill=colour)
        x += width

# This function draws the small offer sticker in the top corner.
def draw_sticker(image):
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle([48, 190, 470, 254], 32, fill=(124, 58, 237, 235))
    draw.text((72, 200), "30% OFF · ends 15 Dec", font=STICKER_FONT, fill="white")

# This function turns a "who it's for" reveal count into the matching screen.
def who_screen(words, t):
    triggers = ["lenders", "credit", "car", "money", "landlords", "online"]
    shown = sum(1 for word in words if word[2].lower().strip(",.") in triggers and word[0] <= t)
    return cv2.imread(f"{W_DIR}/who{shown}.png")

def main():
    backdrop, mask = load_backdrop()
    words = json.load(open(W_DIR + "/words.json"))
    voice_lengths = [float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                      f"{W_DIR}/s{i}.mp3"], capture_output=True, text=True).stdout) for i in range(8)]
    card, selfie = clip_frames("capture-card-phone"), clip_frames("capture-selfie-phone")
    confirmed, rejected, review = clip_frames("result-confirmed-phone"), clip_frames("result-rejected-phone"), clip_frames("review-desktop")
    scenes = [
        lambda t: phone_frame(backdrop, mask, cv2.imread(card[0])),
        lambda t: phone_frame(backdrop, mask, frame_at(card, 0, t * len(card) / FPS / (voice_lengths[1] + GAP))),
        lambda t: phone_frame(backdrop, mask, frame_at(selfie, 0, t * len(selfie) / FPS / (voice_lengths[2] + GAP))),
        lambda t: phone_frame(backdrop, mask, frame_at(confirmed, 0, t)),
        lambda t: phone_frame(backdrop, mask, frame_at(rejected, 2.0, t)),
        lambda t: laptop_frame(backdrop, frame_at(review, 0, t)),
        lambda t: phone_frame(backdrop, mask, who_screen(words[6], t)),
        lambda t: phone_frame(backdrop, mask, cv2.imread(W_DIR + "/offer.png")),
    ]
    encoder = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{WIDTH}x{HEIGHT}",
                                "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", W_DIR + "/video-only.mp4"],
                               stdin=subprocess.PIPE)
    starts, clock = [], 0.0
    for i, scene in enumerate(scenes):
        length = voice_lengths[i] + (TAIL if i == len(scenes) - 1 else GAP)
        starts.append(clock)
        for n in range(round(length * FPS)):
            t = n / FPS
            frame = push_in(scene(t), t / length, 900 if i == 5 else 1030)
            image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).convert("RGBA")
            overlay = Image.new("RGBA", image.size)
            draw_sticker(overlay)
            draw_subtitle(overlay, words[i], t, 1420 if i == 5 else 1300)
            image = Image.alpha_composite(image, overlay).convert("RGB")
            encoder.stdin.write(cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR).tobytes())
        clock += length
    encoder.stdin.close(); encoder.wait()
    json.dump(starts, open(W_DIR + "/starts.json", "w"))
    print("video", round(clock, 2), "s; scene starts", [round(s, 2) for s in starts])

main()
