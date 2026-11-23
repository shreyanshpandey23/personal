"""Score, foley and mix for 'Whose Cone?' -> out/mix.wav. Reads events.json (exported from the page)."""
import json, os, sys
import numpy as np, soundfile as sf
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.environ['LIB'], 'core', 'audio'))
import sfx
from sfx import SR, t_, env_exp, lp, hp, bp, noise, norm, add

ev = json.load(open(os.path.join(HERE, 'events.json')))
DUR = ev['dur']; EV = ev['ev']
N = int((DUR + .4) * SR)
music = np.zeros((N, 2)); fol = np.zeros((N, 2)); amb = np.zeros((N, 2))
hz = lambda m: 440 * 2 ** ((m - 69) / 12)

def marimba(m, v=1.0):
    f = hz(m); tau = .35 if m < 60 else .22; d = 1.2; tt = t_(d)
    x = np.sin(2*np.pi*f*tt) * env_exp(d, tau) + .22*np.sin(2*np.pi*4*f*tt) * env_exp(d, tau*.25) + .05*np.sin(2*np.pi*9.9*f*tt) * env_exp(d, .01)
    x += hp(noise(d), 2000) * env_exp(d, .002) * .15
    return norm(x) * v
def glock(m, v=1.0):
    f = hz(m); d = 2.0; tt = t_(d)
    x = sum(a*np.sin(2*np.pi*f*k*tt) * env_exp(d, tau) for k, a, tau in [(1, 1, .9), (2.76, .3, .25), (5.4, .12, .08)])
    return norm(x) * v
def bass(m, v=1.0):   # plucked bass with 2nd/3rd harmonics so it speaks on small speakers
    f = hz(m); d = .9; tt = t_(d)
    x = sum(np.sin(2*np.pi*f*k*tt) / k**1.3 * env_exp(d, .45 / k**.5) for k in range(1, 7))
    x[:96] *= np.linspace(0, 1, 96)
    return norm(lp(x, 1400)) * v

# --- score (120 bpm, beat .5 s, F major) ---
add(music, bass(41, .5), 0.0, 1, 0)
for i, m in enumerate([81, 84, 88]):                      # dye notes: one per system as it takes its colour
    t = [e for e in EV if e['type'] == 'dye'][i]['t']; p = [e for e in EV if e['type'] == 'dye'][i]['pan']
    add(music, glock(m, .5), t, 1, p)
add(music, glock(89, .35), 2.0, 1, .2)
pat = {2.0: [65, 69, 72, 69], 3.0: [65, 69, 72, 77], 4.0: [70, 74, 77, 74], 5.0: [72, 76, 79, 76]}
for b0, notes in pat.items():
    for k in range(8):
        t = b0 + k * .125 * 2 / 2 * 1.0
        t = b0 + k * .125
        if t >= 5.55: break
        add(music, marimba(notes[k % 4], .5 if k % 2 == 0 else .32), t, 1, -.25 if k % 2 else .25)
for t, m in [(2.0, 41), (2.5, 41), (3.0, 41), (3.5, 48), (4.0, 46), (4.5, 46), (5.0, 48)]:
    add(music, bass(m, .7), t, 1, 0)
# silence 5.6–6.3 ; then the landing and the resolve
add(music, bass(41, .8), 7.1, 1, 0)
for i, m in enumerate([65, 69, 72, 77]):                  # rolled chord
    for r in range(6): add(music, marimba(m, .35 * (1 - r / 7)), 7.5 + i * .03 + r * .09, 1, -.3 + i * .2)
for t, m in [(7.5, 84), (7.75, 89), (8.0, 93)]: add(music, glock(m, .4), t, 1, .3)
for k in range(8):
    add(music, marimba([77, 81, 84, 81][k % 4], .28), 8.5 + k * .125 * 1, 1, -.2 if k % 2 else .2)
add(music, bass(41, .6), 8.5, 1, 0); add(music, bass(48, .5), 9.0, 1, 0)
add(music, glock(89, .45), 9.5, 1, 0); add(music, marimba(65, .4), 9.5, 1, 0); add(music, marimba(72, .3), 9.5, 1, .2)

# --- foley from the page's events ---
for e in EV:
    t, p = e['t'], e.get('pan', 0)
    ty = e['type']
    if ty == 'whoosh': add(fol, sfx.whoosh(1.2, .35), t, 1, p)
    elif ty == 'tug':
        add(fol, sfx.creak(.32), t - .02, 1, p)
        add(fol, sfx.thump(.25, 120), t, 1, p)                                   # a soft plush tug
        add(fol, lp(noise(.25), 2500) * env_exp(.25, .06) * .12, t, 1, p)         # cloth
    elif ty == 'pop': add(fol, sfx.pop(.7), t, 1, 0); add(fol, sfx.click(.6, .35), t, 1, 0)
    elif ty == 'arc': add(fol, sfx.whoosh(.8, .18), t, 1, -.1)
    elif ty == 'splat':
        d = .3; add(fol, (lp(noise(d), 900) * env_exp(d, .05) + np.sin(2*np.pi*90*t_(d)) * env_exp(d, .06)) * .6, t, 1, 0)
    elif ty == 'lick': add(fol, bp(noise(.12), 1500, 4500) * env_exp(.12, .03) * .25, t, 1, p)

# --- ambience: soft park air, a little lower in the silence ---
d = DUR + .4; air = lp(sfx.brown(d), 900) * .05 + bp(noise(d), 3000, 7000) * .004
tt = t_(d); duck = 1 - .5 * ((tt > 5.6) & (tt < 6.3))
amb[:len(air), 0] += air * duck; amb[:len(air), 1] += np.roll(air, 2400) * duck

# the silence: music fully out between 5.6 and 6.3
gate = np.ones(N); i0, i1 = int(5.58 * SR), int(6.3 * SR); gate[i0:i1] = 0; gate[i0 - 1200:i0] = np.linspace(1, 0, 1200)
music *= gate[:, None]

mix = music * .8 + fol * 1.0 + amb
for c in range(2): mix[:, c] = sfx.limit(mix[:, c], .9)
fade = np.ones(N); fe = int(DUR * SR); fade[fe - int(.35 * SR):fe] = np.linspace(1, 0, int(.35 * SR)); fade[fe:] = 0
mix *= fade[:, None]
os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
sf.write(os.path.join(HERE, 'out', 'mix.wav'), mix[:int(DUR * SR)].astype(np.float32), SR)
print('mix.wav', mix.shape, 'peak', float(np.abs(mix).max()))
