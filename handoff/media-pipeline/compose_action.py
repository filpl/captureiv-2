"""Action cut of the Capture IV product tour.

Full-bleed product, fast punch-in zooms, whip-blur transitions, kinetic
titles on charcoal, and a full-frame cut to the same flight clip the viewer
is playing. Writes JPEG frames to vframes_action/ for ffmpeg.
"""
import json, os, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
REC, OUT = S + '/rec', S + '/vframes_action'
CLIP = '/home/user/uplat/static/uploads/demo-flight-podium.mp4'
FPS, W, H = 30, 1920, 1080
SRC_W, SRC_H = 1600, 900
F = '/usr/share/fonts/opentype/inter/'
font = lambda name, size: ImageFont.truetype(F + name, size)
CHAR = (23, 25, 29)
BLUE = (37, 99, 235)

os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT):
    os.remove(os.path.join(OUT, f))

data = json.load(open(REC + '/frames.json'))
frames = data['frames']; t0 = frames[0]['t']
R = np.array([fr['t'] - t0 for fr in frames])
M = {m['name']: m['t'] - t0 for m in data['markers']}
_cache = {}
def load(i):
    if i not in _cache:
        if len(_cache) > 40: _cache.clear()
        _cache[i] = Image.open(frames[i]['file']).convert('RGB')
    return _cache[i]

def src(r):
    """Blend the two captured frames around recording time r (smooths low capture fps)."""
    i = int(np.clip(np.searchsorted(R, r) - 1, 0, len(R) - 1))
    j = min(i + 1, len(R) - 1)
    if j == i or R[j] - R[i] < 1e-6: return load(i)
    k = float(np.clip((r - R[i]) / (R[j] - R[i]), 0, 1))
    return load(i) if k < .5 else load(j)

def ease_out(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 4
def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def cam_frame(img, cx, cy, z):
    w, h = SRC_W / z, SRC_H / z
    x0 = min(max(cx - w / 2, 0), SRC_W - w); y0 = min(max(cy - h / 2, 0), SRC_H - h)
    return img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))

def lerp_cam(a, b, k):
    return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))

def smear(img, amount):
    """Horizontal motion blur."""
    if amount <= 1: return img
    small = img.resize((max(8, int(W / amount)), H), Image.BILINEAR)
    return small.resize((W, H), Image.BILINEAR)

def flash(img, k):
    return Image.blend(img, Image.new('RGB', img.size, (255, 255, 255)), k) if k > 0 else img

# ---------- captions
def caption_layer(step, text, k):
    """Slide-in kinetic caption, bottom-left, over a soft dark gradient."""
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    grad = np.zeros((H, W, 4), np.uint8)
    ramp = np.clip((np.arange(H) - H * 0.55) / (H * 0.45), 0, 1) ** 1.6
    grad[..., 3] = (ramp[:, None] * 200 * k).astype(np.uint8)
    grad[..., :3] = CHAR
    layer = Image.alpha_composite(layer, Image.fromarray(grad, 'RGBA'))
    d = ImageDraw.Draw(layer)
    x = 96 - int((1 - ease_out(k)) * 120)
    a = int(255 * min(1, k * 1.6))
    fs = font('Inter-Bold.otf', 22)
    tw = int(fs.getlength(step))
    d.rounded_rectangle((x, H - 222, x + tw + 28, H - 186), 8, fill=BLUE + (a,))
    d.text((x + 14, H - 204), step, font=fs, fill=(255, 255, 255, a), anchor='lm')
    ft = font('InterDisplay-ExtraBold.otf', 72)
    d.text((x + 3, H - 170 + 3), text, font=ft, fill=(0, 0, 0, int(a * .35)))
    d.text((x, H - 170), text, font=ft, fill=(255, 255, 255, a))
    return layer

def with_caption(img, step, text, k):
    if k <= 0: return img
    return Image.alpha_composite(img.convert('RGBA'), caption_layer(step, text, k)).convert('RGB')

# ---------- title cards (charcoal)
def charcoal_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    base = np.ones((H, W, 3), np.float32) * np.array(CHAR, np.float32)
    d = np.sqrt(((x / W - .5) / .6) ** 2 + ((y / H - .45) / .6) ** 2)
    glow = np.clip(1 - d, 0, 1)[..., None] ** 2
    img = base + glow * np.array([10, 16, 30], np.float32)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))
