"""Tech-vibe cut of the software walkthrough: active pacing (speed ramps, cuts on a
120 BPM grid) but clean — grid + HUD intro, decoding text, smooth fast slides with a
blue scan line, mono step labels, a progress rail. No glitch, shake or flashes.
Writes frames to vframes_tech/ and timing to tech_timing.json for music_tech.py."""
import json, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
REC, OUT = S + '/tourrec', S + '/vframes_tech2'
FPS, W, H, SW, SH = 30, 1920, 1080, 1600, 900
BPM = 120.0; BEAT = 60 / BPM
FI, FM = '/usr/share/fonts/opentype/inter/', '/usr/share/fonts/truetype/jetbrains-mono/'
_fc = {}
def font(n, s):
    if (n, s) not in _fc: _fc[n, s] = ImageFont.truetype((FM if n.startswith('JetBrains') else FI) + n, s)
    return _fc[n, s]
CHAR, BLUE, SKY, MUTED = (17, 19, 23), (37, 99, 235), (96, 165, 250), (140, 148, 160)
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
clamp = lambda x: min(max(x, 0.0), 1.0)
ease_out = lambda x: 1 - (1 - clamp(x)) ** 3
ease_io = lambda x: (lambda x: 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2)(clamp(x))

def view(img, cx, cy, z):
    w, h = SW / z, SH / z; x0 = min(max(cx - w / 2, 0), SW - w); y0 = min(max(cy - h / 2, 0), SH - h)
    return img.resize((W, H), Image.BILINEAR if z > 1.02 else Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
def blur_token(img, r):
    if r < M['share'] + .9: return img
    box = (600, 430, 926, 474)
    a = clamp((np.asarray(img.convert('L').crop((600, 400, 926, 428)), np.float32).mean() - 186) / 40)
    if r > M['share'] + 1.8: a = 1.0
    if a <= 0: return img
    img = img.copy(); crop = img.crop(box); img.paste(Image.blend(crop, crop.filter(ImageFilter.GaussianBlur(9)), a), box[:2]); return img
def hblur(img, amt):
    return img if amt <= 1 else img.resize((max(8, int(W / amt)), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
def shift(img, dx):
    return img.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, 0))

GLYPHS = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789/#<>_'
def decode(text, k, seed=0):
    """Text resolves left-to-right from random glyphs; k in 0..1."""
    rnd = random.Random(seed + int(k * 40)); n = len(text); done = int(n * clamp(k)); out = []
    for i, ch in enumerate(text):
        if i < done or ch == ' ': out.append(ch)
        elif i < done + 6 and k > 0: out.append(rnd.choice(GLYPHS))
        else: out.append(' ')
    return ''.join(out)

# ---------------------------------------------------------------- backgrounds
def tech_bg():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); img = np.ones((H, W, 3), np.float32) * np.array(CHAR, np.float32)
    dd = np.sqrt(((x / W - .5) / .7) ** 2 + ((y / H - .42) / .6) ** 2); img += np.clip(1 - dd, 0, 1)[..., None] ** 2 * np.array([10, 20, 44], np.float32)
    grid = ((x % 64) < 1) | ((y % 64) < 1); fade = np.clip(1 - dd * .9, 0, 1)
    img += (grid * fade * 14)[..., None]
    im = Image.fromarray(img.clip(0, 255).astype(np.uint8)); dr = ImageDraw.Draw(im)
    for cx, cy, sx, sy in ((72, 72, 1, 1), (W - 72, 72, -1, 1), (72, H - 72, 1, -1), (W - 72, H - 72, -1, -1)):   # HUD corners
        dr.line((cx, cy, cx + 36 * sx, cy), fill=(70, 82, 104), width=2); dr.line((cx, cy, cx, cy + 36 * sy), fill=(70, 82, 104), width=2)
    return im
BG = tech_bg()

