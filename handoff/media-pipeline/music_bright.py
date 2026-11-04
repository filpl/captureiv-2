"""Original synthesized track v3 for the Capture IV tech cut (no samples).
110 BPM, D major, bright and forward-moving: FM bell hook, syncopated plucked
chord stabs, broken-beat drums with swung hats, bouncy sub bass, airy pad.
Transitions: reverse-bell swell + bell ding. Outro: strummed bell chord."""
import json, wave
import numpy as np

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
T = json.load(open(S + '/tech_timing.json'))
SR = 44100; BPM = T['bpm']; BEAT = 60 / BPM; STEP = BEAT / 4; DUR = T['dur']
N = int(SR * DUR); rng = np.random.default_rng(23)
bus = {k: np.zeros((N, 2), np.float32) for k in ('drums', 'music', 'bells', 'fx')}
bt = lambda b: b * BEAT
X = lambda n: np.arange(n) / SR

def add(sig, start, gain=1.0, pan=0.0, to='music'):
    i = int(round(start * SR))
    if i >= N: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]; l, r = np.sqrt(.5 * (1 - pan)) * 1.414, np.sqrt(.5 * (1 + pan)) * 1.414
    bus[to][i:i + len(sig), 0] += sig * gain * l; bus[to][i:i + len(sig), 1] += sig * gain * r

def onepole(sig, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR); out = np.empty_like(sig); y = 0.0
    for i in range(len(sig)): y = (1 - a) * sig[i] + a * y; out[i] = y
    return out
def lp(sig, win): return np.convolve(sig, np.ones(max(1, win)) / max(1, win), 'same')
def hp(sig, win=6): return sig - lp(sig, win)
A = lambda semi: 110.0 * 2 ** (semi / 12)

_bell = {}
def bell(semi, L=1.2, ratio=3.5, idx=2.6, d=.45):
    key = (semi, L, ratio, idx, d)
    if key not in _bell:
        n = int(SR * L); x = X(n); f = A(semi)
        I = idx * np.exp(-x * 7)
        s = np.sin(2 * np.pi * f * x + I * np.sin(2 * np.pi * f * ratio * x)) + .25 * np.sin(2 * np.pi * f * 2 * x) * np.exp(-x * 4)
        _bell[key] = s * np.exp(-x / d) * np.minimum(x / .002, 1) * np.minimum((L - x) / .02, 1)
    return _bell[key]
def kick():
    n = int(SR * .3); x = X(n); f = 50 + 110 * np.exp(-x * 36)
    return np.tanh(1.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 10)) * np.minimum(x / .002, 1)
def snare():
    n = int(SR * .2); x = X(n)
    body = np.sin(2 * np.pi * np.cumsum(200 + 60 * np.exp(-x * 40)) / SR) * np.exp(-x * 28)
    return body * .6 + hp(rng.standard_normal(n), 4) * np.exp(-x * 20) * .7
def clap():
    n = int(SR * .2); w = rng.standard_normal(n); e = np.zeros(n)
    for o in (0, .008, .016): e += np.exp(-np.maximum(X(n) - o, 0) / (.008 if o < .016 else .07)) * (X(n) >= o)
    return hp(lp(w, 2), 20) * e * .45
def hat(L=.04):
    n = int(SR * L); return hp(hp(rng.standard_normal(n), 2), 2) * np.exp(-X(n) / .012) * .3
def ohat():
    n = int(SR * .18); return hp(hp(rng.standard_normal(n), 2), 2) * np.exp(-X(n) / .06) * .22
def saw(freq, L, voices=3, spread=.006, a=.003, d=.2, rel=.01):
    n = int(SR * L); x = X(n); out = np.zeros(n)
    for v in range(voices):
        out += 2 * ((freq * (1 + (v - (voices - 1) / 2) * spread) * x + rng.random()) % 1) - 1
    e = np.minimum(x / a, 1) * np.exp(-x / d); r = min(n, int(rel * SR)); e[-r:] *= np.linspace(1, 0, r)
    return out / voices * e
def air(L):
    n = int(SR * L); x = X(n) / L; return hp(lp(rng.standard_normal(n), 3), 20) * x ** 2 * (1 - x) ** .3 * 1.3
def boom(L=2.4):
    n = int(SR * L); x = X(n); return np.sin(2 * np.pi * np.cumsum(42 + 28 * np.exp(-x * 6)) / SR) * np.exp(-x * 1.7) * np.minimum(x / .01, 1)

INTRO = bt(T['intro_beats']); OUT = bt(T['outro_beat']); CUTS = [bt(b) for b in T['cut_beats']]
# D major: Dmaj9  Bm7  Gmaj7  Asus  (semitones from A2 = 110 Hz)
prog = [(5, 9, 12, 16, 19), (2, 5, 9, 12, 14), (-2, 2, 5, 9, 12), (0, 5, 7, 12, 14)]
hook = [24, None, 21, 24, 26, None, 24, 21, 17, None, 19, 21, None, 24, 21, None,
        24, None, 26, 28, 29, None, 28, 26, 24, None, 21, None, 19, 21, None, None]
