"""Original synthesized music bed for the Capture IV action cut (no samples used).

Timed to the edit: impacts on the three intro words, a riser into the logo,
a drop when the product appears, whooshes on whip transitions, an impact on
the full-frame flight cut, and a final hit with a pad tail on the outro.
"""
import numpy as np, wave

SR = 48000
DUR = 15.70
N = int(SR * DUR)
t = np.arange(N) / SR
mix = np.zeros((N, 2), np.float32)

BPM = 128.0
BEAT = 60 / BPM
rng = np.random.default_rng(7)

def add(sig, start, gain=1.0, pan=0.0):
    i = int(start * SR)
    if i >= N: return
    sig = sig[: N - i]
    l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    mix[i:i + len(sig), 0] += sig * gain * l * 1.414
    mix[i:i + len(sig), 1] += sig * gain * r * 1.414

def env(n, a=0.002, d=0.2):
    x = np.arange(n) / SR
    return np.minimum(x / a, 1) * np.exp(-x / d)

def kick(length=0.45):
    n = int(SR * length); x = np.arange(n) / SR
    f = 42 + 110 * np.exp(-x * 38)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-x * 7.5) + 0.15 * np.tanh(4 * np.sin(ph)) * np.exp(-x * 30)

def hat(length=0.06, open_=False):
    n = int(SR * (0.22 if open_ else length))
    w = rng.standard_normal(n)
    w = np.diff(np.concatenate([[0], w]))  # crude high-pass
    return w * env(n, 0.001, 0.09 if open_ else 0.018) * 0.35

def clap():
    n = int(SR * 0.25); w = rng.standard_normal(n)
    e = np.zeros(n)
    for o in (0, 0.012, 0.024):
        e += env(n, 0.001, 0.012 if o < 0.02 else 0.12) * (np.arange(n) >= int(o * SR))
    b = np.convolve(w, np.ones(6) / 6, 'same') - np.convolve(w, np.ones(40) / 40, 'same')
    return b * e * 0.6

def impact(length=2.2):
    n = int(SR * length); x = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (34 + 60 * np.exp(-x * 9)) * x) * np.exp(-x * 2.2)
    noise = rng.standard_normal(n); noise = np.convolve(noise, np.ones(30) / 30, 'same') * np.exp(-x * 5)
    boom = np.tanh(2.2 * (sub + 0.6 * noise))
    return boom

def whoosh(length=0.45, up=True):
    n = int(SR * length); x = np.arange(n) / SR
    w = rng.standard_normal(n)
    out = np.zeros(n); k = 4
    # sweeping moving-average filter: window shrinks (brighter) over time
    for i0 in range(0, n, 480):
        frac = i0 / n
        win = int(80 - 70 * (frac if up else 1 - frac)) + 2
        seg = w[max(0, i0 - win): i0 + 480]
        out[i0:i0 + 480] = np.convolve(seg, np.ones(win) / win, 'same')[-len(out[i0:i0 + 480]):]
    shape = np.sin(np.pi * np.clip(x / length, 0, 1)) ** 1.5
    return out * shape * 2.2

def riser(length):
    n = int(SR * length); x = np.arange(n) / SR
    f = 180 * (2 ** (3 * x / length))
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    noise = rng.standard_normal(n) * (x / length) ** 2 * 0.3
    return (0.25 * saw + noise) * (x / length) ** 1.8

def note(freq, length, kind='saw', a=0.01, d=0.3, detune=0.004):
    n = int(SR * length); x = np.arange(n) / SR
    out = np.zeros(n)
    for dt in (-detune, 0, detune):
        ph = 2 * np.pi * freq * (1 + dt) * x
        out += (2 * ((ph / (2 * np.pi)) % 1) - 1) if kind == 'saw' else np.sin(ph)
    out /= 3
    e = np.minimum(x / a, 1) * np.exp(-x / d)
    rel = int(0.03 * SR); e[-rel:] *= np.linspace(1, 0, rel)
    return out * e

def lowpass(sig, win):
    return np.convolve(sig, np.ones(win) / win, 'same')

A = lambda semis: 110.0 * 2 ** (semis / 12)

# ---------------------------------------------------------------- timeline
OFF = 0.0                        # titles open the video (no launch shot)
WORDS = [OFF + 0.0, OFF + 0.42, OFF + 0.84]
LOGO = OFF + 1.26
DROP = 2.67          # product appears after the whip
WHIP1, WHIP2, WHIP3 = 2.40, 6.17, 11.53
CLIP_CUT = 8.80
OUTRO = 13.87