def title_card(l1, l2, tag_items, u, seed):
    img = BG.copy(); dr = ImageDraw.Draw(img)
    fm = font('JetBrainsMono-Medium.ttf', 24); fl = font('InterDisplay-Bold.otf', 50); fh = font('InterDisplay-Bold.otf', 100)
    # top mono status line
    dr.text((112, 96), decode('CAPTURE IV  //  PROJECT VIEWER  //  LIVE CAPTURE', u / .9, seed), font=fm, fill=MUTED)
    t = f'{min(u, 99):05.2f}'; dr.text((W - 112, 96), 'T+' + t, font=fm, fill=MUTED, anchor='ra')
    lw = fl.getlength('Capture IV'); a = int(255 * clamp(u / .3))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.text((W / 2 - lw / 2, 300), 'Capture', font=fl, fill=(255, 255, 255, a)); ld.text((W / 2 - lw / 2 + fl.getlength('Capture '), 300), 'IV', font=fl, fill=SKY + (a,))
    img = Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB'); dr = ImageDraw.Draw(img)
    dr.text((W / 2, 410), decode(l1, (u - .25) / .7, seed + 1), font=fh, fill='white', anchor='ma')
    dr.text((W / 2, 528), decode(l2, (u - .55) / .7, seed + 2), font=fh, fill=SKY, anchor='ma')
    # tag items tick in one per beat
    if tag_items:
        fs = font('JetBrainsMono-Medium.ttf', 26); gap = 46
        widths = [fs.getlength(s) for s in tag_items]; total = sum(widths) + gap * (len(tag_items) - 1); x = W / 2 - total / 2
        for i, (s, w) in enumerate(zip(tag_items, widths)):
            k = clamp((u - 1.2 - i * BEAT * .5) / .25)
            if k > 0:
                col = tuple(int(MUTED[c] + (SKY[c] - MUTED[c]) * (1 - k)) for c in range(3))
                dr.text((x, 700), decode(s, k, seed + 10 + i), font=fs, fill=col)
                dr.rectangle((x, 742, x + w * ease_out(k), 744), fill=BLUE if k < 1 else (58, 70, 92))
            x += w + gap
    return img

# ---------------------------------------------------------------- product overlays
GRAD = None
def caption(img, idx, label, text, u, dur):
    global GRAD
    k = clamp((u - .08) / .45); out = clamp((dur - u) / .18)
    if GRAD is None:
        g = np.zeros((H, W, 4), np.uint8); ramp = np.clip((np.arange(H) - H * .6) / (H * .4), 0, 1) ** 1.5
        g[..., :3] = CHAR; g[..., 3] = (ramp[:, None] * 215).astype(np.uint8); GRAD = Image.fromarray(g, 'RGBA')
    a = clamp(k * 3) * out
    lay = Image.fromarray((np.asarray(GRAD).astype(np.float32) * np.array([1, 1, 1, min(1, a * 1.2)])).astype(np.uint8), 'RGBA')
    dr = ImageDraw.Draw(lay); A_ = int(255 * a); x = 112
    fm = font('JetBrainsMono-SemiBold.ttf', 24)
    lab = f'{idx:02d} / {label}'
    dr.rectangle((x, H - 214, x + 10, H - 204), fill=SKY + (A_,))
    dr.text((x + 24, H - 219), decode(lab, k * 1.6, idx * 7), font=fm, fill=SKY + (A_,))
    lw = int((fm.getlength(lab) + 24) * ease_out(k * 1.4)); dr.line((x, H - 186, x + lw, H - 186), fill=(255, 255, 255, int(A_ * .35)), width=1)
    ft = font('InterDisplay-Bold.otf', 72)
    dr.text((x, H - 168), decode(text, (k - .1) * 1.5, idx * 13), font=ft, fill=(255, 255, 255, A_))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

def progress(img, pos, alpha):
    """Bottom rail: 6 steps, fill = overall progress through the product part."""
    if alpha <= 0: return img
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay); x0, x1, y = 112, W - 112, H - 56; A_ = int(255 * alpha)
    dr.line((x0, y, x1, y), fill=(255, 255, 255, int(A_ * .22)), width=2)
    dr.line((x0, y, x0 + (x1 - x0) * clamp(pos), y), fill=SKY + (A_,), width=2)
    for i in range(STEPS + 1):
        xx = x0 + (x1 - x0) * i / STEPS; on = pos >= i / STEPS - 1e-6
        dr.ellipse((xx - 4, y - 4, xx + 4, y + 4), fill=(SKY if on else (90, 98, 112)) + (A_,))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