bars = int(np.ceil(T['total_beats'] / 4))
kicks = []

for bar in range(bars):
    t = bt(bar * 4); ch = prog[bar % 4]; groove = INTRO <= t < OUT
    if t >= DUR: break
    # pad (whole piece, quieter in intro/outro)
    pg = .045 if groove else .03
    for j, semi in enumerate(ch[:4]):
        add(onepole(saw(A(semi + 12), bt(4), a=.4, d=6, rel=.3), 900), t, pg, (-.6, -.2, .2, .6)[j])
    # bell hook (8th notes); in the intro a softer, darker version
    for e in range(8):
        semi = hook[(bar % 2) * 16 + e * 2]
        if semi is None: continue
        bb = bell(semi + 12, 1.0, idx=2.6 if groove else 1.4)
        add(bb, t + e * BEAT / 2, .2 if groove else .14, (-.3, .3)[e % 2], to='bells')
    if not groove: continue
    for st in range(16):
        ts = t + st * STEP + (STEP * .22 if st % 2 else 0)               # swing
        if st in (0, 7, 10): add(kick(), t + st * STEP, .9, to='drums'); kicks.append(t + st * STEP)
        if st in (4, 12): add(snare(), t + st * STEP, .42, to='drums'); add(clap(), t + st * STEP, .5, .05, to='drums')
        if st % 2 == 0 or st in (7, 15): add(hat(), ts, .5 if st % 4 == 2 else .3, .3, to='drums')
        if st == 14: add(ohat(), ts, .6, -.25, to='drums')
        # syncopated plucked chord stabs
        if st in (3, 6, 11, 14):
            for j, semi in enumerate(ch[1:4]):
                add(onepole(saw(A(semi + 12), STEP * 1.6, a=.002, d=.09), 2200), t + st * STEP, .055, (-.4, 0, .4)[j])
        # bouncy bass
        if st in (0, 7, 10, 14):
            o = -12 if st == 14 else -24
            n = int(SR * STEP * 2.6); x = X(n)
            add(np.sin(2 * np.pi * A(ch[0] + o) * x) * np.exp(-x * 7) * np.minimum(x / .003, 1), t + st * STEP, .55)
            add(onepole(saw(A(ch[0] + o + 12), STEP * 1.5, voices=2, a=.002, d=.06), 900), t + st * STEP, .22)

# intro: soft ticks for the tag items and a reverse-bell swell into the groove
for i in range(T['tags']):
    add(bell(36 + (0, 4, 7, 9, 12, 16)[i % 6], .25, ratio=4, idx=1.2, d=.06), 1.2 + i * BEAT * .5, .12, -.5 + .2 * i, to='fx')
rev = bell(29, 1.6, idx=2)[::-1]
add(rev[-int(SR * bt(2)):], INTRO - bt(2), .35, to='fx'); add(air(bt(2)), INTRO - bt(2), .3, to='fx')

# transitions
for c in CUTS[:-1]:
    r = bell(24, 1.2, idx=1.8)[::-1]; L = int(SR * BEAT * .9)
    add(r[-L:], c - BEAT * .9, .22, -.2, to='fx'); add(air(BEAT * .9), c - BEAT * .9, .22, to='fx')
    add(bell(36, .9, ratio=2.0, idx=1.0, d=.3), c, .13, .25, to='fx')

# outro: strummed bell chord + soft boom
add(air(BEAT * 2), OUT - BEAT * 2, .3, to='fx'); add(boom(), OUT, .5, to='fx'); add(kick(), OUT, .7, to='drums'); kicks.append(OUT)
for j, semi in enumerate((5, 9, 12, 16, 19, 24, 28)):
    add(bell(semi + 12, DUR - OUT, idx=1.6, d=1.4), OUT + j * .045, .13, -.6 + .2 * j, to='bells')

# mix
t = X(N); duck = np.ones(N, np.float32)
for k in kicks:
    m = (t >= k) & (t < k + BEAT * .5); xx = t[m] - k
    duck[m] = np.minimum(duck[m], 1 - .38 * np.exp(-xx / .08))
bells = bus['bells']; dl = int(bt(.75) * SR)
echo = np.zeros_like(bells); echo[dl:] += bells[:-dl][:, ::-1] * .3; echo[2 * dl:] += bells[:-2 * dl] * .14
mix = bus['drums'] + bus['music'] * duck[:, None] + (bells + echo) * (.8 + .2 * duck[:, None]) + bus['fx']
rv = np.zeros_like(mix)
for dly, g in ((.029, .26), (.047, .21), (.071, .16), (.107, .11), (.151, .08), (.211, .05)):
    i = int(dly * SR); rv[i:] += mix[:-i] * g
mix = mix + .28 * rv[:, ::-1]
fi_, fo = int(.02 * SR), int(1.8 * SR)
mix[:fi_] *= np.linspace(0, 1, fi_)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.4
mix = np.tanh(mix * 1.05); mix = mix / np.max(np.abs(mix)) * .93
with wave.open(S + '/video/capture-iv-bright-music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('wrote', DUR, 's; intro', INTRO, 'cuts', [round(c, 2) for c in CUTS], 'outro', OUT)
