"""Original synthesized tech track for the Capture IV tech cut (no samples).
120 BPM, A minor. Clean and driving: sequenced 16th arpeggio with a slowly
opening filter, soft round kick, tight hats + shaker, rim clicks, sub bass with
offbeat plucks, warm pad. Transitions get a soft data blip and an airy sweep —
no crashes, impacts or distortion."""
import json, wave
import numpy as np

S = '/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad'
T = json.load(open(S + '/tech_timing.json'))
SR = 44100; BPM = T['bpm']; BEAT = 60 / BPM; DUR = T['dur']
N = int(SR * DUR); rng = np.random.default_rng(5)
bus = {k: np.zeros((N, 2), np.float32) for k in ('drums', 'music', 'fx')}
bt = lambda b: b * BEAT
X = lambda n: np.arange(n) / SR

def add(sig, start, gain=1.0, pan=0.0, to='music'):
    i = int(round(start * SR))
    if i >= N: return
    if i < 0: sig = sig[-i:]; i = 0
    sig = sig[: N - i]; l, r = np.sqrt(.5 * (1 - pan)) * 1.414, np.sqrt(.5 * (1 + pan)) * 1.414
    bus[to][i:i + len(sig), 0] += sig * gain * l; bus[to][i:i + len(sig), 1] += sig * gain * r

def onepole(sig, cutoff):
    """One-pole low-pass, cutoff in Hz (scalar)."""
    a = np.exp(-2 * np.pi * cutoff / SR); out = np.empty_like(sig); y = 0.0
    for i in range(len(sig)): y = (1 - a) * sig[i] + a * y; out[i] = y
    return out
def lp(sig, win): return np.convolve(sig, np.ones(max(1, win)) / max(1, win), 'same')
def hp(sig, win=6): return sig - lp(sig, win)

def kick():
    n = int(SR * .32); x = X(n); f = 46 + 95 * np.exp(-x * 32)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 9) * np.minimum(x / .002, 1)
def hat(L=.035):
    n = int(SR * L); return hp(hp(rng.standard_normal(n), 2), 2) * np.exp(-X(n) / .01) * .35
def shaker():
    n = int(SR * .06); x = X(n); return hp(rng.standard_normal(n), 3) * np.sin(np.pi * x / .06) ** 2 * .14
def rim():
    n = int(SR * .08); x = X(n)
    return (np.sin(2 * np.pi * 1650 * x) * .5 + hp(rng.standard_normal(n), 3) * .5) * np.exp(-x * 70)
def blip(f0=1800, f1=3200, L=.07):
    n = int(SR * L); x = X(n); f = f0 + (f1 - f0) * x / L
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 40) * np.minimum(x / .002, 1)
def air(L, up=True):
    n = int(SR * L); x = X(n) / L; w = hp(lp(rng.standard_normal(n), 3), 20)
    return w * ((np.sin(np.pi * x) ** 2) if not up else x ** 2 * (1 - x) ** .3 * 2.2) * .6
def sub_swell(L, f=55):
    n = int(SR * L); x = X(n); return np.sin(2 * np.pi * f * x) * (x / L) ** 2 * np.minimum((L - x) / .05, 1)
def soft_boom(L=2.5):
    n = int(SR * L); x = X(n); f = 40 + 30 * np.exp(-x * 6)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 1.6) * np.minimum(x / .01, 1)
def saw(freq, L, voices=3, spread=.006, a=.003, d=.2, rel=.01):
    n = int(SR * L); x = X(n); out = np.zeros(n)
    for v in range(voices):
        dt = (v - (voices - 1) / 2) * spread; out += 2 * ((freq * (1 + dt) * x + rng.random()) % 1) - 1
    e = np.minimum(x / a, 1) * np.exp(-x / d); r = min(n, int(rel * SR)); e[-r:] *= np.linspace(1, 0, r)
    return out / voices * e
def sq(freq, L, a=.002, d=.12):
    n = int(SR * L); x = X(n); s = np.sign(np.sin(2 * np.pi * freq * x)) * .6 + np.sin(2 * np.pi * freq * 2 * x) * .2
    e = np.minimum(x / a, 1) * np.exp(-x / d); e[-int(.005 * SR):] *= np.linspace(1, 0, int(.005 * SR)); return s * e
A = lambda semi: 110.0 * 2 ** (semi / 12)

INTRO = bt(T['intro_beats']); OUT = bt(T['outro_beat']); CUTS = [bt(b) for b in T['cut_beats']]
prog = [(0, 3, 7, 10), (-4, 0, 3, 7), (3, 7, 10, 14), (-2, 2, 5, 9)]     # Am7  Fmaj7  Cmaj7  G6-ish
arp_pat = [0, 2, 1, 3, 2, 1, 3, 2, 0, 2, 1, 3, 2, 3, 1, 2]
total_beats = T['total_beats']
kicks = []

