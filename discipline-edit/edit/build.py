"""Discipline-tracker edit, inspired by a dashboard + quote-inset reel.

Dark UI dashboard (non-money tracker) with a quote inset that changes on the
kicks of "Belo Ritmo Salsa" (window 10.49s-24.49s, drop at 4.00s output).
Usage: python build.py   (paths relative to this file)
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 14.0
N = int(DUR * FPS)
K = 0.80                      # kick period (s); kicks at 0, 0.8, 1.6, ...
kick = lambda k: k * K
DROP = kick(5)                # 4.00s

INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_SB = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
INTER_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
INTER_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
INTER_BLK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
for fp in (INTER, INTER_SB, INTER_B, INTER_XB, INTER_BLK, SERIF):
    assert Path(fp).exists(), f"font missing: {fp}"

_fc: dict = {}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    key = (path, size)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(path, size)
    return _fc[key]


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def ease_io(t):
    t = min(max(t, 0.0), 1.0)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def kick_pulse(t, start=0.0, decay=0.10):
    if t < start:
        return 0.0
    k = int(t / K)
    return float(np.exp(-(t - k * K) / decay))


# ------------------------------------------------------------------ dashboard
CARD = (22, 22, 24)
LINE = (38, 38, 42)
GRAY = (140, 140, 146)
WHITE = (240, 240, 242)
ORANGE, BLUE, PURPLE, STEEL = (242, 140, 40), (80, 140, 245), (160, 120, 245), (200, 200, 206)
GREEN = (60, 210, 120)

INSET = (40, 1090, 440, 1490)     # x0, y0, x1, y1 (400x400)


def icon(d: ImageDraw.ImageDraw, cx, cy, kind):
    tint = {"clock": ORANGE, "cal": BLUE, "bolt": PURPLE, "lock": STEEL}[kind]
    bg = tuple(int(c * 0.22) for c in tint)
    d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=bg)
    if kind == "clock":
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=tint)
        d.line((cx, cy, cx, cy - 10), fill=bg, width=4)
        d.line((cx, cy, cx + 8, cy + 4), fill=bg, width=4)
    elif kind == "cal":
        d.rounded_rectangle((cx - 16, cy - 14, cx + 16, cy + 16), 5, outline=tint, width=4)
        d.line((cx - 16, cy - 5, cx + 16, cy - 5), fill=tint, width=4)
        d.line((cx - 8, cy - 20, cx - 8, cy - 10), fill=tint, width=4)
        d.line((cx + 8, cy - 20, cx + 8, cy - 10), fill=tint, width=4)
    elif kind == "bolt":
        d.polygon([(cx + 4, cy - 20), (cx - 12, cy + 3), (cx - 1, cy + 3), (cx - 5, cy + 20),
                   (cx + 12, cy - 4), (cx + 1, cy - 4)], fill=tint)
    else:  # lock
        d.rounded_rectangle((cx - 15, cy - 4, cx + 15, cy + 18), 4, fill=tint)
        d.arc((cx - 10, cy - 20, cx + 10, cy + 4), 180, 360, fill=tint, width=4)


def dashboard(t: float) -> Image.Image:
    """Full 1080x1920 dashboard for time t (counters tick on the drop)."""
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    after = t >= DROP
    # main card
    d.rounded_rectangle((30, 520, 1050, 960), 28, fill=CARD)
    d.text((72, 556), "Days locked in", font=font(INTER_SB, 30), fill=GRAY)
    # streak counter: 141 -> 142 rolls on the drop
    roll = ease_out((t - DROP) / 0.22) if after else 0.0
    big = font(INTER_SB, 92)
    clip = Image.new("RGBA", (360, 110), (0, 0, 0, 0))
    cd = ImageDraw.Draw(clip)
    cd.text((0, -10 - 110 * roll), "141", font=big, fill=WHITE)
    cd.text((0, 100 - 110 * roll), "142", font=big, fill=GREEN if 0 < t - DROP < 0.8 else WHITE)
    img.paste(clip, (66, 600), clip)
    d.rounded_rectangle((850, 600, 1010, 656), 28, fill=(34, 34, 38))
    d.text((930, 628), "Keep going", font=font(INTER_SB, 24), fill=WHITE, anchor="mm")
    tiles = [
        ("clock", "5:00 AM", "Wake up"),
        ("cal", "6 / 6" if after else "5 / 6", "Workouts this week"),
        ("bolt", "38 h", "Deep work this month"),
        ("lock", "0", "Excuses"),
    ]
    for i, (kind, val, lab) in enumerate(tiles):
        x = 72 if i % 2 == 0 else 560
        y = 760 if i < 2 else 870
        icon(d, x + 38, y + 30, kind)
        col = GREEN if (kind == "cal" and 0 < t - DROP < 0.8) else WHITE
        d.text((x + 100, y + 2), val, font=font(INTER_SB, 34), fill=col)
        d.text((x + 100, y + 42), lab, font=font(INTER, 24), fill=GRAY)
    # dropdown pill
    d.rounded_rectangle((560, 1000, 900, 1056), 28, fill=(26, 26, 28), outline=LINE, width=2)
    d.rounded_rectangle((592, 1016, 614, 1040), 4, outline=WHITE, width=3)
    d.text((630, 1028), "All time", font=font(INTER_SB, 26), fill=WHITE, anchor="lm")
    d.line((858, 1022, 868, 1032), fill=WHITE, width=3)
    d.line((868, 1032, 878, 1022), fill=WHITE, width=3)
    # right column next to the inset
    lab ="Current streak: "
    val = "142 days" if after else "141 days"
    vw = font(INTER_B, 30).getlength(val)
    d.text((1040 - vw, 1120), lab, font=font(INTER, 30), fill=GRAY, anchor="rm")
    d.text((1040, 1120), val, font=font(INTER_B, 30), fill=WHITE, anchor="rm")
    lab2, val2 = "Excuses: ", "0"
    vw2 = font(INTER_B, 30).getlength(val2)
    d.text((1040 - vw2, 1196), lab2, font=font(INTER, 30), fill=GRAY, anchor="rm")
    d.text((1040, 1196), val2, font=font(INTER_B, 30), fill=WHITE, anchor="rm")
    return img


# ------------------------------------------------------------------ inset art
S = 400
PAPER = (238, 233, 220)
GREY_PAPER = (206, 203, 196)
INK = (35, 33, 30)
HILITE = (205, 222, 60)
rng = np.random.default_rng(4)


def paper(size, base, amount=6):
    arr = np.ones((size[1], size[0], 3), np.float32) * np.array(base, np.float32)
    arr += rng.normal(0, amount, (size[1], size[0], 1))
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


# Tree diagram on a big sheet; the inset "camera" moves across it.
TREE_SZ = (1600, 1200)
TREE = paper(TREE_SZ, PAPER)
_td = ImageDraw.Draw(TREE)
_f = font(SERIF, 96)
_td.text((120, 560), "if you", font=_f, fill=INK, anchor="lm")
_td.line((410, 300, 410, 840), fill=INK, width=5)
_td.line((410, 300, 560, 300), fill=INK, width=5)
_td.line((410, 840, 560, 840), fill=INK, width=5)
_td.text((580, 300), "try", font=_f, fill=INK, anchor="lm")
_td.line((730, 300, 860, 300), fill=INK, width=5)
_td.line((860, 160, 860, 440), fill=INK, width=5)
_td.line((860, 160, 960, 160), fill=INK, width=5)
_td.line((860, 440, 960, 440), fill=INK, width=5)
_td.text((980, 160), "win", font=_f, fill=INK, anchor="lm")
_td.text((980, 440), "lose", font=_f, fill=INK, anchor="lm")
_td.text((580, 840), "don't try", font=_f, fill=INK, anchor="lm")
_td.line((960, 840, 1080, 840), fill=INK, width=5)
_td.text((1100, 840), "lose", font=_f, fill=INK, anchor="lm")

PAD = 500
TREE_PADDED = paper((TREE_SZ[0] + 2 * PAD, TREE_SZ[1] + 2 * PAD), PAPER)
TREE_PADDED.paste(TREE, (PAD, PAD))

# camera keyframes (center x, center y, view size) at each kick 0..5
TREE_KEYS = [
    (780, 520, 1560),   # whole diagram
    (330, 560, 560),    # "if you"
    (700, 300, 640),    # "try"
    (1000, 300, 520),   # win / lose
    (850, 840, 700),    # don't try - lose
    (1200, 840, 420),   # "lose"
]


def tree_view(lt: float) -> Image.Image:
    k = min(int(lt / K), len(TREE_KEYS) - 1)
    a = TREE_KEYS[k]
    b = TREE_KEYS[min(k + 1, len(TREE_KEYS) - 1)]
    # hold most of the kick, glide in the last 45%
    u = ease_io((lt - k * K) / K * 1.8 - 0.8)
    cx, cy, vs = [a[i] + (b[i] - a[i]) * u for i in range(3)]
    vs *= 1 - 0.04 * kick_pulse(lt, 0, 0.12)
    box = (PAD + cx - vs / 2, PAD + cy - vs / 2, PAD + cx + vs / 2, PAD + cy + vs / 2)
    return TREE_PADDED.resize((S, S), Image.BICUBIC, box=box)


def vs_quote(lt: float) -> Image.Image:
    """'It's you vs you.' with a highlighter swipe, then a punch-in."""
    big = paper((800, 800), GREY_PAPER, 7)
    d = ImageDraw.Draw(big, "RGBA")
    f = font(SERIF, 88)
    text = "It's you vs you."
    tw = f.getlength(text)
    x0, y = 400 - tw / 2, 400
    sw = ease_out(lt / 0.35)
    d.rectangle((x0 - 14, y - 52, x0 - 14 + (tw + 28) * sw, y + 40), fill=HILITE + (230,))
    d.text((x0, y), text, font=f, fill=INK, anchor="lm")
    # view: full line, punch in on "you vs you" on the 2nd kick
    if lt < K:
        vs, cx = 760 - 40 * ease_out(lt / K), 400
    else:
        vs, cx = 470 - 30 * ease_out((lt - K) / K), 470
    vs *= 1 - 0.05 * kick_pulse(lt, 0, 0.1)
    return big.resize((S, S), Image.BICUBIC, box=(cx - vs / 2, 400 - vs / 2, cx + vs / 2, 400 + vs / 2))