BG = charcoal_bg()

def word_card(word, k, color=(255, 255, 255)):
    img = BG.copy()
    s = 1.18 - 0.18 * ease_out(k * 2.2)
    f = font('InterDisplay-ExtraBold.otf', int(150 * s))
    d = ImageDraw.Draw(img)
    d.text((W / 2, H / 2), word, font=f, fill=color, anchor='mm')
    d.rectangle((W / 2 - 60, H / 2 + 110, W / 2 + 60, H / 2 + 116), fill=BLUE)
    return img

def logo_card(line1, line2, sub, k):
    img = BG.copy(); d = ImageDraw.Draw(img)
    fl = font('InterDisplay-Bold.otf', 52); lw = fl.getlength('Capture IV')
    y0 = 300 + int((1 - ease_out(k)) * 30)
    d.text((W / 2 - lw / 2, y0), 'Capture', font=fl, fill='white')
    d.text((W / 2 - lw / 2 + fl.getlength('Capture '), y0), 'IV', font=fl, fill=(96, 165, 250))
    fh = font('InterDisplay-ExtraBold.otf', 96)
    d.text((W / 2, y0 + 120), line1, font=fh, fill='white', anchor='ma')
    d.text((W / 2, y0 + 232), line2, font=fh, fill=(96, 165, 250), anchor='ma')
    d.text((W / 2, y0 + 372), sub, font=font('Inter-Medium.otf', 28), fill=(161, 167, 177), anchor='ma')
    if k < 1:
        img = Image.blend(BG, img, smooth(k * 1.5))
    return img

# ---------- flight clip frames (full-frame cut)
CLIP_DIR = S + '/clipframes'
if not os.path.isdir(CLIP_DIR) or not os.listdir(CLIP_DIR):
    os.makedirs(CLIP_DIR, exist_ok=True)
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', CLIP, '-vf', f'scale={W}:{H}:flags=lanczos', '-q:v', '2', CLIP_DIR + '/c%04d.jpg'], check=True)
CLIP_FR = sorted(os.listdir(CLIP_DIR))
def clip_at(sec):
    return Image.open(CLIP_DIR + '/' + CLIP_FR[min(int(sec * 30), len(CLIP_FR) - 1)]).convert('RGB')

# ---------- build
n = 0
def emit(img):
    global n
    img.save(f'{OUT}/a{n:05d}.jpg', quality=93); n += 1

def frames_for(sec): return int(round(sec * FPS))

# 1. Kinetic intro: three words, then logo
for word in ['ROUTES.', 'FOOTAGE.', 'DOCUMENTS.']:
    m = frames_for(0.42)
    for i in range(m): emit(word_card(word, i / m, (96, 165, 250) if word == 'FOOTAGE.' else (255, 255, 255)))
m = frames_for(1.1)
for i in range(m): emit(logo_card('See the site', 'from every angle.', 'Project viewer  ·  live product capture', i / (m * .6)))

FULL = (800, 450, 1.0)
ROUTE_CAM = (690, 445, 2.05)
VIDEO_CAM = (800, 407, 1.95)
DOCS_CAM = (820, 300, 1.55)

# whip from logo into map
last = logo_card('See the site', 'from every angle.', 'Project viewer  ·  live product capture', 1)
m = frames_for(0.28)
for i in range(m):
    k = i / (m - 1)
    a = smear(last, 1 + 40 * k).transform((W, H), Image.AFFINE, (1, 0, int(W * .35 * k), 0, 1, 0))
    b = smear(cam_frame(src(0), *FULL), 1 + 40 * (1 - k)).transform((W, H), Image.AFFINE, (1, 0, -int(W * .35 * (1 - k)), 0, 1, 0))
    emit(Image.blend(a, b, smooth(k)))

