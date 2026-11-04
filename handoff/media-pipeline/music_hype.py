"""Original synthesized hype track for the Capture IV hype cut (no samples).
140 BPM, A minor. Word slams -> snare-roll build + riser -> gap -> drop with
distorted four-on-the-floor, rolling sidechained bass, pumping supersaw chords,
pluck hook; crash + impact + reverse swell on every cut; big outro hit + tail."""
import json, wave
import numpy as np

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
T = json.load(open(S + '/hype_timing.json'))
SR = 44100; BPM = T['bpm']; BEAT = 60 / BPM; DUR = T['dur'] + 0.0
N = int(SR * DUR); rng = np.random.default_rng(11)
bus = {k: np.zeros((N, 2), np.float32) for k in ('drums', 'music', 'fx')}
bt = lambda b: b * BEAT

def add(sig, start, gain=1.0, pan=0.0, to='music'):
    i = int(round(start * SR))
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]
    l, r = np.sqrt(.5 * (1 - pan)) * 1.414, np.sqrt(.5 * (1 + pan)) * 1.414
    bus[to][i:i + len(sig), 0] += sig * gain * l; bus[to][i:i + len(sig), 1] += sig * gain * r

X = lambda n: np.arange(n) / SR
def lp(sig, win): return np.convolve(sig, np.ones(max(1, win)) / max(1, win), 'same')
def hp(sig, win=8): return sig - lp(sig, win)
def env(n, a, d): x = X(n); return np.minimum(x / a, 1) * np.exp(-x / d)

def kick(L=.38):
    n = int(SR * L); x = X(n); f = 48 + 190 * np.exp(-x * 45)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-x * 8)
    click = hp(rng.standard_normal(n), 4) * np.exp(-x * 400) * .5
    return np.tanh(3.2 * (body + click)) * .9
def clap():
    n = int(SR * .3); w = rng.standard_normal(n); e = np.zeros(n)
    for o in (0, .009, .018, .027): e += env(n, .0008, .01 if o < .027 else .14) * (X(n) >= o)
    return np.tanh(2 * hp(lp(w, 3), 30) * e) * .8
def snare(L=.18):
    n = int(SR * L); x = X(n)
    tone = np.sin(2 * np.pi * 190 * x) * np.exp(-x * 30)
    return np.tanh(1.6 * (tone + hp(rng.standard_normal(n), 6) * np.exp(-x * 22)))
def hat(open_=False):
    n = int(SR * (.25 if open_ else .05)); return hp(rng.standard_normal(n), 3) * env(n, .0005, .08 if open_ else .012) * .5
def crash(L=1.8):
    n = int(SR * L); x = X(n); w = hp(hp(rng.standard_normal(n), 3), 3)
    return w * np.exp(-x * 2.2) * .5 * (1 + .3 * np.sin(2 * np.pi * 7 * x))
def impact(L=2.2):
    n = int(SR * L); x = X(n)
    sub = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-x * 7)) / SR) * np.exp(-x * 1.8)
    boom = lp(rng.standard_normal(n), 40) * np.exp(-x * 4) * 3
    return np.tanh(2.5 * (sub + boom)) * .9
def subdrop(L=1.6):
    n = int(SR * L); x = X(n); f = 70 * 2 ** (-x * 2.2)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 1.4) * np.minimum(x / .005, 1)
def swell(L, up=True):
    """Reverse-cymbal style noise swell (brightening)."""
    n = int(SR * L); x = X(n) / L; w = rng.standard_normal(n); out = np.zeros(n); blk = 441
    for i0 in range(0, n, blk):
        fr = i0 / n if up else 1 - i0 / n; win = int(60 - 56 * fr) + 2
        seg = w[max(0, i0 - win): i0 + blk]; out[i0:i0 + blk] = (seg - np.convolve(seg, np.ones(win * 3) / (win * 3), 'same'))[-len(out[i0:i0 + blk]):]
    return out * ((x ** 2.2) if up else (1 - x) ** 2) * 1.6
def riser(L, f0=220, octaves=3):
    n = int(SR * L); x = X(n) / L; f = f0 * 2 ** (octaves * x ** 1.3)
    out = np.zeros(n)
    for dt in (-.012, -.005, 0, .005, .012):
        ph = np.cumsum(f * (1 + dt)) / SR; out += 2 * (ph % 1) - 1
    return out / 5 * x ** 1.6
def saw(freq, L, voices=7, spread=.014, a=.005, d=10.0, rel=.03):
    n = int(SR * L); x = X(n); out = np.zeros(n)
    for v in range(voices):
        dt = (v - (voices - 1) / 2) / max(1, (voices - 1) / 2) * spread
        out += 2 * ((freq * (1 + dt) * x + rng.random()) % 1) - 1
    e = np.minimum(x / a, 1) * np.exp(-x / d); r = min(n, int(rel * SR)); e[-r:] *= np.linspace(1, 0, r)
    return out / voices * e
def pluck(freq, L=.2):
    n = int(SR * L); x = X(n); s = (2 * ((freq * x) % 1) - 1) + .5 * np.sin(2 * np.pi * freq * 2 * x)
    return lp(s, 3) * np.exp(-x * 14) * np.minimum(x / .002, 1)
A = lambda semi: 110.0 * 2 ** (semi / 12)

DROP = bt(T['drop_beat']); OUT = bt(T['outro_beat']); CUTS = [bt(b) for b in T['cut_beats']]
kicks = []

