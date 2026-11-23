"""Score, foley, voice and mix for 'What Causes an Earthquake? (15 s)' -> out/mix.wav (reads events.json from the page)."""
import json, os, sys
import numpy as np, soundfile as sf, soxr
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.environ['LIB'], 'core', 'audio'))
import sfx
from sfx import SR, t_, env_exp, lp, hp, bp, noise, norm, add

E = json.load(open(os.path.join(HERE, 'events.json'))); DUR = E['dur']; EV = E['ev']
N = int((DUR + .5) * SR)
mus, fol, amb, vox = (np.zeros((N, 2)) for _ in range(4))
hz = lambda m: 440 * 2 ** ((m - 69) / 12)
BEAT = 60 / 96

def kalimba(m, v=1.):
    f = hz(m); d = 1.6; tt = t_(d)
    x = np.sin(2*np.pi*f*tt) * env_exp(d, .5) + .3*np.sin(2*np.pi*5.4*f*tt) * env_exp(d, .05) + .1*np.sin(2*np.pi*2.0*f*tt) * env_exp(d, .25)
    x[:48] *= np.linspace(0, 1, 48); return norm(x) * v
def marimba(m, v=1.):
    f = hz(m); d = 1.0; tt = t_(d)
    x = np.sin(2*np.pi*f*tt) * env_exp(d, .28) + .2*np.sin(2*np.pi*4*f*tt) * env_exp(d, .06) + hp(noise(d), 2500) * env_exp(d, .002) * .1
    return norm(x) * v
def bass(m, v=1., d=1.0):
    f = hz(m); tt = t_(d); x = sum(np.sin(2*np.pi*f*k*tt) / k**1.4 * env_exp(d, .5 / k**.5) for k in range(1, 6)); x[:96] *= np.linspace(0, 1, 96)
    return norm(lp(x, 1200)) * v
def shaker(v=1.): d = .09; return norm(bp(noise(d), 5000, 11000) * np.sin(np.pi * t_(d) / d) ** 3) * v
def pizz(m, v=1.):
    f = hz(m); d = .4; tt = t_(d); x = sum(np.sin(2*np.pi*f*k*tt) / k * env_exp(d, .09 / k**.3) for k in range(1, 6)); return norm(x) * v

# ---- score (15 s cut, film time): D major-ish, 96 bpm ----
motif = [74, 78, 81, 78, 76]
for i, m in enumerate(motif): add(mus, kalimba(m, .45), .1 + i * BEAT / 2, 1, -.2 + i * .1)
prog = [(50, [62, 66, 69]), (47, [59, 62, 66]), (43, [62, 67, 71]), (45, [61, 64, 69])]
t = .1; bar = 0
while t < 4.8:
    root, ch = prog[bar % 4]
    add(mus, bass(root, .55), t, 1, 0)
    for k in range(8):
        tk = t + k * BEAT / 2
        if tk >= 4.8: break
        add(mus, marimba(ch[k % 3] + (12 if k == 6 else 0), .3 if k % 2 else .4), tk, 1, -.3 if k % 2 else .3)
        add(mus, shaker(.12 if k % 2 else .18), tk, 1, .5)
    t += 4 * BEAT; bar += 1
d = 8.6 - 4.8; tt = t_(d); f0 = hz(38)
drone = (np.sin(2*np.pi*f0*tt) + .5*np.sin(2*np.pi*2*f0*tt*(1 + .02*tt/d)) + .25*np.sin(2*np.pi*3.01*f0*tt)) * (tt / d) ** 1.5
add(mus, lp(drone, 600) * .35, 4.8, 1, 0)
for k in range(int(d / BEAT)): add(mus, marimba(50, .25), 4.8 + k * BEAT, 1, 0)
add(mus, bass(43, .4, 2.0), 11.2, 1, 0)
for k in range(2): add(mus, marimba([62, 67][k], .22), 11.2 + k * BEAT, 1, -.2 + k * .3)
add(mus, bass(50, .55, 2.6), 12.6, 1, 0)
for m, tm in zip([74, 78, 81, 86], [12.7, 13.0, 13.3, 13.6]): add(mus, kalimba(m, .45), tm, 1, .1)
for m in [62, 66, 69, 74]: add(mus, marimba(m, .3), 14.0, 1, 0); add(mus, kalimba(m + 12, .2), 14.05, 1, .2)