# 2. Map: route select + popup, punch in
seg_a, seg_b = 0.0, M['nav'] + 0.05
m = frames_for(seg_b - seg_a)
for i in range(m):
    r = seg_a + i / FPS
    k = ease_out((r - (M['route'] + 0.25)) / 0.55)
    cam = lerp_cam(FULL, ROUTE_CAM, k)
    img = cam_frame(src(r), *cam)
    img = with_caption(img, '01 — SITE MAP', 'Pick a route.', smooth((r - 0.35) / 0.25) * smooth((seg_b - r) / 0.2 + .0001))
    emit(img)

# whip cut to the flight dialog
d0 = float(R[np.searchsorted(R, M['dialog'])])
prev = cam_frame(src(seg_b), *ROUTE_CAM)
m = frames_for(0.24)
for i in range(m):
    k = i / (m - 1)
    b = cam_frame(src(d0), *FULL)
    emit(flash(Image.blend(smear(prev, 1 + 50 * k), smear(b, 1 + 50 * (1 - k)), smooth(k)), 0.25 * (1 - abs(2 * k - 1))))

# 3. Dialog: fast-forward to play, punch in on the video
seg_a, seg_b = d0, M['play']
m = frames_for((seg_b - seg_a) / 3.0)
for i in range(m):
    r = seg_a + i * 3.0 / FPS
    emit(cam_frame(src(r), *lerp_cam(FULL, (800, 430, 1.25), ease_out(i / m))))

play = M['play']
total = 4.0
m = frames_for(total)
for i in range(m):
    t = i / FPS; r = play + t
    if 1.25 <= t < 2.85:
        # full-frame cut to the flight clip the viewer is playing
        img = clip_at(t)
        img = ImageEnhance.Contrast(img).enhance(1.06)
        z = 1.0 + 0.05 * (t - 1.25)
        cw, ch = W / z, H / z
        img = img.resize((W, H), Image.LANCZOS, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        if t < 1.33: img = flash(img, (1.33 - t) / .08 * .5)
    else:
        k = ease_out(t / 0.6) if t < 1.25 else 1.0
        cam = lerp_cam((800, 430, 1.25), VIDEO_CAM, k)
        if t >= 2.85: cam = lerp_cam(VIDEO_CAM, (800, 430, 1.3), ease_out((t - 2.85) / 0.8))
        img = cam_frame(src(r), *cam)
        if 2.85 <= t < 2.93: img = flash(img, (2.93 - t) / .08 * .4)
    img = with_caption(img, '02 — FLIGHT FOOTAGE', 'Watch the flight.', smooth((t - 0.15) / 0.25) * smooth((total - t) / 0.25))
    emit(img)

# whip to documents
d1 = float(R[min(np.searchsorted(R, M['docs'] + 0.3), len(R) - 1)])
prev = cam_frame(src(play + total), *(800, 430, 1.3))
m = frames_for(0.24)
for i in range(m):
    k = i / (m - 1)
    a = smear(prev, 1 + 50 * k).transform((W, H), Image.AFFINE, (1, 0, int(W * .3 * k), 0, 1, 0))
    b = smear(cam_frame(src(d1), *FULL), 1 + 50 * (1 - k)).transform((W, H), Image.AFFINE, (1, 0, -int(W * .3 * (1 - k)), 0, 1, 0))
    emit(Image.blend(a, b, smooth(k)))

# 4. Documents, punch in
seg_a, seg_b = d1, M['end']
m = frames_for(seg_b - seg_a)
for i in range(m):
    r = seg_a + i / FPS
    cam = lerp_cam(FULL, DOCS_CAM, ease_out((r - seg_a) / 0.7))
    img = cam_frame(src(r), *cam)
    img = with_caption(img, '03 — DOCUMENTS', 'Open the record.', smooth((r - seg_a - 0.2) / 0.25))
    emit(img)

# 5. Outro
lastimg = img
m = frames_for(0.3)
outro = lambda k: logo_card('Bring your project', 'into focus.', 'Capture Intelligence Visualized', k)
for i in range(m):
    k = i / (m - 1)
    emit(flash(Image.blend(smear(lastimg, 1 + 40 * k), outro(1), smooth(k)), 0.3 * (1 - abs(2 * k - 1))))
for i in range(frames_for(1.6)):
    emit(outro(1))

print('wrote', n, 'frames =', round(n / FPS, 1), 's')