def billboard(lt: float, words: list[str]) -> Image.Image:
    """Grey building wall with a white panel; one line lands per kick."""
    img = Image.new("RGB", (S, S), (70, 72, 76))
    d = ImageDraw.Draw(img)
    for x in range(0, S, 26):                        # windows of the building
        d.rectangle((x + 4, 0, x + 18, S), fill=(52, 54, 58))
    push = 1 + 0.06 * ease_out(lt / (K * len(words)))
    pw, ph = int(310 * push), int(340 * push)
    px, py = S // 2 - pw // 2, S // 2 - ph // 2 + 30
    d.rectangle((px, py, px + pw, py + ph), fill=(236, 236, 232))
    f = font(INTER_BLK, int(36 * push))
    n = min(len(words), int(lt / K) + 1)
    for i in range(n):
        a = ease_out((lt - i * K) / 0.12)
        yy = py + 40 * push + i * 52 * push - (1 - a) * 18
        col = tuple(int(255 - (255 - c) * a) for c in (20, 20, 22))
        d.text((px + 22 * push, yy), words[i], font=f, fill=col)
    return img


def black_words(lt: float, lines: list[tuple[str, str, int, tuple]], per=K) -> Image.Image:
    img = Image.new("RGB", (S, S), (6, 6, 8))
    d = ImageDraw.Draw(img)
    n = min(len(lines), int(lt / per) + 1)
    total_h = sum(sz + 14 for _, _, sz, _ in lines) - 14
    y = S / 2 - total_h / 2
    for i, (txt, fp, sz, col) in enumerate(lines):
        if i < n:
            a = ease_out((lt - i * per) / 0.15)
            c = tuple(int(v * a) for v in col)
            d.text((S / 2, y + sz / 2 + (1 - a) * 12), txt, font=font(fp, sz), fill=c, anchor="mm")
        y += sz + 14
    return img