# ---- foley ----
def snap():
    d = 2.6; tt = t_(d)
    crack = hp(noise(.12), 1500) * env_exp(.12, .02)
    boom = np.sin(2*np.pi*42*tt*(1 - .15*tt/d)) * env_exp(d, .6) + lp(sfx.brown(d), 180) * env_exp(d, .9) * 1.2
    x = boom; x[:len(crack)] += crack * 1.2; return norm(x)
for e in EV:
    t, p, ty = e['t'], e.get('pan', 0), e['type']
    if ty == 'whoosh': add(fol, sfx.whoosh(.7, .3), t, 1, p)
    elif ty == 'land': add(fol, sfx.thump(.7, 60), t, 1, p); add(fol, lp(sfx.clack(.6, .5), 3000), t, 1, p)
    elif ty == 'pop': add(fol, sfx.pop(.25), t, 1, p); add(fol, sfx.click(1.2, .18), t, 1, p)
    elif ty == 'road': add(fol, bp(noise(.8), 300, 2500) * np.sin(np.pi*t_(.8)/.8) * .08, t, 1, 0)
    elif ty == 'arrow': add(fol, sfx.whoosh(.4, .18), t, 1, p)
    elif ty == 'cut': add(fol, hp(sfx.whoosh(.35, .25), 2000), t, 1, p)
    elif ty == 'slide': add(fol, lp(sfx.rumble(.6, .4), 400), t, 1, p)
    elif ty == 'trace': add(fol, sfx.ding(.12), t, 1, 0)
    elif ty == 'year': add(fol, pizz(62 + (e['i'] % 5) * 2 + (e['i'] // 5) * 5, .28), t, 1, p)
    elif ty == 'strain_start':
        d = 8.6 - t; tt = t_(d); gr = lp(sfx.brown(d), 300) * (tt / d) ** 2; add(fol, gr * .35, t, 1, .3)
        for k in range(5): add(fol, sfx.creak(.12 + .05 * k), t + .3 + k * .6, 1, .3)
    elif ty == 'snap': add(fol, snap() * 1.0, t, 1, 0); add(fol, sfx.rumble(3.8, .55), t + .05, 1, .1)
    elif ty == 'rattle':
        for k in range(5): add(fol, sfx.clack(1.3, .14 * (1 - k / 5)), t + k * .06, 1, p)
    elif ty == 'tick': add(fol, sfx.click(1.6, .15), t, 1, 0)
# ---- ambience: light wind + birds, thinned under speech ----
d = DUR + .5; wind = lp(sfx.brown(d), 700) * .05
amb[:, 0] += wind; amb[:, 1] += np.roll(wind, 4000)
rng = np.random.default_rng(3)
for tb in [1.2, 3.1, 13.9]:
    f = 3200 + rng.random() * 800; dd = .12; tt = t_(dd); chirp = np.sin(2*np.pi*(f + 900*np.sin(np.pi*tt/dd))*tt) * np.sin(np.pi*tt/dd)
    add(amb, chirp * .01, tb, 1, rng.random() - .5)
# ---- voice: compress, place on the cues ----
for e in EV:
    if e['type'] != 'voice': continue
    x, sr = sf.read(os.path.join(HERE, 'voices', e['id'] + '.wav'))
    if x.ndim > 1: x = x.mean(1)
    x = soxr.resample(x, sr, SR); x = sfx.compress(norm(x, .9), .3, 3.0)
    add(vox, x, e['t'], 1, 0)
# ---- mix: duck music ~8 dB and ambience under the voice; silence before the snap ----
env = np.abs(vox).mean(1); from scipy.ndimage import maximum_filter1d, uniform_filter1d
act = uniform_filter1d(maximum_filter1d((env > .02).astype(float), int(.25 * SR)), int(.12 * SR))
duck = 1 - .6 * act
gate = np.ones(N); a, b = int(8.6 * SR), int(10.0 * SR); gate[a - 2400:a] = np.linspace(1, 0, 2400); gate[a:b] = 0
mix = mus * (duck * gate)[:, None] * .38 + amb * (1 - .55 * act)[:, None] * gate[:, None] ** .5 + fol * .8 + vox * 1.0
for c in range(2): mix[:, c] = sfx.limit(mix[:, c], .92)
fe = int(DUR * SR); fade = np.ones(N); fade[fe - int(.6 * SR):fe] = np.linspace(1, 0, int(.6 * SR)); fade[fe:] = 0
mix *= fade[:, None]
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix[:fe].astype(np.float32), SR)
def rms(x): return 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
vm = act > .5
print('voice vs music RMS (dB, where voice speaks):', round(rms(vox[vm]) - rms((mus * (duck * gate)[:, None] * .38)[vm]), 1))
