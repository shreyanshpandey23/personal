"""Text-only motivation reel over a generated stormy-mountain background.

Beat-synced to "Belo Ritmo Salsa" window 10.49s-24.49s (kicks every 0.8s,
drop at 4.00s output). Black & white storm: mountains, fog, rain, lightning.
Usage: python build.py   (paths relative to this file)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 14.0
N = int(DUR * FPS)
K = 0.80
kick = lambda k: k * K
DROP = kick(5)

BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
SERIF_I = "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf"
for fp in (BLACK, SERIF_I):
    assert Path(fp).exists(), f"font missing: {fp}"

rng = np.random.default_rng(7)


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def kick_pulse(t, start=0.0, decay=0.10):
    if t < start:
        return 0.0
    return float(np.exp(-(t - int(t / K) * K) / decay))


# ------------------------------------------------------------------ background
# Rendered at 1.15x so the camera can push in / punch without showing edges.
OS = 1.15
BW, BH = int(W * OS), int(H * OS)


def ridge(width, base, amp, rough, seed):
    r = np.random.default_rng(seed)
    n = 513
    pts = np.zeros(n)
    pts[0], pts[-1] = r.uniform(-1, 1, 2) * amp
    step, scale = n - 1, amp
    while step > 1:
        half = step // 2
        for i in range(half, n - 1, step):
            pts[i] = (pts[i - half] + pts[i + half]) / 2 + r.uniform(-1, 1) * scale
        step, scale = half, scale * rough
    xs = np.linspace(0, width, n)
    return np.interp(np.arange(width), xs, base - pts)


yy = np.arange(BH, dtype=np.float32)[:, None]
SKY = (14 + 34 * (yy / BH) ** 1.4) * np.ones((1, BW), np.float32)          # dark top, lighter horizon
far = ridge(BW, BH * 0.62, 170, 0.55, 3)
near = ridge(BW, BH * 0.72, 230, 0.58, 11)
FAR_MASK = (yy >= far[None, :]).astype(np.float32)
NEAR_MASK = (yy >= near[None, :]).astype(np.float32)


def fog_tex(w, h, blur, seed):
    r = np.random.default_rng(seed)
    small = Image.fromarray((r.random((h // 16, w // 16)) * 255).astype(np.uint8))
    big = small.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    a = np.asarray(big, np.float32) / 255
    return (a - a.min()) / (a.max() - a.min())


FOG1 = fog_tex(BW * 2, BH, 40, 1)
FOG2 = fog_tex(BW * 2, BH, 70, 2)
# horizon fog band strength
BAND = np.exp(-((yy / BH - 0.70) / 0.12) ** 2)


def rain_tex():
    img = Image.new("L", (BW, BH * 2), 0)
    d = ImageDraw.Draw(img)
    r = np.random.default_rng(5)
    for _ in range(1400):
        x, y = r.uniform(0, BW), r.uniform(0, BH * 2)
        ln = r.uniform(40, 110)
        d.line((x, y, x - ln * 0.18, y + ln), fill=int(r.uniform(60, 160)), width=2)
    return np.asarray(img, np.float32) / 255


RAIN = rain_tex()


def bolt_mask(seed):
    r = np.random.default_rng(seed)
    img = Image.new("L", (BW, BH), 0)
    d = ImageDraw.Draw(img)

    def seg(x, y, ang, length, width, depth):
        for _ in range(int(length / 30)):
            ang += r.normal(0, 0.35)
            nx, ny = x + 30 * np.sin(ang), y + 30 * np.cos(ang)
            d.line((x, y, nx, ny), fill=255, width=max(1, int(width)))
            if depth < 2 and r.random() < 0.08:
                seg(nx, ny, ang + r.choice([-0.7, 0.7]), length * 0.35, width * 0.5, depth + 1)
            x, y = nx, ny
            if y > far[min(BW - 1, max(0, int(x)))]:
                break

    seg(BW * 0.62, 0, 0.15, BH * 0.75, 5, 0)
    glow = img.filter(ImageFilter.GaussianBlur(22))
    return np.asarray(img, np.float32) / 255, np.asarray(glow, np.float32) / 255


BOLT, BOLT_GLOW = bolt_mask(9)
LIGHTNING = {DROP: 1.0, kick(13): 0.55}          # flash strengths


def flash_amount(t):
    v = 0.0
    for at, amp in LIGHTNING.items():
        dt = t - at
        if 0 <= dt < 0.6:
            # double flicker typical of lightning
            v = max(v, amp * (np.exp(-dt / 0.06) + 0.6 * np.exp(-max(0, dt - 0.12) / 0.08) * (dt > 0.12)))
    return min(v, 1.0)


yv, xv = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xv - W / 2) / W) ** 2 + ((yv - H / 2) / H) ** 2)
VIGNETTE = np.clip(1.2 - 1.3 * rr ** 1.5, 0.2, 1.0)
GRAIN = [rng.normal(0, 6, (H, W)).astype(np.float32) for _ in range(6)]


def background(t: float) -> np.ndarray:
    fl = flash_amount(t)
    sky = SKY + fl * 120 * (1 - yy / BH * 0.6)
    # fog drifting at two speeds
    o1 = int(t * 60) % BW
    o2 = int(t * 25) % BW
    fog = 0.6 * FOG1[:, o1:o1 + BW] + 0.4 * FOG2[:, o2:o2 + BW]
    img = sky + fog * 28 * (0.4 + BAND)
    # far range (dark grey, lit a bit by lightning), near range (black)
    far_col = 22 + fl * 55
    img = img * (1 - FAR_MASK) + (far_col + fog * 10) * FAR_MASK
    img = img * (1 - NEAR_MASK) + (6 + fl * 18 + fog * 6) * NEAR_MASK
    img = img + BAND * fog * 22                                  # fog in front of mountains
    # lightning bolt visible for ~0.15s after each strike
    for at, amp in LIGHTNING.items():
        if 0 <= t - at < 0.16:
            img = img + (BOLT * 255 + BOLT_GLOW * 160) * amp * (1 - FAR_MASK)
    # rain falling fast
    ro = int(t * 2400) % BH
    img = img + RAIN[ro:ro + BH] * 55
    return img


def camera(img: np.ndarray, t: float) -> np.ndarray:
    push = 1.0 + 0.07 * (t / DUR)
    punch = 0.025 * kick_pulse(t, DROP, 0.09) + (0.04 if 0 <= t - DROP < 0.1 else 0)
    z = push + punch
    cw, ch = BW / OS / z * 1.0, BH / OS / z
    cx, cy = BW / 2, BH / 2
    # shake on the drop
    if 0 <= t - DROP < 0.35:
        s = 18 * np.exp(-(t - DROP) / 0.1)
        cx += rng.uniform(-s, s)
        cy += rng.uniform(-s, s)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    im = im.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
    return np.asarray(im, np.float32)


# ------------------------------------------------------------------ text
def word_layer(text: str, size: int, fpath: str = BLACK, color=(245, 245, 245), max_w=920) -> Image.Image:
    while True:
        f = ImageFont.truetype(fpath, size)
        l, t_, r_, b = f.getbbox(text)
        if r_ - l <= max_w:
            break
        size = int(size * 0.94)
    pad = 60
    img = Image.new("RGBA", (r_ - l + 2 * pad, b - t_ + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((pad - l, pad - t_ + 6), text, font=f, fill=(0, 0, 0, 200))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(sh)
    ImageDraw.Draw(img).text((pad - l, pad - t_), text, font=f, fill=color + (255,))
    return img


# Each card: (start kick, end kick, [(line text, size, font, color)])
GREY = (165, 165, 170)
CARDS = [
    (0, 1, [("IF YOU TRY", 150, BLACK, (245, 245, 245))]),
    (1, 2, [("you might", 90, SERIF_I, GREY), ("WIN.", 230, BLACK, (245, 245, 245))]),
    (2, 3, [("you might", 90, SERIF_I, GREY), ("LOSE.", 230, BLACK, (245, 245, 245))]),
    (3, 4, [("IF YOU", 150, BLACK, (245, 245, 245)), ("DON'T TRY", 150, BLACK, (245, 245, 245))]),
    (4, 5, [("you already", 90, SERIF_I, GREY), ("LOST.", 230, BLACK, (245, 245, 245))]),
    (5, 6, [("IT'S YOU", 190, BLACK, (245, 245, 245))]),
    (6, 7, [("VS YOU.", 210, BLACK, (245, 245, 245))]),
    (7, 8, [("YESTERDAY", 170, BLACK, (245, 245, 245))]),
    (8, 9, [("you said", 170, SERIF_I, (215, 215, 220))]),
    (9, 10, [("TOMORROW.", 170, BLACK, (245, 245, 245))]),
    (10, 11, [("DISCIPLINE", 170, BLACK, (245, 245, 245))]),
    (11, 12, [("over", 190, SERIF_I, (215, 215, 220))]),
    (12, 13, [("MOTIVATION.", 160, BLACK, (245, 245, 245))]),
    (13, 14, [("NO RISK.", 200, BLACK, (245, 245, 245))]),
    (14, 99, [("NO RISK.", 200, BLACK, (245, 245, 245)), ("NO STORY.", 200, BLACK, (245, 245, 245))]),
]
LAYERS = []
for a, b, lines in CARDS:
    imgs = [word_layer(t, s, f, c) for t, s, f, c in lines]
    w = max(i.width for i in imgs)
    h = sum(i.height for i in imgs) - 70 * (len(imgs) - 1)
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for im in imgs:
        card.alpha_composite(im, ((w - im.width) // 2, y))
        y += im.height - 70
    LAYERS.append((kick(a), kick(b), card))


def composite_text(frame: np.ndarray, t: float) -> np.ndarray:
    for a, b, card in LAYERS:
        if a <= t < b:
            break
    else:
        return frame
    lt = t - a
    if a == kick(14):                       # last card: no re-punch of "NO RISK."
        scale = 1.0 + 0.04 * (lt / (DUR - a))
    else:
        scale = 1.18 - 0.18 * ease_out(lt / 0.16)
    alpha = ease_out(lt / 0.06)
    if t > DUR - 0.35:
        alpha *= max(0.0, (DUR - t) / 0.35)
    cw, ch = int(card.width * scale), int(card.height * scale)
    c = card.resize((cw, ch), Image.BICUBIC)
    arr = np.asarray(c, np.float32)
    x0, y0 = W // 2 - cw // 2, int(H * 0.44) - ch // 2
    if 0 <= t - DROP < 0.3:
        s = int(14 * np.exp(-(t - DROP) / 0.08))
        x0 += int(rng.integers(-s, s + 1))
        y0 += int(rng.integers(-s, s + 1))
    xa, ya = max(0, x0), max(0, y0)
    xb, yb = min(W, x0 + cw), min(H, y0 + ch)
    sub = arr[ya - y0:yb - y0, xa - x0:xb - x0]
    al = sub[..., 3:4] / 255 * alpha
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    return frame


def render_frame(i: int) -> np.ndarray:
    t = i / FPS
    bg = camera(background(t), t)
    bg = bg * VIGNETTE + GRAIN[i % len(GRAIN)]
    frame = np.repeat(bg[..., None], 3, axis=2)
    frame *= np.array([0.97, 0.99, 1.03], np.float32)      # slightly cold B&W
    frame = composite_text(frame, t)
    if t < 0.12:
        frame *= ease_out(t / 0.12)
    if t > DUR - 0.3:
        frame *= max(0.0, (DUR - t) / 0.3)
    return np.clip(frame, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio + encode
def build_audio() -> Path:
    src, pre, out = HERE / "music_window.wav", HERE / "mix_prenorm.wav", HERE / "mix.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    f"afade=t=in:st=0:d=0.01,afade=t=out:st={DUR - 0.45}:d=0.45", str(pre)], check=True)
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
