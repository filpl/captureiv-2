"""Hype cut of the software walkthrough. Every cut sits on a 140 BPM beat grid;
speed ramps fast through cursor travel and slow on the key moments; beat-bounce
zooms, shake + RGB split on hits, smear/flash whips, slam captions.
Writes frames to vframes_hype/ and timing to hype_timing.json for music_hype.py."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
REC, OUT = S + '/tourrec', S + '/vframes_hype'
FPS, W, H, SW, SH = 30, 1920, 1080, 1600, 900
BPM = 140.0; BEAT = 60 / BPM
F = '/usr/share/fonts/opentype/inter/'
_fc = {}
def font(n, s):
    if (n, s) not in _fc: _fc[n, s] = ImageFont.truetype(F + n, s)
    return _fc[n, s]
CHAR, BLUE, SKY = (23, 25, 29), (37, 99, 235), (96, 165, 250)
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
ease_out = lambda x: 1 - (1 - clamp(x)) ** 4
smooth = lambda x: (lambda x: x * x * (3 - 2 * x))(clamp(x))

def view(img, cx, cy, z, dx=0, dy=0):
    w, h = SW / z, SH / z; x0 = min(max(cx - w / 2 + dx, 0), SW - w); y0 = min(max(cy - h / 2 + dy, 0), SH - h)
    return img.resize((W, H), Image.BILINEAR if z > 1.02 else Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))
def blur_token(img, r):
    if r < M['share'] + 1.2: return img
    box = (600, 430, 926, 474)
    # blur strength follows the share window's fade-in (white label row above the link)
    a = clamp((np.asarray(img.convert('L').crop((600, 400, 926, 428)), np.float32).mean() - 186) / 40)
    if r > M['share'] + 1.8: a = 1.0
    if a <= 0: return img
    img = img.copy(); crop = img.crop(box); img.paste(Image.blend(crop, crop.filter(ImageFilter.GaussianBlur(9)), a), box[:2]); return img
def smear(img, amt):
    return img if amt <= 1 else img.resize((max(8, int(W / amt)), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
def flash(img, k, col=(255, 255, 255)):
    return Image.blend(img, Image.new('RGB', img.size, col), min(k, 1)) if k > 0.004 else img
def shift(img, dx):
    return img.transform((W, H), Image.AFFINE, (1, 0, dx, 0, 1, 0))
def rgb_split(img, px):
    px = int(px)
    if px < 1: return img
    r, g, b = img.split()
    return Image.merge('RGB', (r.transform((W, H), Image.AFFINE, (1, 0, -px, 0, 1, 0)), g, b.transform((W, H), Image.AFFINE, (1, 0, px, 0, 1, 0))))

GRAD = None
def caption(img, step, text, rt, dur):
    """Slam-in caption: pill pops, headline slides in fast with overshoot."""
    global GRAD
    k = clamp((rt - .05) / .2); out = clamp((dur - rt) / .12)
    if k <= 0 or out <= 0: return img
    if GRAD is None:
        g = np.zeros((H, W, 4), np.uint8); ramp = np.clip((np.arange(H) - H * .55) / (H * .45), 0, 1) ** 1.6
        g[..., :3] = CHAR; g[..., 3] = (ramp[:, None] * 210).astype(np.uint8); GRAD = Image.fromarray(g, 'RGBA')
    a = clamp(k * 2) * out
    lay = Image.fromarray((np.asarray(GRAD).astype(np.float32) * np.array([1, 1, 1, a])).astype(np.uint8), 'RGBA')
    dr = ImageDraw.Draw(lay)
    ov = 1 + .12 * np.sin(np.pi * clamp(k * 1.2)) * (1 - k)          # small overshoot
    x = 96 - int((1 - ease_out(k)) * 260) ; A_ = int(255 * a)
    fs = font('Inter-Bold.otf', 24); tw = int(fs.getlength(step))
    pop = 1 + .25 * max(0, 1 - rt / .18)
    ph = int(38 * pop)
    dr.rounded_rectangle((96, H - 226 - (ph - 38) // 2, 96 + int((tw + 30) * pop), H - 188 + (ph - 38) // 2), 8, fill=BLUE + (A_,))
    dr.text((96 + int((tw + 30) * pop) // 2, H - 207), step, font=fs, fill=(255, 255, 255, A_), anchor='mm')
    ft = font('InterDisplay-ExtraBold.otf', int(84 * ov))
    dr.text((x + 4, H - 170), text, font=ft, fill=(0, 0, 0, int(A_ * .4))); dr.text((x, H - 174), text, font=ft, fill=(255, 255, 255, A_))
    return Image.alpha_composite(img.convert('RGBA'), lay).convert('RGB')

def charcoal():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32); base = np.ones((H, W, 3), np.float32) * np.array(CHAR, np.float32)
    dd = np.sqrt(((x / W - .5) / .6) ** 2 + ((y / H - .45) / .6) ** 2); glow = np.clip(1 - dd, 0, 1)[..., None] ** 2
    return Image.fromarray((base + glow * np.array([12, 20, 40], np.float32)).clip(0, 255).astype(np.uint8))
BG = charcoal()

def word_frame(word, rt, col):
    s = 1.45 - .45 * ease_out(rt / .16)
    img = BG.copy(); dr = ImageDraw.Draw(img)
    dr.text((W / 2, H / 2), word, font=font('InterDisplay-ExtraBold.otf', int(176 * s)), fill=col, anchor='mm')
    bw = int(70 * ease_out(rt / .2)); dr.rectangle((W / 2 - bw, H / 2 + 124, W / 2 + bw, H / 2 + 131), fill=BLUE)
    hit = max(0, 1 - rt / .12)
    img = rgb_split(img, 14 * hit)
    return flash(img, .22 * hit, (60, 110, 255))

def logo_frame(l1, l2, sub, rt, intro=True):
    k = ease_out(rt / .35)
    img = BG.copy(); dr = ImageDraw.Draw(img); fl = font('InterDisplay-Bold.otf', 54); lw = fl.getlength('Capture IV')
    y0 = 292 + int((1 - k) * 40)
    dr.text((W / 2 - lw / 2, y0), 'Capture', font=fl, fill='white'); dr.text((W / 2 - lw / 2 + fl.getlength('Capture '), y0), 'IV', font=fl, fill=SKY)
    fh = font('InterDisplay-ExtraBold.otf', 104); dr.text((W / 2, y0 + 118), l1, font=fh, fill='white', anchor='ma'); dr.text((W / 2, y0 + 236), l2, font=fh, fill=SKY, anchor='ma')
    dr.text((W / 2, y0 + 384), sub, font=font('Inter-Medium.otf', 30), fill=(161, 167, 177), anchor='ma')
    img = Image.blend(BG, img, clamp(rt / .2))
    z = 1 + .035 * rt                                                   # slow push
    if z > 1.001:
        w, h = W / z, H / z; img = img.resize((W, H), Image.BILINEAR, box=((W - w) / 2, (H - h) / 2, (W + w) / 2, (H + h) / 2))
    return img

# ---------------------------------------------------------------- speed ramp
FAST = 2.4
def ramp_map(a, b, holds, beats):
    """Return function out_time -> rec_time. holds: [(r0, r1, rel_speed)] slower windows."""
    rs = np.linspace(a, b, 4000); s = np.full_like(rs, FAST)
    for h0, h1, sp in holds:
        w = np.clip(np.minimum((rs - h0 + .15) / .15, (h1 + .15 - rs) / .15), 0, 1)
        s = s * (1 - w) + sp * w
    cost = np.concatenate([[0], np.cumsum((1 / s[1:] + 1 / s[:-1]) / 2 * np.diff(rs))])
    natural = cost[-1]
    if beats is None: beats = max(4, 2 * round(natural / BEAT / 2))
    T = beats * BEAT
    return (lambda u: float(np.interp(u / T * natural, cost, rs))), beats, natural

# ---------------------------------------------------------------- sections
FULL = (800, 450, 1.0)
def lerp(a, b, k): return tuple(a[i] + (b[i] - a[i]) * k for i in range(3))
SECTIONS = []
def product(a, b, holds, step, text, camf, beats=None):
    f, nb, nat = ramp_map(a, b, holds, beats)
    SECTIONS.append(dict(kind='prod', f=f, beats=nb, step=step, text=text, cam=camf, a=a))
    print(f'{text:28s} rec {b - a:5.2f}s -> {nb} beats ({nb * BEAT:.2f}s)')

WORDS = [('DATES.', 'w'), ('ROUTES.', 'w'), ('FOOTAGE.', 'b'), ('COMPARE.', 'w'), ('SHARE.', 'b')]
SECTIONS.append(dict(kind='words', beats=len(WORDS)))
SECTIONS.append(dict(kind='logo', beats=3))

product(M['date'] - .25, M['date-nav'] + .08,
        [(M['date'] + .45, M['date'] + 1.3, .95), (M['date-nav'] - .7, M['date-nav'] + .08, .8)],
        '01 — CALENDAR', 'Pick a date.',
        lambda r: lerp(FULL, (380, 300, 1.95), ease_out((r - M['date'] - .5) / .45)))
product(after(M['route'] - .35), M['video-nav'] + .05,
        [(M['route'] + .15, M['route'] + 1.5, .9), (M['video-nav'] - .7, M['video-nav'] + .05, .8)],
        '02 — SITE MAP', 'Hit a route.',
        lambda r: lerp(FULL, (740, 430, 2.05), ease_out((r - M['route'] - .2) / .5)))
vplay = M['library'] - 1.0 - 0.8 - 3.6                                   # roughly when playback starts
product(after(M['video'] - .02), M['library'] - 1.75,
        [(M['video'] - .02, M['video'] + .7, .9), (vplay, vplay + 2.6, 1.0)],
        '03 — FLIGHT VIDEO', 'Watch the flight.',
        lambda r: lerp(FULL, (800, 410, 1.62), ease_out((r - M['video']) / .7)))
product(M['library'] - .05, M['lib-nav'] + .05,
        [(M['library'] + 1.0, M['library'] + 2.0, .95), (M['lib-nav'] - .7, M['lib-nav'] + .05, .8)],
        '04 — FLIGHT LIBRARY', 'Every flight, by date.',
        lambda r: lerp(FULL, (800, 650, 1.75), ease_out((r - M['library'] - 1.0) / .45)))
product(after(M['lib-video'] - .02), M['lib-video'] + 2.3, [(M['lib-video'], M['lib-video'] + 2.3, 1.1)],
        '04 — FLIGHT LIBRARY', 'Open any flight.',
        lambda r: lerp((800, 410, 1.5), (800, 410, 1.7), (r - M['lib-video']) / 2.3))
product(M['compare'] - .05, M['share'] - 1.25,
        [(M['compare'] + .7, M['compare'] + 1.9, .9), (M['compare'] + 2.0, M['share'] - 1.25, 1.6)],
        '05 — COMPARE', 'See what changed.',
        lambda r: lerp(lerp(FULL, (820, 470, 1.22), smooth((r - M['compare'] - 1.6) / .8)), (820, 470, 1.32), smooth((r - M['compare'] - 3) / 3)))
product(M['share'] - .05, M['end'],
        [(M['share'] + 1.3, M['share'] + 2.3, .9), (M['end'] - 2.0, M['end'], .85)],
        '06 — SECURE SHARING', 'Share it safely.',
        lambda r: lerp(FULL, (800, 470, 1.9), ease_out((r - M['share'] - 1.45) / .45)))
SECTIONS.append(dict(kind='outro', beats=8))

# ---------------------------------------------------------------- render
start_beat = 0; DROP_SECTION = 2
for s in SECTIONS:
    s['b0'] = start_beat; start_beat += s['beats']
TOTAL = start_beat * BEAT
HW = 4                                                                   # whip half-width (frames)

def render(s, u, gb):
    """Section s at u seconds into it; gb = global beat position."""
    if s['kind'] == 'words':
        i = min(int(u / BEAT), len(WORDS) - 1); w, c = WORDS[i]
        return word_frame(w, u - i * BEAT, SKY if c == 'b' else (255, 255, 255))
    if s['kind'] == 'logo':
        return logo_frame('The project viewer,', 'start to finish.', 'Live product capture · demo project data', u)
    if s['kind'] == 'outro':
        im = logo_frame('Bring your project', 'into focus.', 'Capture Intelligence Visualized', u)
        hit = max(0, 1 - u / .15); return flash(rgb_split(im, 12 * hit), .25 * hit)
    r = s['f'](u); cx, cy, z = s['cam'](r)
    ph = gb - np.floor(gb)                                               # beat bounce
    z *= 1 + .022 * np.exp(-ph * 9)
    hit = max(0, 1 - u / .28); sh = 16 * hit
    im = view(blur_token(src(r), r), cx, cy, z, sh * np.sin(u * 90), sh * np.cos(u * 70))
    im = rgb_split(im, 10 * max(0, 1 - u / .14))
    return caption(im, s['step'], s['text'], u, s['beats'] * BEAT)

n = 0; total_frames = int(round(TOTAL * FPS))
bounds = [int(round(s['b0'] * BEAT * FPS)) for s in SECTIONS] + [total_frames]
def section_at(fi):
    k = max(i for i in range(len(SECTIONS)) if bounds[i] <= fi); return k
edge = {}
def edge_frame(k, which):
    key = (k, which)
    if key not in edge:
        s = SECTIONS[k]; L = s['beats'] * BEAT
        u = 0.0 if which == 'first' else L - 1 / FPS
        edge[key] = render(s, u, s['b0'] + u / BEAT)
    return edge[key]

for fi in range(total_frames):
    k = section_at(fi); s = SECTIONS[k]; u = (fi - bounds[k]) / FPS; gb = fi / FPS / BEAT
    to_next = bounds[k + 1] - fi; since = fi - bounds[k]
    whip_ok = lambda kk: kk >= 2                                           # whips into product + outro (not inside intro)
    if to_next <= HW and k + 1 < len(SECTIONS) and whip_ok(k + 1):
        kk = (HW - to_next + 1) / (HW * 2)                               # 0..0.5
        a = render(s, u, gb); b = edge_frame(k + 1, 'first')
        A = shift(smear(a, 1 + 70 * kk * 2), int(W * .35 * kk * 2))
        im = Image.blend(A, shift(smear(b, 1 + 70 * (1 - kk * 2) ), -int(W * .35 * (1 - kk * 2))), smooth(kk))
        im = flash(rgb_split(im, 22 * kk * 2), .45 * kk * 2)
    elif since < HW and k >= 2:
        kk = .5 + since / (HW * 2)                                       # 0.5..1
        a = edge_frame(k - 1, 'last'); b = render(s, u, gb)
        B = shift(smear(b, 1 + 70 * (1 - kk) * 2), -int(W * .35 * (1 - kk) * 2))
        im = Image.blend(shift(smear(a, 1 + 70 * (1 - kk) * 2 + 40), int(W * .35)), B, smooth(kk))
        im = flash(rgb_split(im, 22 * (1 - kk) * 2), .45 * (1 - kk) * 2)
    else:
        im = render(s, u, gb)
    im.save(f'{OUT}/h{fi:05d}.jpg', quality=90); n += 1

T = dict(bpm=BPM, dur=round(total_frames / FPS, 4), words=len(WORDS),
         drop_beat=SECTIONS[DROP_SECTION]['b0'], cut_beats=[s['b0'] for s in SECTIONS[DROP_SECTION + 1:]],
         outro_beat=SECTIONS[-1]['b0'], total_beats=start_beat)
json.dump(T, open(S + '/hype_timing.json', 'w'))
print('frames', n, 'seconds', T['dur'], T)
