"""Score, foley, voice and mix for 'Bowlista — Store in a Box (10 s)' -> out/mix.wav (reads events.json from the page)."""
import json, os, sys
import numpy as np, soundfile as sf, soxr
from scipy.ndimage import maximum_filter1d, uniform_filter1d
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.environ['LIB'], 'core', 'audio'))
import sfx
from sfx import SR, t_, env_exp, lp, hp, bp, noise, norm, add

E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']
N = int((DUR + .5) * SR)
mus, fol, amb, vox = (np.zeros((N, 2)) for _ in range(4))
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
BEAT = .6   # 100 bpm

def piano(m, v=1., d=2.2):
    f = hz(m); tt = t_(d)
    x = sum(np.sin(2*np.pi*f*k*tt*(1 + .0004*k*k)) / k**1.6 * env_exp(d, .9 / k**.7) for k in range(1, 8))
    x += hp(noise(d), 3000) * env_exp(d, .004) * .05; x[:64] *= np.linspace(0, 1, 64); return norm(lp(x, 4500)) * v
def vibe(m, v=1., d=1.8):
    f = hz(m); tt = t_(d); trem = 1 + .25 * np.sin(2*np.pi*5.5*tt)
    x = (np.sin(2*np.pi*f*tt) + .18*np.sin(2*np.pi*4*f*tt) * env_exp(d, .15)) * env_exp(d, .7) * trem; x[:48] *= np.linspace(0, 1, 48); return norm(x) * v
def glock(m, v=1.):
    f = hz(m); d = 1.4; tt = t_(d); return norm(sum(a*np.sin(2*np.pi*f*k*tt) * env_exp(d, tau) for k, a, tau in [(1, 1, .7), (2.76, .3, .2), (5.4, .1, .06)])) * v
def pizz(m, v=1.):
    f = hz(m); d = .45; tt = t_(d); return norm(sum(np.sin(2*np.pi*f*k*tt) / k * env_exp(d, .1 / k**.3) for k in range(1, 6))) * v
def shaker(v=1.): d = .08; return norm(bp(noise(d), 5000, 11000) * np.sin(np.pi * t_(d) / d) ** 3) * v
def strings(m, d, v=1.):
    f = hz(m); tt = t_(d)
    saw = sum(np.sin(2*np.pi*f*k*tt*(1 + .002*np.sin(2*np.pi*.3*tt + k))) / k for k in range(1, 9))
    env = np.minimum(1, tt / .8) * np.minimum(1, (d - tt) / .8); return norm(lp(saw, 900)) * env * v

# ---- score: F major, 100 bpm; piano chords per bar, a low string root under everything ----
PROG = [(41, [65, 69, 72]), (38, [62, 65, 69]), (46, [62, 65, 70]), (48, [64, 67, 72])]
BAR = 4 * BEAT
nb = int(DUR / BAR) + 1
for b in range(nb):
    t0 = b * BAR; root, ch = PROG[b % 4]
    if t0 > DUR - .5: break
    add(mus, strings(root, BAR + .9, .5), t0 - .2, 1, 0)
    if t0 >= 1.2:
        for i, m in enumerate(ch): add(mus, piano(m, .3 - i * .04), t0 + i * .03, 1, -.25 + i * .25)
        add(mus, piano(ch[1] + 12, .18), t0 + 2 * BEAT, 1, .2)
# the opening motif on vibraphone as the lid comes off
for i, m in enumerate([72, 77, 81, 84]): add(mus, vibe(m, .45), .35 + i * .22, 1, -.3 + i * .2)
# walking: pizzicato on each step of the customer, shaker on the off-beats
steps = [e['t'] for e in EV if e['type'] == 'step']
for i, t in enumerate(steps): add(mus, pizz([53, 57, 60, 57][i % 4], .35), t, 1, .15); add(mus, shaker(.12), t + .15, 1, .4)
# floor letters: a vibraphone note each, the accent doubled on glockenspiel
scale = [65, 67, 69, 72, 74, 77, 79, 81]
for e in EV:
    if e['type'] == 'land':
        m = scale[e['i'] % len(scale)]
        add(mus, vibe(m, .32 if not e['accent'] else .45), e['t'], 1, (e['i'] % 5 - 2) * .15)
        if e['accent']: add(mus, glock(m + 12, .3), e['t'], 1, 0)
