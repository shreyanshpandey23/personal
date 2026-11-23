"""High-energy phonk-style text reel, beat-synced to zer0cks (window 9.71s-24.71s).

Something moves on every beat (~0.4s): shockwave ring + text punch + card changes,
on top of continuous smoke, embers and a scrolling ghost word. Big 808 hits get
shake, RGB split, flash and an invert frame.
Usage: python build.py   (paths relative to this file)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(DUR * FPS)
T0 = 9.71   # window start in the track

# Detected beat times in the track (librosa), shifted to output time.
BEATS_SRC = [9.71, 10.12, 10.52, 10.91, 11.31, 11.70, 12.12, 12.52, 12.91, 13.33, 13.75, 14.14,
             14.54, 14.93, 15.35, 15.74, 16.16, 16.56, 16.97, 17.37, 17.76, 18.16, 18.55, 18.95,
             19.34, 19.76, 20.18, 20.57, 20.99, 21.39, 21.78, 22.20, 22.59, 22.99, 23.41, 23.78,
             24.17, 24.57]
BEATS = [b - T0 for b in BEATS_SRC]
b = lambda k: BEATS[k]
DROP = 12.89 - T0                                   # 3.18s
ACCENTS = [DROP, 15.51 - T0, 19.33 - T0, 21.95 - T0]  # heavy 808 hits

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
assert Path(FONT).exists()

RED = np.array([230, 30, 40], np.float32)
WHITE = (248, 248, 248)
REDT = (255, 45, 55)
rng = np.random.default_rng(3)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def last_beat(t):
    past = [x for x in BEATS if x <= t]
    return past[-1] if past else None


def beat_pulse(t, decay=0.09):
    lb = last_beat(t)
    return 0.0 if lb is None else float(np.exp(-(t - lb) / decay))


def accent_amt(t, decay=0.08):
    v = 0.0
    for a in ACCENTS:
        if 0 <= t - a < 0.6:
            v = max(v, float(np.exp(-(t - a) / decay)) * (1.0 if a == DROP else 0.75))
    return v


def energy(t):
    """0 in the pre-drop build, 1 after the drop."""
    return 0.0 if t < DROP else 1.0


# ------------------------------------------------------------------ background layers
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
VIGNETTE = np.clip(1.25 - 1.4 * rr ** 1.4, 0.15, 1.0)[..., None]
GRAIN = [rng.normal(0, 7, (H, W, 1)).astype(np.float32) for _ in range(6)]
DIST = np.sqrt((xx - W / 2) ** 2 + (yy - H * 0.46) ** 2)


def smoke_tex(w, h, blur, seed):
    r = np.random.default_rng(seed)
    s = Image.fromarray((r.random((h // 20, w // 20)) * 255).astype(np.uint8))
    a = np.asarray(s.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur)), np.float32)
    return (a - a.min()) / (a.max() - a.min())


SMOKE1 = smoke_tex(W, H * 2, 45, 1)
SMOKE2 = smoke_tex(W, H * 2, 80, 2)


def ghost_strip():
    f = ImageFont.truetype(FONT, 520)
    txt = "LOCK IN  •  LOCK IN  •  "
    l, t, r, bb = f.getbbox(txt)
    img = Image.new("L", (r - l, bb - t + 40), 0)
    ImageDraw.Draw(img).text((-l, -t + 20), txt, font=f, fill=0, stroke_width=4, stroke_fill=255)
    a = np.asarray(img, np.float32) / 255
    return np.concatenate([a, a], axis=1)


GHOST = ghost_strip()
GHOST_W = GHOST.shape[1] // 2

# embers: start positions + speeds, positions are analytic in t
NE = 140
E_X = rng.uniform(0, W, NE)
E_Y0 = rng.uniform(0, H, NE)
E_V = rng.uniform(120, 420, NE)
E_SW = rng.uniform(0.5, 2.0, NE)
E_SZ = rng.integers(2, 6, NE)
E_PH = rng.uniform(0, 6.28, NE)


def background(t: float, i: int) -> np.ndarray:
    e = energy(t)
    bp = beat_pulse(t)
    frame = np.zeros((H, W, 3), np.float32) + np.array([10, 6, 7], np.float32)
    # smoke drifting upward, red-tinted, brighter after drop and on beats
    o1 = int(t * 140) % H
    o2 = int(t * 60) % H
    sm = 0.6 * SMOKE1[o1:o1 + H] + 0.4 * SMOKE2[o2:o2 + H]
    sm_i = (32 + 16 * e) * (1 + 0.5 * bp * (0.4 + e))
    frame += sm[..., None] * np.array([1.0, 0.25, 0.25], np.float32) * sm_i
    # centre red glow
    glow = np.exp(-(DIST / 620) ** 2)[..., None]
    frame += glow * RED * (0.08 + 0.10 * e + 0.22 * bp * e)
    # giant ghost word scrolling sideways, direction flips every 8 beats
    seg = int(t / (b(8) - b(0))) if t >= 0 else 0
    sgn = 1 if seg % 2 == 0 else -1
    off = int((t * 520 * sgn) % GHOST_W)
    gh = GHOST[:, off:off + W]
    gy = int(H * 0.46 - gh.shape[0] / 2)
    frame[gy:gy + gh.shape[0]] += gh[..., None] * np.array([90, 30, 32], np.float32) * (0.5 + 0.5 * e)
    # shockwave ring on every beat
    lb = last_beat(t)
    if lb is not None and t - lb < 0.38:
        p = (t - lb) / 0.38
        rad = 80 + 900 * ease_out(p)
        width = 10 + 26 * (1 - p)
        ring = np.exp(-((DIST - rad) / width) ** 2)[..., None]
        col = np.array([255, 70, 70], np.float32) if e else np.array([200, 200, 210], np.float32)
        frame += ring * col * (1 - p) * (0.35 + 0.45 * e)
    # embers rising (burst faster after accents)
    boost = 1 + 2.5 * accent_amt(t, 0.25)
    ys = (E_Y0 - E_V * t * (1 + 0.6 * e) * boost) % H
    xs = (E_X + 40 * np.sin(t * E_SW + E_PH)) % W
    for x, y, s in zip(xs.astype(int), ys.astype(int), E_SZ):
        frame[max(0, y - s):y + s, max(0, x - s):x + s] += np.array([255, 120, 60], np.float32) * (0.5 + 0.5 * e)
    return frame


# ------------------------------------------------------------------ text cards
def card_layer(lines: list[tuple[str, tuple]], size: int) -> Image.Image:
    rendered = []
    for txt, col in lines:
        s = size
        while True:
            f = ImageFont.truetype(FONT, s)
            l, t_, r_, bb = f.getbbox(txt)
            if r_ - l <= 940:
                break
            s = int(s * 0.94)
        pad = 50
        im = Image.new("RGBA", (r_ - l + 2 * pad, bb - t_ + 2 * pad), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 8, pad - t_ + 10), txt, font=f, fill=(0, 0, 0, 220))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        ImageDraw.Draw(im).text((pad - l, pad - t_), txt, font=f, fill=col + (255,),
                                stroke_width=max(4, s // 28), stroke_fill=(12, 4, 6, 255))
        rendered.append(im)
    w = max(i.width for i in rendered)
    h = sum(i.height for i in rendered) - 60 * (len(rendered) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for im in rendered:
        out.alpha_composite(im, ((w - im.width) // 2, y))
        y += im.height - 60
    return out


W_, R_ = WHITE, REDT
# (start time, lines, size)
CARDS = [
    (b(0), [("THEY", W_)], 230),
    (b(1), [("THEY", W_), ("DOUBTED", W_)], 210),
    (b(2), [("YOU.", R_)], 300),
    (b(4), [("NOW", W_)], 260),
    (b(5), [("NOW", W_), ("MAKE", W_)], 240),
    (b(6), [("NOW", W_), ("MAKE", W_), ("THEM", W_)], 220),
    (b(7), [("WATCH.", R_)], 250),
    (DROP, [("LOCK", W_), ("IN.", R_)], 330),
    (b(10), [("NO DAYS", W_), ("OFF.", R_)], 230),
    (b(12), [("NO", W_), ("EXCUSES.", R_)], 230),
    (b(14), [("OUTWORK", W_)], 230),
    (ACCENTS[1], [("EVERY", W_), ("ONE.", R_)], 270),
    (b(17), [("PAIN IS", W_)], 230),
    (b(19), [("TEMPORARY.", R_)], 200),
    (b(22), [("PRIDE IS", W_)], 230),
    (b(24), [("FOREVER.", R_)], 230),
    (b(26), [("BE", W_), ("OBSESSED.", R_)], 220),
    (b(28), [("OR BE", W_), ("AVERAGE.", W_)], 210),
    (ACCENTS[3], [("BECOME", W_)], 250),
    (b(32), [("UNSTOP", W_), ("PABLE.", R_)], 280),
]
LAYERS = [(t, card_layer(lines, size)) for t, lines, size in CARDS]


def text_onto(frame: np.ndarray, t: float) -> np.ndarray:
    idx = None
    for j, (start, _) in enumerate(LAYERS):
        if t >= start:
            idx = j
    if idx is None:
        return frame
    start, layer = LAYERS[idx]
    lt = t - start
    style = idx % 4 if start != DROP else 0
    bp = beat_pulse(t)
    scale = 1.0 + 0.07 * bp
    dx = dy = 0.0
    rot = [-3.0, 2.5, -2.0, 3.0][idx % 4]
    if style == 0:            # slam in
        scale *= 1.45 - 0.45 * ease_out(lt / 0.14)
    elif style == 1:          # slide from left
        dx = -700 * (1 - ease_out(lt / 0.16))
    elif style == 2:          # slide from right
        dx = 700 * (1 - ease_out(lt / 0.16))
    else:                     # drop from top
        dy = -500 * (1 - ease_out(lt / 0.16))
    if t >= b(32):            # final card: slow push
        scale *= 1 + 0.06 * (t - b(32)) / (DUR - b(32))
    L = layer.resize((max(1, int(layer.width * scale)), max(1, int(layer.height * scale))), Image.BICUBIC)
    L = L.rotate(rot * (1 - ease_out(lt / 0.3)) + rot * 0.25, resample=Image.BICUBIC, expand=True)
    arr = np.asarray(L, np.float32).copy()
    # glitch slices on the first 3 frames of each card
    if lt < 3 / FPS:
        for _ in range(6):
            y0 = int(rng.integers(0, max(1, arr.shape[0] - 40)))
            hh = int(rng.integers(10, 50))
            arr[y0:y0 + hh] = np.roll(arr[y0:y0 + hh], int(rng.integers(-60, 60)), axis=1)
    ch, cw = arr.shape[:2]
    acc = accent_amt(t)
    sx = int(rng.uniform(-1, 1) * 22 * acc)
    sy = int(rng.uniform(-1, 1) * 22 * acc)
    x0 = int(W / 2 - cw / 2 + dx) + sx
    y0 = int(H * 0.46 - ch / 2 + dy) + sy
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + cw), min(H, y0 + ch)
    if xb <= xa or yb <= ya:
        return frame
    sub = arr[ya - y0:yb - y0, xa - x0:xb - x0]
    al = sub[..., 3:4] / 255 * ease_out(lt / 0.05)
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    return frame


# ------------------------------------------------------------------ frame
def render_frame(i: int) -> np.ndarray:
    t = i / FPS
    frame = background(t, i)
    frame = text_onto(frame, t)

    # camera: zoom punch per beat after drop + bigger on accents + slow drift
    z = 1.0 + 0.012 * (t / DUR) + (0.03 * beat_pulse(t) if t >= DROP else 0.01 * beat_pulse(t)) + 0.06 * accent_amt(t, 0.07)
    acc = accent_amt(t)
    img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
    if z > 1.001 or acc > 0.02:
        cw, ch = W / z, H / z
        cx = W / 2 + rng.uniform(-1, 1) * 30 * acc
        cy = H / 2 + rng.uniform(-1, 1) * 30 * acc
        img = img.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    frame = np.asarray(img, np.float32).copy()

    # RGB split on accents, small one on every beat after drop
    split = int(26 * acc + (5 * beat_pulse(t) if t >= DROP else 0))
    if split:
        frame[..., 0] = np.roll(frame[..., 0], -split, axis=1)
        frame[..., 2] = np.roll(frame[..., 2], split, axis=1)

    frame = frame * VIGNETTE + GRAIN[i % len(GRAIN)]

    # pre-drop: tension darkening in the last beat, then flash/invert on hits
    if b(7) <= t < DROP:
        frame *= 1 - 0.45 * (t - b(7)) / (DROP - b(7))
    for a in ACCENTS:
        dt = t - a
        if 0 <= dt < 1 / FPS:                 # one inverted frame
            frame = 255 - frame
        elif 0 <= dt < 0.25:
            amp = (0.8 if a == DROP else 0.45) * np.exp(-dt / 0.05)
            col = np.array([255, 255, 255] if a == DROP else [255, 60, 60], np.float32)
            frame = frame * (1 - amp) + col * amp

    # progress bar (bottom)
    pw = int(W * t / DUR)
    frame[H - 14:H - 6, :pw] = frame[H - 14:H - 6, :pw] * 0.2 + RED * 0.8

    if t < 0.1:
        frame *= ease_out(t / 0.1)
    if t > DUR - 0.3:
        frame *= max(0.0, (DUR - t) / 0.3)
    return np.clip(frame, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio + encode
def build_audio() -> Path:
    src, pre, out = HERE / "music_window.wav", HERE / "mix_prenorm.wav", HERE / "mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    f"afade=t=in:st=0:d=0.03,afade=t=out:st={DUR - 0.5}:d=0.5", str(pre)], check=True)
    f = "loudnorm=I=-14:TP=-1:LRA=11:print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af", f, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    f2 = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", f2, "-ar", "48000", str(out)], check=True)
    return out


def main() -> None:
    audio = build_audio()
    out = HERE / "final.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio), "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ], stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(render_frame(i).tobytes())
    proc.stdin.close()
    assert proc.wait() == 0
    print(f"done: {out}")


if __name__ == "__main__":
    main()