# ---------------------------------------------------------------- speed ramp
FAST = 2.0
def ramp_map(a, b, holds):
    rs = np.linspace(a, b, 4000); s = np.full_like(rs, FAST)
    for h0, h1, sp in holds:
        w = np.clip(np.minimum((rs - h0 + .2) / .2, (h1 + .2 - rs) / .2), 0, 1); s = s * (1 - w) + sp * w
    cost = np.concatenate([[0], np.cumsum((1 / s[1:] + 1 / s[:-1]) / 2 * np.diff(rs))]); natural = cost[-1]
    beats = max(4, 2 * round(natural / BEAT / 2)); T = beats * BEAT
    return (lambda u: float(np.interp(u / T * natural, cost, rs))), beats

FULL = (800, 450, 1.0)
def lerp(a, b, k): return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))
SECTIONS = []
def product(a, b, holds, step, label, text, camf):
    f, nb = ramp_map(a, b, holds)
    SECTIONS.append(dict(kind='prod', f=f, beats=nb, step=step, label=label, text=text, cam=camf))
    print(f'{text:28s} rec {b - a:5.2f}s -> {nb} beats ({nb * BEAT:.2f}s)')

TAGS = ['DATES', 'ROUTES', 'FOOTAGE', 'COMPARE', 'DOCUMENTS', 'SHARE']
STEPS = 7
SECTIONS.append(dict(kind='intro', beats=8))
product(M['date'] - .25, M['date-nav'] + .08,
        [(M['date'] + .45, M['date'] + 1.3, .95), (M['date-nav'] - .7, M['date-nav'] + .08, .85)],
        1, 'CALENDAR', 'Pick a date.',
        lambda r: lerp(FULL, (380, 300, 1.9), ease_io((r - M['date'] - .45) / .7)))
product(after(M['route'] - .35), M['video-nav'] + .05,
        [(M['route'] + .15, M['route'] + 1.5, .9), (M['video-nav'] - .7, M['video-nav'] + .05, .85)],
        2, 'SITE MAP', 'Select a route.',
        lambda r: lerp(FULL, (740, 430, 1.95), ease_io((r - M['route'] - .1) / .8)))
vplay = M['library'] - 1.0 - 0.8 - 3.6
product(after(M['video'] - .02), M['library'] - 1.75,
        [(M['video'] - .02, M['video'] + .7, .9), (vplay, vplay + 2.8, 1.0)],
        3, 'FLIGHT VIDEO', 'Watch the flight.',
        lambda r: lerp(FULL, (800, 410, 1.58), ease_io((r - M['video']) / 1.0)))
product(M['library'] - .05, M['lib-nav'] + .05,
        [(M['library'] + 1.0, M['library'] + 2.0, .95), (M['lib-nav'] - .7, M['lib-nav'] + .05, .85)],
        4, 'FLIGHT LIBRARY', 'Every flight, by date.',
        lambda r: lerp(FULL, (800, 650, 1.7), ease_io((r - M['library'] - .9) / .7)))
product(after(M['lib-video'] - .02), M['lib-video'] + 2.3, [(M['lib-video'], M['lib-video'] + 2.3, 1.1)],
        4, 'FLIGHT LIBRARY', 'Open any flight.',
        lambda r: lerp((800, 410, 1.5), (800, 410, 1.66), (r - M['lib-video']) / 2.3))
product(M['compare'] - .05, M['docs'] - 1.25,
        [(M['compare'] + .7, M['compare'] + 1.9, .9), (M['compare'] + 2.0, M['docs'] - 1.25, 1.5)],
        5, 'COMPARE', 'See what changed.',
        lambda r: lerp(lerp(FULL, (820, 470, 1.2), ease_io((r - M['compare'] - 1.6) / 1.0)), (820, 470, 1.3), ease_io((r - M['compare'] - 3) / 3)))
product(M['docs-list'] - .45, M['docs-dl'] + .6,
        [(M['docs-list'] - .1, M['docs-list'] + 1.0, 1.0), (M['docs-search'] - .2, M['docs-filtered'] + .3, 1.15), (M['docs-dl'] - .5, M['docs-dl'] + .6, .9)],
        6, 'DOCUMENTS', 'Every document, searchable.',
        lambda r: lerp(lerp(FULL, (840, 300, 1.42), ease_io((r - M['docs-list'] + .1) / .8)), (880, 260, 1.4), ease_io((r - M['docs-search'] + .5) / .7)))
