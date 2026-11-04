"""Action cut of the full software walkthrough (same style as the earlier action cut):
kinetic intro on charcoal, full-bleed product with punch-in zooms, whip-blur
transitions with flashes, bold slide-in captions, charcoal outro. Writes frames
to vframes_tact/ and cut timings to tour_timing.json for the music."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
REC, OUT = S + '/tourrec', S + '/vframes_tact'
FPS, W, H, SW, SH = 30, 1920, 1080, 1600, 900
F = '/usr/share/fonts/opentype/inter/'
font = lambda n, s: ImageFont.truetype(F + n, s)
CHAR, BLUE = (23, 25, 29), (37, 99, 235)
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))

d = json.load(open(REC + '/frames.json')); fr = d['frames']; t0 = fr[0]['t']
R = np.array([f['t'] - t0 for f in fr]); M = {m['name']: m['t'] - t0 for m in d['markers']}
cache = {}
def src(r):
    i = int(np.clip(np.searchsorted(R, r, side='right') - 1, 0, len(R) - 1))
    if i not in cache:
        if len(cache) > 40: cache.clear()
        cache[i] = Image.open(fr[i]['file']).convert('RGB')
    return cache[i]
after = lambda r: float(R[min(np.searchsorted(R, r), len(R) - 1)])
ease_out = lambda x: 1 - (1 - min(max(x, 0.0), 1.0)) ** 4
smooth = lambda x: (lambda x: x * x * (3 - 2 * x))(min(max(x, 0.0), 1.0))

def view(img, cx, cy, z):
    w, h = SW / z, SH / z; x0 = min(max(cx - w / 2, 0), SW - w); y0 = min(max(cy - h / 2, 0), SH - h)
    return img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
def blur_token(img, r):
    if r < M['share'] + .3: return img
    box = (600, 430, 926, 474); img = img.copy(); img.paste(img.crop(box).filter(ImageFilter.GaussianBlur(9)), box[:2]); return img
def smear(img, amt):
    return img if amt <= 1 else img.resize((max(8, int(W / amt)), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
def flash(img, k):
    return Image.blend(img, Image.new('RGB', img.size, (255, 255, 255)), k) if k > 0 else img
def shift(img, dx):
    return img.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, 0))

GRAD = None
def caption(img, step, text, k):
    global GRAD
    if k <= 0: return img
    if GRAD is None:
        g = np.zeros((H, W, 4), np.uint8); ramp = np.clip((np.arange(H) - H * .55) / (H * .45), 0, 1) ** 1.6
        g[..., :3] = CHAR; g[..., 3] = (ramp[:, None] * 200).astype(np.uint8); GRAD = Image.fromarray(g, 'RGBA')
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    lay = Image.alpha_composite(lay, Image.fromarray((np.asarray(GRAD).astype(np.float32) * np.array([1, 1, 1, k])).astype(np.uint8), 'RGBA'))
    dr = ImageDraw.Draw(lay); x = 96 - int((1 - ease_out(k)) * 120); a = int(255 * min(1, k * 1.6))
    fs = font('Inter-Bold.otf', 22); tw = int(fs.getlength(step))
    dr.rounded_rectangle((x, H - 222, x + tw + 28, H - 186), 8, fill=BLUE + (a,)); dr.text((x + 14, H - 204), step, font=fs, fill=(255, 255, 255, a), anchor='lm')
    ft = font('InterDisplay-ExtraBold.otf', 72)
    dr.text((x + 3, H - 167), text, font=ft, fill=(0, 0, 0, int(a * .35))); dr.text((x, H - 170), text, font=ft, fill=(255, 255, 255, a))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

def charcoal():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); base = np.ones((H, W, 3), np.float32) * np.array(CHAR, np.float32)
    dd = np.sqrt(((x / W - .5) / .6) ** 2 + ((y / H - .45) / .6) ** 2); glow = np.clip(1 - dd, 0, 1)[..., None] ** 2
    return Image.fromarray((base + glow * np.array([10, 16, 30], np.float32)).clip(0, 255).astype(np.uint8))
BG = charcoal()
def word_card(word, k, color=(255, 255, 255)):
    img = BG.copy(); s = 1.18 - .18 * ease_out(k * 2.2); dr = ImageDraw.Draw(img)
    dr.text((W / 2, H / 2), word, font=font('InterDisplay-ExtraBold.otf', int(150 * s)), fill=color, anchor='mm')
    dr.rectangle((W / 2 - 60, H / 2 + 110, W / 2 + 60, H / 2 + 116), fill=BLUE); return img
def logo_card(l1, l2, sub, k):
    img = BG.copy(); dr = ImageDraw.Draw(img); fl = font('InterDisplay-Bold.otf', 52); lw = fl.getlength('Capture IV'); y0 = 300 + int((1 - ease_out(k)) * 30)
    dr.text((W / 2 - lw / 2, y0), 'Capture', font=fl, fill='white'); dr.text((W / 2 - lw / 2 + fl.getlength('Capture '), y0), 'IV', font=fl, fill=(96, 165, 250))
    fh = font('InterDisplay-ExtraBold.otf', 96); dr.text((W / 2, y0 + 120), l1, font=fh, fill='white', anchor='ma'); dr.text((W / 2, y0 + 232), l2, font=fh, fill=(96, 165, 250), anchor='ma')
    dr.text((W / 2, y0 + 372), sub, font=font('Inter-Medium.otf', 28), fill=(161, 167, 177), anchor='ma')
    return Image.blend(BG, img, smooth(k * 1.5)) if k < 1 else img

n = 0
T = {'words': [], 'whips': [], 'hits': []}
def emit(im):
    global n; im.save(f'{OUT}/a{n:05d}.jpg', quality=92); n += 1
now = lambda: n / FPS
fr_ = lambda s: int(round(s * FPS))

def whip(a, b, direction=1, fl=.28):
    T['whips'].append(now()); m = fr_(.24)
    for i in range(m):
        k = i / (m - 1)
        A = shift(smear(a, 1 + 50 * k), int(direction * W * .3 * k)); B = shift(smear(b, 1 + 50 * (1 - k)), -int(direction * W * .3 * (1 - k)))
        emit(flash(Image.blend(A, B, smooth(k)), fl * (1 - abs(2 * k - 1))))

# 1. kinetic intro
for w in ['DATES.', 'ROUTES.', 'FOOTAGE.', 'COMPARE.', 'SHARE.']:
    T['words'].append(now()); m = fr_(.36)
    for i in range(m): emit(word_card(w, i / m, (96, 165, 250) if w in ('FOOTAGE.', 'SHARE.') else (255, 255, 255)))
T['logo'] = now(); m = fr_(1.05)
for i in range(m): emit(logo_card('The project viewer,', 'start to finish.', 'Live product capture · demo project data', i / (m * .6)))
last = logo_card('The project viewer,', 'start to finish.', 'Live product capture · demo project data', 1)

FULL = (800, 450, 1.0)
def lerp(a, b, k): return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))
def segment(a, b, speed, step, text, camf, hits=()):
    """Play recording a..b at `speed`, camera from camf(rel_seconds)."""
    global last
    m = fr_((b - a) / speed); dur = m / FPS
    for i in range(m):
        rt = i / FPS; r = a + rt * speed
        im = view(blur_token(src(r), r), *camf(rt, r))
        im = caption(im, step, text, smooth((rt - .15) / .25) * smooth((dur - rt) / .2 + 1e-4))
        for h in hits:
            if 0 <= r - h < .1: im = flash(im, (1 - (r - h) / .1) * .35)
        emit(im); last = im
    return dur

# 2. date
s0 = .5; first = view(src(s0), *FULL)
whip(last, first); T['drop'] = now()
segment(s0, M['date-nav'] + .05, 1.35, '01 — CALENDAR', 'Pick a date.',
        lambda rt, r: lerp(FULL, (380, 300, 1.9), ease_out((r - M['date'] - .6) / .5)))
# 3. route + popup
a = after(M['date-nav'] + .25); prev = last
whip(prev, view(src(a), *FULL))
segment(a, M['video-nav'] + .05, 1.25, '02 — SITE MAP', 'Hit a route.',
        lambda rt, r: lerp(FULL, (740, 430, 2.0), ease_out((r - M['route'] - .5) / .55)))
# 4. flight video popup
a = after(M['video'] - .05); prev = last; T['hits'].append(now() + .24)
whip(prev, view(src(a), *FULL), fl=.4)
segment(a, M['library'] - .05, 1.15, '03 — FLIGHT VIDEO', 'Watch the flight.',
        lambda rt, r: lerp(lerp(FULL, (800, 410, 1.6), ease_out(rt / .6)), FULL, smooth((r - (M['library'] - 1.4)) / 1.2)))
# 5. library
a = M['library'] + .1; prev = last
whip(prev, view(src(a), *FULL), -1)
segment(a, M['lib-nav'] + .05, 1.3, '04 — FLIGHT LIBRARY', 'Every flight, by date.',
        lambda rt, r: lerp(FULL, (800, 650, 1.7), ease_out((r - M['library'] - .9) / .5)))
a = after(M['lib-video'] - .05); prev = last; T['hits'].append(now() + .24)
whip(prev, view(src(a), *FULL), fl=.4)
segment(a, M['compare'] - .05, 1.4, '04 — FLIGHT LIBRARY', 'Open any flight.',
        lambda rt, r: lerp((800, 410, 1.5), (800, 410, 1.65), rt / 4))
# 6. compare
a = M['compare'] + .1; prev = last
whip(prev, view(src(a), *FULL), -1)
segment(a, M['share'] - .05, 1.5, '05 — COMPARE', 'See what changed.',
        lambda rt, r: lerp(FULL, (840, 470, 1.18), smooth((r - M['compare'] - 2.2) / 1.5)))
# 7. share
a = M['share'] + .05; prev = last
whip(prev, view(src(a), *FULL))
segment(a, M['end'], 1.2, '06 — SECURE SHARING', 'Share it safely.',
        lambda rt, r: lerp(FULL, (800, 470, 1.85), ease_out((r - M['share'] - 1.1) / .6)))
# 8. outro
T['outro'] = now() + .15; prev = last; m = fr_(.3)
out = lambda k: logo_card('Bring your project', 'into focus.', 'Capture Intelligence Visualized', k)
for i in range(m):
    k = i / (m - 1); emit(flash(Image.blend(smear(prev, 1 + 40 * k), out(1), smooth(k)), .3 * (1 - abs(2 * k - 1))))
for _ in range(fr_(1.8)): emit(out(1))
T['dur'] = round(n / FPS, 3)
json.dump(T, open(S + '/tour_timing.json', 'w'))
print('frames', n, 'seconds', T['dur'], T)