# ------------------------------------------------ intro: word slams
for i in range(T['words']):
    t = bt(i); add(kick(), t, 1.0, to='drums'); kicks.append(t); add(clap(), t, .5, to='drums')
    add(impact(.9), t, .45, to='fx'); add(saw(A(-12 + (0, 0, 3, 0, 7)[i]), BEAT * .9, d=.3), t, .22)
    add(crash(.6), t, .18, to='fx')
# build: logo card (beats words..drop) -> snare roll, riser, swell, gap
B0 = bt(T['words'])
build = DROP - B0
steps = []
b = T['words']
while b < T['drop_beat'] - .25:
    rel = (b - T['words']) / (T['drop_beat'] - T['words'])
    div = 2 if rel < .34 else (4 if rel < .67 else 8)
    steps.append((b, rel)); b += 1 / div
for b, rel in steps: add(snare(), bt(b), .25 + .55 * rel, (-.15 if int(b * 8) % 2 else .15), to='drums')
add(riser(build - BEAT * .25, 180, 3), B0, .32); add(swell(build - BEAT * .25), B0, .55, to='fx')
add(saw(A(0), build, a=.3, d=8) + saw(A(7), build, a=.3, d=8), B0, .08)
gap0 = DROP - BEAT * .25                                                  # silence before the drop

# ------------------------------------------------ drop groove
prog = [(0, 3, 7), (-4, 0, 3), (3, 7, 10), (-2, 2, 5)]                    # Am  F  C  G (relative to A)
hook = [12, 15, 19, 15, 22, 19, 15, 12]                                   # eighth-note pluck hook
nbeats = int(round((OUT - DROP) / BEAT))
for k in range(nbeats):
    t = DROP + k * BEAT; bar = k // 4; ch = prog[bar % 4]
    add(kick(), t, 1.0, to='drums'); kicks.append(t)
    if k % 2 == 1: add(clap(), t, .62, .05, to='drums'); add(snare(.12), t, .25, to='drums')
    for q in range(4): add(hat(open_=(q == 2)), t + q * BEAT / 4, (.42, .2, .55, .25)[q], .3, to='drums')
    for q in (1, 2, 3):                                                   # rolling bass on 16ths after the kick
        add(lp(saw(A(ch[0] - 24), BEAT / 4 * .9, voices=2, spread=.004, a=.002, d=.08), 6), t + q * BEAT / 4, .55)
    add(np.sin(2 * np.pi * A(ch[0] - 24) * X(int(SR * BEAT * .9))) * np.exp(-X(int(SR * BEAT * .9)) * 3), t, .35)
    if k % 4 == 0:                                                        # pumping supersaw chord for the bar
        for j, semi in enumerate(ch): add(lp(saw(A(semi + 12), BEAT * 4, a=.01, d=6), 4), t, .085, (-.6, 0, .6)[j])
        add(saw(A(ch[0]), BEAT * 4, voices=5, a=.01, d=6), t, .05)
    for e in (0, 1):                                                       # pluck hook
        semi = hook[(k * 2 + e) % 8] + (0 if bar % 4 < 2 else -2)
        add(pluck(A(semi + 12)), t + e * BEAT / 2, .2, .4 if e else -.4)

# ------------------------------------------------ cut accents
for c in CUTS:
    add(swell(BEAT, True), c - BEAT, .45, to='fx')
    add(crash(), c, .42, to='fx'); add(impact(1.2), c, .4, to='fx')
    for q in range(4): add(snare(.1), c - BEAT + q * BEAT / 4, .18 + .1 * q, to='drums')
add(impact(2.4), DROP, .8, to='fx'); add(subdrop(1.8), DROP, .7, to='fx'); add(crash(2.4), DROP, .55, to='fx')

# ------------------------------------------------ outro: hit + tail
add(swell(BEAT * 2), OUT - BEAT * 2, .6, to='fx')
add(impact(3), OUT, 1.0, to='fx'); add(subdrop(2.4), OUT, .8, to='fx'); add(crash(3), OUT, .6, to='fx'); add(kick(), OUT, 1.0, to='drums'); kicks.append(OUT)
for j, semi in enumerate((0, 3, 7, 12, 15)):
    add(lp(saw(A(semi), DUR - OUT, a=.02, d=1.8), 5), OUT, .09, (-.7, -.35, 0, .35, .7)[j])

# ------------------------------------------------ mix
t = X(N); duck = np.ones(N, np.float32)
for k in kicks:
    m = (t >= k) & (t < k + BEAT); x = t[m] - k
    duck[m] = np.minimum(duck[m], 1 - .82 * np.exp(-x / .11) * np.minimum(x / .004 + .2, 1))
music = bus['music'] * duck[:, None]
fx = bus['fx'] * (0.6 + 0.4 * duck[:, None])
mix = bus['drums'] + music + fx
# pre-drop gap: cut everything except the riser tail for the last quarter beat
g0, g1 = int(gap0 * SR), int(DROP * SR); mix[g0:g1] *= np.linspace(.25, 0, g1 - g0)[:, None]
# stereo room
rev = np.zeros_like(mix)
for dly, g in ((.029, .3), (.043, .26), (.067, .2), (.101, .15), (.149, .1)):
    i = int(dly * SR); rev[i:] += mix[:-i] * g
mix = mix + .22 * rev[:, ::-1]
fo = int(1.2 * SR); mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.6
mix = np.tanh(mix * 1.15); mix = mix / np.max(np.abs(mix)) * .95
with wave.open(S + '/video/capture-iv-hype-music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('wrote', DUR, 's; drop', DROP, 'cuts', [round(c, 2) for c in CUTS], 'outro', OUT)
