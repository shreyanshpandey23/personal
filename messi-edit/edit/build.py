"""Messi kinetic-typography edit, beat-synced to QUINTA CONGA (5.21s-20.21s window).

Renders 1080x1920@30 frames with PIL/numpy, synthesizes SFX, mixes, loudnorms.
Usage: python build.py  (run from anywhere; paths are relative to this file)
"""
from __future__ import annotations

import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import butter, sosfilt

HERE = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(DUR * FPS)
SR = 48000
P = 0.5215                      # beat period (s), grid anchored on first kick = 0.0
B = lambda k: k * P              # beat k -> output time
DROP = B(8)                      # 4.17s, the big hit (9.38s in the track)

SKY = (117, 170, 219)            # Argentina sky blue #75AADB
WHITE = (245, 245, 245)
GOLD = (242, 193, 78)
BG = (8, 10, 16)

FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
for fp in (FONT_BLACK, FONT_BOLD):
    assert Path(fp).exists(), f"font missing: {fp}"


def ease_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 4 * t**3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


# ---------------------------------------------------------------- text cards
def text_layer(lines: list[tuple[str, str, int, tuple]], gap: int = 10, max_w: int = 820) -> Image.Image:
    """lines: (text, font_path, size, color). Each line auto-shrinks to max_w."""
    rendered = []
    for text, fpath, size, color in lines:
        while True:
            f = ImageFont.truetype(fpath, size)
            l, t, r, b = f.getbbox(text)
            if r - l <= max_w or size < 20:
                break
            size = int(size * 0.94)
        img = Image.new("RGBA", (r - l + 40, b - t + 40), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((20 - l, 20 - t), text, font=f, fill=color + (255,))
        rendered.append(img)
    w = max(i.width for i in rendered)
    h = sum(i.height for i in rendered) + gap * (len(rendered) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y = 0
    for i in rendered:
        out.paste(i, ((w - i.width) // 2, y), i)
        y += i.height + gap
    return out


def stars_layer(n: int = 3, r: int = 50) -> Image.Image:
    img = Image.new("RGBA", (n * r * 3, r * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i in range(n):
        cx, cy = r * 1.5 + i * r * 3, r + 4
        pts = []
        for k in range(10):
            ang = -np.pi / 2 + k * np.pi / 5
            rr = r if k % 2 == 0 else r * 0.42
            pts.append((cx + rr * np.cos(ang), cy + rr * np.sin(ang)))
        d.polygon(pts, fill=GOLD + (255,))
    return img


def big(text, color=WHITE, size=330):
    return (text, FONT_BLACK, size, color)


def small(text, color=SKY, size=78):
    return (text, FONT_BOLD, size, color)


# (start, end, layer, kind) kind: "intro" | "hit" | "stat" | "final"
CARDS: list[tuple[float, float, Image.Image, str]] = [
    (B(0), B(2), text_layer([small("FROM", WHITE, 90), big("ROSARIO", SKY, 230)]), "intro"),
    (B(2), B(4), text_layer([small("TO THE", WHITE, 90), big("WORLD", SKY, 280)]), "intro"),
    (B(4), B(5), text_layer([small("NUMBER", WHITE, 120)]), "intro"),
    (B(5), DROP, text_layer([big("10", SKY, 720)]), "ten"),
    (DROP, B(10), text_layer([big("MESSI", WHITE, 330)]), "hit"),
    (B(10), B(12), text_layer([big("8×", GOLD, 400), small("BALLON D'OR", WHITE)]), "stat"),
    (B(12), B(14), text_layer([big("2022", SKY, 330), small("WORLD CHAMPION", WHITE)]), "stat"),
    (B(14), B(16), text_layer([big("800+", WHITE, 330), small("CAREER GOALS", SKY)]), "stat"),
    (B(16), B(18), text_layer([big("91", SKY, 420), small("GOALS IN ONE YEAR", WHITE)]), "stat"),
    (B(18), B(20), text_layer([big("4×", WHITE, 400), small("CHAMPIONS LEAGUE", SKY)]), "stat"),
    (B(20), B(22), text_layer([big("2×", SKY, 400), small("COPA AMÉRICA", WHITE)]), "stat"),
    (B(22), B(23), text_layer([small("THERE IS", WHITE, 120)]), "quick"),
    (B(23), B(24), text_layer([small("ONLY ONE", SKY, 120)]), "quick"),
    (B(24), DUR + 1, text_layer([big("G.O.A.T", GOLD, 300), small("LIONEL MESSI · 10", WHITE, 64)], gap=24), "final"),
]
STARS = stars_layer()

# beats that get a zoom punch (all beats from the drop on, plus the intro kicks)
PUNCH_BEATS = [B(k) for k in range(0, 5)] + [B(k) for k in range(8, 29)]
FLASH_AT = {DROP: 1.0, B(24): 0.9, B(10): 0.35, B(14): 0.35, B(18): 0.35, B(22): 0.25}
SHAKE_AT = {DROP: 26.0, B(24): 20.0, B(10): 8.0, B(14): 8.0, B(18): 8.0, B(20): 6.0, B(12): 6.0, B(16): 6.0}


# ---------------------------------------------------------------- background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
GLOW = np.exp(-(r ** 2) / 0.06)[..., None]                       # centre glow mask
VIGNETTE = np.clip(1.15 - 1.1 * r ** 1.6, 0.25, 1.0)[..., None]
BASE = np.empty((H, W, 3), np.float32)
BASE[:] = BG
# faint flag bands (sky / white / sky)
band = (yy > H * 0.36) & (yy < H * 0.64)
FLAG = np.zeros((H, W, 3), np.float32)
FLAG[~band] = SKY
FLAG[band] = (200, 205, 215)
rng = np.random.default_rng(10)
GRAIN = [rng.normal(0, 7, (H, W, 1)).astype(np.float32) for _ in range(6)]


def pulse(t: float, beats: list[float], decay: float) -> float:
    """Sum of decaying envelopes from the most recent beat."""
    past = [b for b in beats if b <= t]
    if not past:
        return 0.0
    return float(np.exp(-(t - past[-1]) / decay))


def impulse(t: float, table: dict[float, float], decay: float) -> float:
    v = 0.0
    for at, amp in table.items():
        if 0 <= t - at < decay * 6:
            v = max(v, amp * np.exp(-(t - at) / decay))
    return v


def render_frame(i: int) -> np.ndarray:
    t = i / FPS
    post = t >= DROP
    beat_p = pulse(t, PUNCH_BEATS, 0.12)

    # background: dark + flag bands (stronger after drop) + beat glow
    flag_a = 0.05 if not post else 0.10 + 0.06 * beat_p
    if t >= B(24):
        flag_a = 0.12
    frame = BASE * (1 - flag_a) + FLAG * flag_a
    glow_col = np.array(GOLD if t >= B(24) else SKY, np.float32)
    glow_i = (0.10 if not post else 0.22) + 0.35 * beat_p * (1 if post else 0.5)
    if not post and t >= B(5):                                   # break: build glow tension
        glow_i = 0.10 + 0.45 * ease_in_out((t - B(5)) / (DROP - B(5)))
    frame = frame + GLOW * glow_col * glow_i

    # moving diagonal light streaks after drop
    if post:
        phase = (t * 900) % 600
        streak = np.exp(-(((xx + yy * 0.5 - phase) % 600 - 300) / 18) ** 2)[..., None]
        frame = frame + streak * 18 * (0.6 + beat_p)

    # active card
    for (a, b, layer, kind) in CARDS:
        if a <= t < b:
            break
    else:
        layer, kind, a, b = None, None, 0, 0

    shake = impulse(t, SHAKE_AT, 0.07)
    if layer is not None:
        lt = t - a
        if kind == "intro":
            scale = 0.92 + 0.08 * ease_out(lt / (b - a)) + 0.06 * beat_p
            alpha = ease_out(lt / 0.12)
        elif kind == "ten":
            k = ease_in_out(lt / (b - a))
            scale = 0.55 + 0.6 * k
            alpha = ease_out(lt / 0.15)
            shake = max(shake, 2 + 14 * k)                     # rising tension
        elif kind == "hit":
            scale = 1.25 - 0.25 * ease_out(lt / 0.22) + 0.10 * beat_p
            alpha = 1.0
        elif kind == "stat":
            scale = 1.30 - 0.30 * ease_out(lt / 0.18) + 0.08 * beat_p
            alpha = ease_out(lt / 0.05)
        elif kind == "quick":
            scale = 1.15 - 0.15 * ease_out(lt / 0.12)
            alpha = 1.0
        else:  # final: punch in, then slow push
            scale = 1.35 - 0.35 * ease_out(lt / 0.25) + 0.06 * (lt / (DUR - a)) + 0.04 * beat_p
            alpha = 1.0

        lw, lh = max(1, int(layer.width * scale)), max(1, int(layer.height * scale))
        L = layer.resize((lw, lh), Image.BICUBIC)
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ox = int(rng.uniform(-1, 1) * shake)
        oy = int(rng.uniform(-1, 1) * shake)
        cy = H // 2 - lh // 2 + oy
        canvas.paste(L, (W // 2 - lw // 2 + ox, cy), L)
        if kind == "final":
            s_scale = ease_out((t - a - 0.15) / 0.3)
            if s_scale > 0:
                st = STARS.resize((max(1, int(STARS.width * s_scale)), max(1, int(STARS.height * s_scale))), Image.BICUBIC)
                canvas.paste(st, (W // 2 - st.width // 2 + ox, cy - 150), st)
        arr = np.asarray(canvas, np.float32)
        a_ch = arr[..., 3:4] / 255.0 * alpha
        # soft drop-shadow glow behind text
        frame = frame * (1 - a_ch) + arr[..., :3] * a_ch

    # chromatic split at hits
    split = int(impulse(t, {DROP: 22, B(24): 18, B(10): 10, B(12): 8, B(14): 10, B(16): 8, B(18): 10, B(20): 8}, 0.06))
    if split > 0:
        frame[..., 0] = np.roll(frame[..., 0], -split, axis=1)
        frame[..., 2] = np.roll(frame[..., 2], split, axis=1)

    frame = frame * VIGNETTE + GRAIN[i % len(GRAIN)]

    # pre-drop blackout (last 2 frames before the hit), then flashes
    if DROP - 2 / FPS <= t < DROP:
        frame *= 0.15
    fl = impulse(t, FLASH_AT, 0.05)
    if fl > 0:
        frame = frame * (1 - fl) + 255 * fl
    # fade from black at start, short fade to black at very end
    if t < 0.15:
        frame *= ease_out(t / 0.15)
    if t > DUR - 0.35:
        frame *= max(0.0, (DUR - t) / 0.35)
    return np.clip(frame, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sound design
def bp_noise_sweep(dur, f0, f1, env, seed):
    n = int(dur * SR)
    rngs = np.random.default_rng(seed)
    out = np.zeros(n)
    steps = 24
    seg = n // steps
    noise = rngs.normal(0, 1, n + seg)
    for s in range(steps):
        fc = f0 * (f1 / f0) ** (s / (steps - 1))
        sos = butter(2, [max(30, fc * 0.6), min(SR / 2 - 100, fc * 1.6)], btype="band", fs=SR, output="sos")
        chunk = sosfilt(sos, noise[s * seg: s * seg + 2 * seg])
        win = np.hanning(2 * seg)
        a = s * seg
        e = min(n, a + 2 * seg)
        out[a:e] += (chunk * win)[: e - a]
    out *= env(np.linspace(0, 1, n))
    return out / (np.abs(out).max() + 1e-9)


def whoosh(dur=0.45, seed=1):
    # swell that peaks at the END (lands on the beat), quick tail cut
    return bp_noise_sweep(dur, 400, 5000, lambda x: x ** 2.2 * (1 - np.clip((x - 0.92) / 0.08, 0, 1)), seed)


def riser(dur):
    n = int(dur * SR)
    x = np.linspace(0, 1, n)
    noise = bp_noise_sweep(dur, 200, 7000, lambda x: x ** 2.5, 7)
    f = 180 * (1000 / 180) ** x
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * x ** 3
    return 0.7 * noise + 0.35 * tone


def impact(dur=1.1, f0=110, f1=38, punch=1.0, seed=3):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-tt / 0.08)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt / 0.35)
    rngs = np.random.default_rng(seed)
    crack = rngs.normal(0, 1, n) * np.exp(-tt / 0.025)
    sos = butter(2, 3500, btype="low", fs=SR, output="sos")
    crack = sosfilt(sos, crack)
    tail = sosfilt(butter(2, [300, 2500], btype="band", fs=SR, output="sos"), rngs.normal(0, 1, n)) * np.exp(-tt / 0.4) * 0.25
    sig = np.tanh(1.8 * punch * (body + 0.6 * crack + tail))
    return sig / np.abs(sig).max()


def tick(seed=5):
    n = int(0.08 * SR)
    tt = np.arange(n) / SR
    sig = np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt / 0.012)
    return sig


def read_wav(path: Path) -> np.ndarray:
    with wave.open(str(path)) as w:
        assert w.getframerate() == SR and w.getnchannels() == 2
        data = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return data.reshape(-1, 2)


def write_wav(path: Path, data: np.ndarray) -> None:
    data = np.clip(data, -1, 1)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((data * 32767).astype(np.int16).tobytes())


def build_audio() -> Path:
    music = read_wav(HERE / "music_window.wav")
    n = int(DUR * SR)
    music = music[:n]
    if len(music) < n:
        music = np.pad(music, ((0, n - len(music)), (0, 0)))
    # 10ms fade-in, 0.5s fade-out
    fi, fo = int(0.01 * SR), int(0.5 * SR)
    music[:fi] *= np.linspace(0, 1, fi)[:, None]
    music[-fo:] *= np.linspace(1, 0, fo)[:, None]

    sfx = np.zeros((n, 2))

    def place(sig, at, gain_db, pan=0.0):
        a = int(round(at * SR))
        e = min(n, a + len(sig))
        if a >= n or e <= 0:
            return
        g = 10 ** (gain_db / 20)
        l, r_ = g * (1 - max(0, pan)), g * (1 + min(0, pan))
        sfx[a:e, 0] += sig[: e - a] * l
        sfx[a:e, 1] += sig[: e - a] * r_

    events = []
    rs = riser(DROP - B(5))
    place(rs, B(5), -20); events.append(("riser", B(5)))
    place(impact(1.3, 120, 34, 1.2), DROP, -12); events.append(("impact", DROP))
    for k, seed, pan in [(10, 11, -0.4), (14, 12, 0.4), (18, 13, -0.3)]:
        w = whoosh(0.42, seed)
        place(w, B(k) - 0.42, -22, pan); events.append(("whoosh", B(k)))
    place(tick(), B(22), -24, -0.3); place(tick(), B(23), -24, 0.3); events.append(("ticks", B(22)))
    w = whoosh(0.5, 21)
    place(w, B(24) - 0.5, -21); events.append(("whoosh", B(24)))
    place(impact(1.6, 95, 30, 1.0, seed=8), B(24), -13); events.append(("impact", B(24)))

    mix = music + sfx
    pre = HERE / "mix_prenorm.wav"
    write_wav(pre, mix * 0.8)
    for name, at in events:
        print(f"  sfx {name:7s} @ {at:5.2f}s")
    return pre


def loudnorm(src: Path, dst: Path) -> None:
    import json
    f = "loudnorm=I=-14:TP=-1:LRA=11:print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af", f, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    f2 = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", f2, "-ar", str(SR), str(dst)], check=True)


def main() -> None:
    print("audio…")
    pre = build_audio()
    norm = HERE / "mix.wav"
    loudnorm(pre, norm)

    out = HERE / "final.mp4"
    print(f"video… {N} frames")
    proc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(norm),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ], stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(render_frame(i).tobytes())
        if i % 60 == 0:
            print(f"  frame {i}/{N}", flush=True)
    proc.stdin.close()
    assert proc.wait() == 0
    print(f"done: {out}")


if __name__ == "__main__":
    main()