# resolve on the brand line
for i, m in enumerate([53, 65, 69, 72, 77]): add(mus, piano(m, .32, 3.0), 7.95 + i * .04, 1, -.2 + i * .1)
add(mus, vibe(84, .4, 2.0), 8.5, 1, .1); add(mus, glock(89, .25), 9.3, 1, 0)

# ---- foley ----
for e in EV:
    t, ty, p = e['t'], e['type'], e.get('pan', 0)
    if ty == 'lid': add(fol, sfx.creak(.25), t + .1, 1, -.2); add(fol, lp(sfx.whoosh(1.0, .35), 3000), t + .3, 1, -.3)
    elif ty == 'panels': add(fol, lp(sfx.rumble(.8, .35), 500), t, 1, 0); add(fol, sfx.thump(.4, 80), t + .75, 1, 0)
    elif ty == 'chime': add(fol, sfx.ding(.18), t, 1, 0)
    elif ty == 'step': add(fol, lp(sfx.step(.18), 3000), t, 1, .1)
    elif ty == 'tap': add(fol, sfx.click(1.8, .14), t, 1, -.1)
    elif ty == 'bowl': add(fol, lp(sfx.clack(.7, .3), 2500), t + .5, 1, -.1)
    elif ty == 'scoop': add(fol, lp(sfx.clack(1.1, .16), 3500), t, 1, -.1); add(fol, bp(noise(.12), 800, 3000) * env_exp(.12, .03) * .1, t + .03, 1, -.1)
    elif ty == 'cup': add(fol, sfx.click(.9, .2), t, 1, .1)
    elif ty == 'pour':
        d = .7; tt = t_(d); x = bp(noise(d), 600, 2400) * np.sin(np.pi * tt / d) * (1 + .4 * np.sin(2*np.pi*13*tt)) * .12
        add(fol, x, t, 1, .1); [add(fol, sfx.click(2.2, .1), t + .1 + k * .12, 1, .1) for k in range(3)]   # ice
    elif ty == 'bag': add(fol, bp(noise(.4), 1500, 7000) * env_exp(.4, .1) * .25, t, 1, .2)
    elif ty == 'cut': add(fol, lp(sfx.whoosh(.3, .12), 2500), t - .15, 1, 0)
    elif ty == 'shelf': add(fol, lp(sfx.clack(.8, .25), 2500), t, 1, .2)
# ---- ambience: quiet mall air ----
d = DUR + .5; air = lp(sfx.brown(d), 600) * .045 + lp(noise(d), 1500) * .006
amb[:, 0] += air; amb[:, 1] += np.roll(air, 3000)
# ---- voice ----
for e in EV:
    if e['type'] != 'voice': continue
    x, sr = sf.read(os.path.join(HERE, 'voices', e['id'] + '.wav'))
    if x.ndim > 1: x = x.mean(1)
    x = soxr.resample(x, sr, SR); x = sfx.compress(norm(x, .9), .3, 3.0); add(vox, x, e['t'], 1, 0)
# ---- mix: music ducks ~16 dB under the voice and lifts between lines ----
env = np.abs(vox).mean(1)
act = uniform_filter1d(maximum_filter1d((env > .02).astype(float), int(.3 * SR)), int(.15 * SR))
mus_g = 1 - .84 * act
mix = mus * mus_g[:, None] * .7 + amb * (1 - .5 * act)[:, None] + fol * .7 + vox
for c in range(2): mix[:, c] = sfx.limit(mix[:, c], .9)
fe = int(DUR * SR); fade = np.ones(N); fade[fe - int(.8 * SR):fe] = np.linspace(1, 0, int(.8 * SR)); fade[fe:] = 0
mix *= fade[:, None]
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix[:fe].astype(np.float32), SR)
rms = lambda x: 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9); vm = act > .5
print('voice over music (dB, while speaking):', round(rms(vox[vm]) - rms((mus * mus_g[:, None] * .7)[vm]), 1))