product(M['share'] - .05, M['end'],
        [(M['share'] + 1.3, M['share'] + 2.3, .9), (M['end'] - 2.0, M['end'], .85)],
        7, 'SECURE SHARING', 'Share it securely.',
        lambda r: lerp(FULL, (800, 470, 1.85), ease_io((r - M['share'] - 1.4) / .7)))
SECTIONS.append(dict(kind='outro', beats=8))

b = 0
for s in SECTIONS: s['b0'] = b; b += s['beats']
TOTAL_BEATS = b; total_frames = int(round(TOTAL_BEATS * BEAT * FPS))
P0, P1 = SECTIONS[1]['b0'] * BEAT, SECTIONS[-1]['b0'] * BEAT            # product span for the progress rail

def render(s, u):
    gt = s['b0'] * BEAT + u
    if s['kind'] == 'intro': return title_card('The project viewer,', 'start to finish.', TAGS, u, 3)
    if s['kind'] == 'outro': return title_card('Bring your project', 'into focus.', ['CAPTURE INTELLIGENCE VISUALIZED'], u, 9)
    r = s['f'](u); im = view(blur_token(src(r), r), *s['cam'](r))
    im = caption(im, s['step'], s['label'], s['text'], u, s['beats'] * BEAT)
    rail_a = clamp((gt - P0) / .4) * clamp((P1 - gt) / .25)
    return progress(im, (gt - P0) / (P1 - P0), rail_a)

HW = 5                                                                   # transition half-width (frames)
bounds = [int(round(s['b0'] * BEAT * FPS)) for s in SECTIONS] + [total_frames]
edge = {}
def edge_frame(k, which):
    if (k, which) not in edge:
        s = SECTIONS[k]; L = s['beats'] * BEAT
        edge[k, which] = render(s, 0.0 if which == 'first' else L - 1 / FPS)
    return edge[k, which]

def slide(a, b, k):
    """Fast push left with light motion blur and a blue scan line at the seam. k 0..1."""
    e = ease_io(k); blur = 1 + 24 * np.sin(np.pi * k)
    off = int(W * e)
    A = shift(hblur(a, blur), off); B = shift(hblur(b, blur), off - W)
    im = A.copy(); seam = W - off
    if seam < W: im.paste(B.crop((seam, 0, W, H)), (seam, 0))
    dr = ImageDraw.Draw(im)
    if 0 < seam < W:
        dr.rectangle((seam - 2, 0, seam + 2, H), fill=SKY)
        glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).rectangle((seam - 14, 0, seam + 14, H), fill=SKY + (70,))
        im = Image.alpha_composite(im.convert('RGBA'), glow.filter(ImageFilter.GaussianBlur(10))).convert('RGB')
    return im

for fi in range(total_frames):
    k = max(i for i in range(len(SECTIONS)) if bounds[i] <= fi); s = SECTIONS[k]; u = (fi - bounds[k]) / FPS
    to_next = bounds[k + 1] - fi; since = fi - bounds[k]
    if to_next <= HW and k + 1 < len(SECTIONS):
        im = slide(render(s, u), edge_frame(k + 1, 'first'), (HW - to_next + 1) / (2 * HW + 1))
    elif since < HW and k >= 1:
        im = slide(edge_frame(k - 1, 'last'), render(s, u), (HW + 1 + since) / (2 * HW + 1))
    else:
        im = render(s, u)
    im.save(f'{OUT}/c{fi:05d}.jpg', quality=90)

T = dict(bpm=BPM, dur=round(total_frames / FPS, 4), intro_beats=SECTIONS[1]['b0'], tags=len(TAGS),
         cut_beats=[s['b0'] for s in SECTIONS[2:]], outro_beat=SECTIONS[-1]['b0'], total_beats=TOTAL_BEATS)
json.dump(T, open(S + '/tech_timing.json', 'w'))
print('frames', total_frames, 'seconds', T['dur'], T)