def no_risk(lt: float) -> Image.Image:
    img = Image.new("RGB", (S, S), (6, 6, 8))
    d = ImageDraw.Draw(img)
    f = font(SERIF, 33)
    a = ease_out(lt / 0.3)
    b = ease_out((lt - K) / 0.3)
    col_a = tuple(int(220 * a) for _ in range(3))
    col_b = tuple(int(220 * b) for _ in range(3))
    d.text((S / 2 - 12, S / 2), "NO RISK.", font=f, fill=col_a, anchor="rm")
    d.text((S / 2 + 12, S / 2), "NO STORY.", font=f, fill=col_b, anchor="lm")
    if lt > 2 * K:                                 # small sign-off line
        c = ease_out((lt - 2 * K) / 0.3)
        d.text((S / 2, S / 2 + 60), "day 142.", font=font(SERIF, 28),
               fill=tuple(int(150 * c) for _ in range(3)), anchor="mm")
    return img


# (start, end, renderer(lt)) on the kick grid
SCENES = [
    (kick(0), kick(5), tree_view),
    (kick(5), kick(7), vs_quote),
    (kick(7), kick(10), lambda lt: billboard(lt, ["YESTERDAY", "YOU SAID", "TOMORROW."])),
    (kick(10), kick(13), lambda lt: black_words(lt, [
        ("DISCIPLINE", INTER_BLK, 50, (245, 245, 245)),
        (">", INTER_BLK, 50, (205, 222, 60)),
        ("MOTIVATION", INTER_BLK, 50, (120, 120, 126)),
    ])),
    (kick(13), DUR + 1, no_risk),
]
CUTS = [s for s, _, _ in SCENES[1:]]