# ---------------------------------------------------- arpeggio + pad (whole piece)
arp_cache = {}
for b in range(int(total_beats)):
    t = bt(b); bar = b // 4; ch = prog[bar % 4]
    if t >= OUT + bt(6): break
    # filter opens over the intro, breathes per 4 bars, closes in the outro
    if t < INTRO: cut = 500 + 1900 * (t / INTRO) ** 1.5
    elif t < OUT: cut = 2400 + 1400 * (0.5 - 0.5 * np.cos(2 * np.pi * ((t - INTRO) / bt(16))))
    else: cut = 2400 * max(.15, 1 - (t - OUT) / bt(6))
    for q in range(4):
        semi = ch[arp_pat[(b * 4 + q) % 16]] + (24 if (b * 4 + q) % 8 < 6 else 36)
        key = (semi, int(cut / 100))
        if key not in arp_cache: arp_cache[key] = onepole(sq(A(semi), BEAT / 4 * .95, d=.09), cut)
        g = .16 if t < INTRO else .19
        add(arp_cache[key], t + q * BEAT / 4, g * (1 if q % 2 == 0 else .8), (-.35, .35)[q % 2])
    if b % 4 == 0:
        L = bt(4)
        for j, semi in enumerate(ch):
            p = onepole(saw(A(semi + 12), L, voices=3, spread=.007, a=.6, d=8, rel=.4), 1100)
            add(p, t, .07 if t >= INTRO else .05 * (t / INTRO + .3), (-.6, -.2, .2, .6)[j])
# echo on the arp feel: simple 3/16 delay applied later to music bus

# ---------------------------------------------------- intro: ticks on tag items, sub swell into the groove
for i in range(T['tags']):
    add(blip(2200, 2600, .05), 1.2 + i * BEAT * .5, .22, (-.5 + .25 * i), to='fx')
add(blip(1400, 3400, .12), 0.02, .2, to='fx')
add(sub_swell(bt(2)), INTRO - bt(2), .35, to='fx'); add(air(bt(2), True), INTRO - bt(2), .35, to='fx')

# ---------------------------------------------------- groove
for b in range(T['intro_beats'], T['outro_beat']):
    t = bt(b); ch = prog[(b // 4) % 4]
    add(kick(), t, .9, to='drums'); kicks.append(t)
    add(hat(), t + BEAT / 2, .55, .25, to='drums'); add(hat(.02), t + BEAT * .75, .22, -.25, to='drums')
    for q in range(4): add(shaker(), t + q * BEAT / 4, .8 if q % 2 else .5, .4, to='drums')
    if b % 2 == 1: add(rim(), t, .3, -.1, to='drums')
    if b % 8 == 7: add(rim(), t + BEAT * .75, .18, .2, to='drums')
    # bass: sub on the beat, filtered pluck on the offbeat
    n = int(SR * BEAT * .9); x = X(n)
    add(np.sin(2 * np.pi * A(ch[0] - 24) * x) * np.exp(-x * 4) * np.minimum(x / .004, 1), t, .5)
    add(onepole(saw(A(ch[0] - 12), BEAT * .4, voices=2, a=.002, d=.09), 700), t + BEAT / 2, .38)

# ---------------------------------------------------- transitions: blip + airy sweep, tiny downbeat accent
for c in CUTS[:-1]:
    add(air(BEAT * .9, True), c - BEAT * .9, .3, to='fx')
    add(blip(), c - .02, .16, .3, to='fx'); add(blip(2600, 1900, .05), c + BEAT / 4, .1, -.3, to='fx')

# ---------------------------------------------------- outro
add(air(BEAT, True), OUT - BEAT, .35, to='fx'); add(soft_boom(), OUT, .55, to='fx'); add(blip(1200, 3600, .18), OUT, .18, to='fx')
for j, semi in enumerate((0, 3, 7, 10, 14)):
    add(onepole(saw(A(semi + 12), DUR - OUT, voices=3, a=.05, d=2.5, rel=.6), 1300), OUT, .08, (-.7, -.35, 0, .35, .7)[j])

# ---------------------------------------------------- mix
t = X(N); duck = np.ones(N, np.float32)
for k in kicks:
    m = (t >= k) & (t < k + BEAT); xx = t[m] - k
    duck[m] = np.minimum(duck[m], 1 - .45 * np.exp(-xx / .1) * np.minimum(xx / .006 + .3, 1))
music = bus['music'] * duck[:, None]
dl = int(bt(.75) * SR); echo = np.zeros_like(music); echo[dl:] += music[:-dl][:, ::-1] * .22   # ping-pong-ish 3/16 echo
echo[2 * dl:] += music[:-2 * dl] * .09
mix = bus['drums'] + music + echo + bus['fx']
rev = np.zeros_like(mix)
for dly, g in ((.031, .28), (.049, .22), (.073, .17), (.109, .12), (.157, .08)):
    i = int(dly * SR); rev[i:] += mix[:-i] * g
mix = mix + .25 * rev[:, ::-1]
fi_, fo = int(.02 * SR), int(1.6 * SR)
mix[:fi_] *= np.linspace(0, 1, fi_)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.4
mix = np.tanh(mix * 1.05); mix = mix / np.max(np.abs(mix)) * .93
with wave.open(S + '/video/capture-iv-tech-music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('wrote', DUR, 's; intro', INTRO, 'cuts', [round(c, 2) for c in CUTS], 'outro', OUT)
