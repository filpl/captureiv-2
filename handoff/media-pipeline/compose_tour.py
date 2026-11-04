"""Compose the full software walkthrough video from tourrec/ frames."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
REC, OUT = S + '/tourrec', S + '/vframes_tour'
FPS, W, H, SW, SH = 30, 1920, 1080, 1600, 900
F = '/usr/share/fonts/opentype/inter/'
font = lambda n, s: ImageFont.truetype(F + n, s)
os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT, f))

d = json.load(open(REC + '/frames.json')); fr = d['frames']; t0 = fr[0]['t']
R = np.array([f['t'] - t0 for f in fr]); M = {m['name']: m['t'] - t0 for m in d['markers']}
cache = {}
def src(r):
    i = int(np.clip(np.searchsorted(R, r, side='right') - 1, 0, len(R) - 1))
    if i not in cache:
        if len(cache) > 30: cache.clear()
        cache[i] = Image.open(fr[i]['file']).convert('RGB')
    return cache[i]
after = lambda r: float(R[min(np.searchsorted(R, r), len(R) - 1)])
ease = lambda x: (lambda x: x * x * (3 - 2 * x))(min(max(x, 0.0), 1.0))

# segments: (start, end, speed, caption step, caption text, camera keyframes [(rel_t, cx, cy, z)])
FULL = (800, 450, 1.0)
SEG = [
    (0.0, M['date-nav'] + .05, 1.0, '01', 'Pick a flight date', [(0, *FULL), (1.0, 380, 300, 1.45), (4.6, 380, 300, 1.45), (5.0, *FULL)]),
    (after(M['date-nav'] + .2), M['video-nav'] + .05, 1.0, '02', 'Select a flight route', [(0, *FULL), (2.2, 760, 430, 1.5), (4.0, 760, 430, 1.5)]),
    (after(M['video'] - .1), M['library'] - .05, 1.0, '03', 'Watch the linked flight video', [(0, *FULL), (1.2, 800, 420, 1.35), (10.5, 800, 420, 1.35), (12.0, *FULL)]),
    (M['library'], M['lib-nav'] + .05, 1.0, '04', 'Browse the flight library', [(0, *FULL), (1.6, 800, 640, 1.4), (3.8, 800, 640, 1.4)]),
    (after(M['lib-video'] - .1), M['compare'] - .05, 1.0, '04', 'Open any flight from the library', [(0, 800, 420, 1.25), (5.5, 800, 420, 1.3)]),
    (M['compare'], M['share'] - .05, 1.0, '05', 'Compare two dates side by side', [(0, *FULL), (12.8, *FULL)]),
    (M['share'], M['end'], 1.0, '06', 'Share with a link and access code', [(0, *FULL), (1.6, 800, 470, 1.55), (6.9, 800, 470, 1.55)]),
]

def cam(keys, rt):
    for (ta, *a), (tb, *b) in zip(keys, keys[1:]):
        if ta <= rt <= tb:
            k = ease((rt - ta) / max(tb - ta, 1e-6)); return [a[i] + (b[i] - a[i]) * k for i in range(3)]
    return keys[-1][1:] if rt > keys[-1][0] else keys[0][1:]

def view(img, cx, cy, z):
    w, h = SW / z, SH / z; x0 = min(max(cx - w / 2, 0), SW - w); y0 = min(max(cy - h / 2, 0), SH - h)
    return img.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))

def blur_token(img, r):
    if r < M['share'] + .3: return img
    box = (600, 430, 926, 474); img = img.copy(); img.paste(img.crop(box).filter(ImageFilter.GaussianBlur(9)), box[:2]); return img

def caption(img, step, text, a):
    if a <= 0: return img
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    f1, f2 = font('Inter-Bold.otf', 20), font('Inter-SemiBold.otf', 30)
    tw = int(f2.getlength(text)); w, h = 78 + tw + 34, 74; x = 48; y = H - h - 44 + int((1 - a) * 14)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((x, y + 8, x + w, y + h + 8), 18, fill=(11, 21, 48, int(90 * a)))
    lay = Image.alpha_composite(lay, sh.filter(ImageFilter.GaussianBlur(14))); dr = ImageDraw.Draw(lay)
    dr.rounded_rectangle((x, y, x + w, y + h), 18, fill=(255, 255, 255, int(240 * a)))
    dr.rounded_rectangle((x + 14, y + 14, x + 60, y + h - 14), 12, fill=(37, 99, 235, int(255 * a)))
    dr.text((x + 37, y + h / 2), step, font=f1, fill=(255, 255, 255, int(255 * a)), anchor='mm')
    dr.text((x + 78, y + h / 2), text, font=f2, fill=(11, 21, 48, int(255 * a)), anchor='lm')
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

def bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); img = np.ones((H, W, 3), np.float32) * np.array([238, 242, 248], np.float32)
    for bx, by, rx, ry, col in [(.12, .06, .45, .55, (219, 231, 255)), (.92, .14, .4, .45, (227, 236, 255)), (.5, 1, .5, .5, (230, 238, 255))]:
        dd = np.sqrt(((x / W - bx) / rx) ** 2 + ((y / H - by) / ry) ** 2); a = np.clip(1 - dd / .7, 0, 1)[..., None]; img = img * (1 - a) + np.array(col, np.float32) * a
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))
BG = bg()
def card(l1, l2, sub):
    im = BG.copy(); dr = ImageDraw.Draw(im); fl = font('InterDisplay-Bold.otf', 48); lw = fl.getlength('Capture IV')
    dr.text((W / 2 - lw / 2, 300), 'Capture', font=fl, fill=(11, 21, 48)); dr.text((W / 2 - lw / 2 + fl.getlength('Capture '), 300), 'IV', font=fl, fill=(37, 99, 235))
    fh = font('InterDisplay-ExtraBold.otf', 88); dr.text((W / 2, 410), l1, font=fh, fill=(11, 21, 48), anchor='ma'); dr.text((W / 2, 516), l2, font=fh, fill=(37, 99, 235), anchor='ma')
    dr.text((W / 2, 660), sub, font=font('Inter-Medium.otf', 28), fill=(71, 85, 105), anchor='ma'); return im
INTRO = card('The project viewer,', 'start to finish.', 'Dates  ·  Routes  ·  Flight video  ·  Compare  ·  Share')
OUTRO = card('Bring your project', 'into focus.', 'Capture Intelligence Visualized')

n = 0
def emit(im):
    global n; im.save(f'{OUT}/t{n:05d}.jpg', quality=92); n += 1

for _ in range(int(2.2 * FPS)): emit(INTRO)
prev = INTRO
for si, (a, b, sp, step, text, keys) in enumerate(SEG):
    m = int((b - a) / sp * FPS); seg_dur = m / FPS
    for i in range(m):
        rt = i / FPS; r = a + rt * sp
        im = view(blur_token(src(r), r), *cam(keys, rt))
        cap = ease(rt / .35) * ease((seg_dur - rt) / .35)
        im = caption(im, step, text, cap)
        if i < int(.35 * FPS) and prev is not None: im = Image.blend(prev, im, ease(i / (.35 * FPS)))
        emit(im); last = im
    prev = last
for i in range(int(.6 * FPS)): emit(Image.blend(prev, OUTRO, ease(i / (.6 * FPS))))
for _ in range(int(2.4 * FPS)): emit(OUTRO)
print('frames', n, 'seconds', round(n / FPS, 1))