# Drone launch: rotor spin-up and climb (synthesized), low pad swell, riser into the titles
def rotors(length):
    n = int(SR * length); x = np.arange(n) / SR
    spin = np.clip(x / 0.5, 0, 1) ** 0.7
    f = 110 + 120 * spin + 35 * np.clip((x - 0.6) / (length - 0.6), 0, 1)
    out = np.zeros(n)
    for m, (det, g) in enumerate([(1.0, .5), (1.013, .4), (0.987, .4), (1.021, .3)]):
        ph = 2 * np.pi * np.cumsum(f * det) / SR
        out += g * (2 * ((ph / (2 * np.pi)) % 1) - 1)
    bpf = np.sin(2 * np.pi * np.cumsum(f * 2) / SR)          # blade-pass flutter
    noise = lowpass(rng.standard_normal(n), 6) * 0.6
    out = lowpass(out, 5) * (0.75 + 0.25 * bpf) + noise * spin
    fade = np.clip((length - x) / 0.35, 0, 1)
    return out * spin * fade * 0.35
# Intro: three impacts on the words, riser into the logo, swell
for w in WORDS:
    add(kick(0.5), w, 0.9); add(clap(), w, 0.35)
    add(note(A(-12), 0.38, 'sine', 0.002, 0.25), w, 0.55)
add(riser(DROP - LOGO), LOGO, 0.32)
add(note(A(0), DROP - LOGO, 'saw', 0.4, 2.0) , LOGO, 0.07, -0.3)
add(note(A(7), DROP - LOGO, 'saw', 0.4, 2.0) , LOGO, 0.07, 0.3)

# Whooshes on transitions
for wt in (WHIP1, WHIP2, WHIP3, OUTRO - 0.15):
    add(whoosh(0.5, True), wt - 0.18, 0.28, -0.2)

# Drop: groove from DROP until OUTRO
add(impact(1.8), DROP, 0.55)
chords = [(-3, 0, 4), (-7, -3, 0), (0, 4, 7), (-5, -1, 2)]   # F#m-ish minor progression in A
bar = BEAT * 4
s = DROP
while s < OUTRO - 0.05:
    b = int(round((s - DROP) / BEAT))
    add(kick(), s, 0.85)
    if b % 2 == 1: add(clap(), s, 0.32, 0.1)
    for half in (0.0, 0.5):
        add(hat(open_=half == 0.5 and b % 4 == 3), s + half * BEAT, 0.5 if half else 0.32, 0.35)
    # sidechained-feeling bass: off-beat pulses
    root = chords[(b // 4) % 4][0]
    add(lowpass(note(A(root - 12), BEAT * 0.45, 'saw', 0.004, 0.18), 18), s + BEAT * 0.5, 0.42)
    s += BEAT
# Pads per bar
s = DROP; ci = 0
while s < OUTRO:
    for k, semi in enumerate(chords[ci % 4]):
        add(lowpass(note(A(semi + 12), bar, 'saw', 0.15, 2.5, 0.006), 10), s, 0.055, (-0.5, 0, 0.5)[k])
    # arpeggio sixteenths
    for k in range(16):
        semi = chords[ci % 4][k % 3] + 24 + (12 if k % 8 == 7 else 0)
        add(note(A(semi), BEAT / 4 * 0.9, 'saw', 0.002, 0.07, 0.002), s + k * BEAT / 4, 0.05, 0.4 if k % 2 else -0.4)
    s += bar; ci += 1

# Accent on the full-frame flight cut
add(impact(1.4), CLIP_CUT, 0.4); add(whoosh(0.35, False), CLIP_CUT - 0.05, 0.2)

# Outro: final hit + sustained chord tail
add(impact(2.4), OUTRO, 0.7)
for k, semi in enumerate((0, 4, 7, 12)):
    add(lowpass(note(A(semi + 12), DUR - OUTRO, 'saw', 0.05, 1.6, 0.006), 12), OUTRO, 0.07, (-0.6, -0.2, 0.2, 0.6)[k])

# ---------------------------------------------------------------- master
# simple room reverb (multi-tap feedback-free)
rev = np.zeros_like(mix)
for d, g in ((0.031, .35), (0.047, .3), (0.071, .25), (0.113, .2), (0.167, .14), (0.241, .1)):
    i = int(d * SR); rev[i:] += mix[:-i] * g
mix = mix + 0.35 * rev[:, ::-1]
# fade in/out, soft clip, normalize to about -1 dBFS
fi, fo = int(0.01 * SR), int(0.9 * SR)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]
mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
mix = np.tanh(mix * 1.3)
mix = mix / np.max(np.abs(mix)) * 0.89
pcm = (mix * 32767).astype(np.int16)
with wave.open('/tmp/claude-0/-home-user-captureiv-2/3f8c5414-7d0d-557f-93cc-eca079e787dc/scratchpad/video/capture-iv-music.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', DUR, 's')