def render_frame(i: int) -> np.ndarray:
    t = i / FPS
    base = dashboard(t)
    for a, b, fn in SCENES:
        if a <= t < b:
            inset = fn(t - a)
            break
    # quick white flash on every scene cut, extra strong on the drop
    arr = np.asarray(inset, np.float32)
    for c in CUTS:
        if 0 <= t - c < 0.2:
            amp = 0.85 if c == DROP else 0.45
            arr = arr + (255 - arr) * amp * np.exp(-(t - c) / 0.05)
    inset = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    base.paste(inset, INSET[:2])

    # subtle whole-frame punch on kicks after the drop
    p = kick_pulse(t, DROP, 0.09)
    z = 1 + 0.018 * p + (0.03 if 0 <= t - DROP < 0.12 else 0)
    if z > 1.0005:
        cw, ch = W / z, H / z
        base = base.resize((W, H), Image.BICUBIC, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
    out = np.asarray(base, np.float32)
    if t < 0.12:
        out *= ease_out(t / 0.12)
    if t > DUR - 0.3:
        out *= max(0.0, (DUR - t) / 0.3)
    return np.clip(out, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio
def build_audio() -> Path:
    src = HERE / "music_window.wav"
    pre = HERE / "mix_prenorm.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af",
                    f"afade=t=in:st=0:d=0.01,afade=t=out:st={DUR - 0.45}:d=0.45", str(pre)], check=True)
    f = "loudnorm=I=-14:TP=-1:LRA=11:print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af", f, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    f2 = (f"loudnorm=I=-14:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    out = HERE / "mix.wav"
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
