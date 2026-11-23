"""Two 9:16 GTA VI diving edits to "MONTAGEM CALMO" (Phonknight), beat-synced.

  python build.py 1   -> edit1_the_dive.mp4   (song 7.19-22.19s, drop at 2.40s)
  python build.py 2   -> edit2_the_reveal.mp4 (song 42.00-55.00s, drop at 6.00s)

Source is 1920x1080p60 gameplay. Each shot is a 506x900 crop (above the game's
bottom-centre mission text; minimap/watermark are outside it) scaled to 1080x1920.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "source" / "source.mp4"
SONG = "/root/.claude/uploads/3f3291ed-96fb-5d54-963a-e6516cb0d4a7/92bcce49-MONTAGEM_CALMO_-_Phonknight.m4a"
W, H, FPS = 1080, 1920, 30
CW, CH, CY = 506, 900, 10
SRC_FPS = 60.0
BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
for fp in (BLACK, BOLD):
    assert Path(fp).exists()
rng = np.random.default_rng(2)

EDIT = int(sys.argv[1]) if len(sys.argv) > 1 else 1
X = lambda f: int(min(1920 - CW, max(0, f * 1920 - CW / 2)))      # crop x from subject centre fraction

if EDIT == 1:
    NAME, SONG_T0, DUR, DROP = "edit1_the_dive", 7.19, 15.0, 2.40
    PRE_HITS = [1.22, 1.80]
    # (out_start, out_end, src_start, speed, centre_fraction, transition_in)
    SHOTS = [
        (0.00, 1.22, 24.30, 0.80, 0.50, None),     # boat hero shot
        (1.22, 1.80, 44.00, 1.00, 0.45, "whip"),   # crew gearing up
        (1.80, 2.40, 58.40, 1.00, 0.60, "whip"),   # jump -> splash on the drop
        (2.40, 3.60, 84.00, 1.00, 0.50, "flash"),  # underwater entry
        (3.60, 4.20, 102.0, 1.00, 0.50, "zoom"),
        (4.20, 4.80, 114.0, 1.00, 0.55, "whip"),
        (4.80, 6.00, 144.0, 1.00, 0.50, "zoom"),   # dark cave
        (6.00, 6.60, 198.0, 1.00, 0.50, "whip"),   # coral close
        (6.60, 7.20, 318.0, 1.00, 0.45, "whip"),   # diver close
        (7.20, 8.40, 482.5, 0.70, 0.55, "flash"),  # cave opening silhouettes
        (8.40, 9.00, 492.5, 1.00, 0.50, "zoom"),   # sunbeams
        (9.00, 9.60, 108.0, 1.00, 0.50, "whip"),
        (9.60, 10.80, 600.2, 1.00, 0.50, "zoom"),  # kelp
        (10.80, 11.40, 608.0, 1.00, 0.50, "whip"),  # reef
        (11.40, 12.00, 577.5, 1.00, 0.50, "whip"),  # fish school
        (12.00, 12.60, 675.6, 1.00, 0.50, "zoom"),  # camera breaks the surface
        (12.60, 13.20, 678.2, 1.00, 0.45, "whip"),  # surfacing at the boat
        (13.20, 15.10, 680.8, 1.00, 0.55, "flash"),  # cutscene close-up
    ]
    HOOK = [("GTA 6", 0.10, 0), ("UNDERWATER", 0.55, 1), ("IS INSANE", DROP, 2)]
    HOOK_UNTIL = 3.55
    LABELS = [("HIDDEN CAVES", 4.80, 6.00), ("THE LIGHTING", 7.20, 9.00), ("KELP FORESTS", 9.60, 10.80)]
    END_TEXT = [("WHO'S DIVING", 13.20), ("FIRST?", 13.80)]
else:
    NAME, SONG_T0, DUR, DROP = "edit2_the_reveal", 42.00, 13.0, 6.00
    PRE_HITS = [1.20, 2.40, 3.00, 3.60, 4.20, 4.80, 5.40]
    SHOTS = [
        (0.00, 1.20, 480.0, 0.80, 0.50, None),     # dark cave diver
        (1.20, 2.40, 482.5, 0.70, 0.55, "flash"),  # cave opening light
        (2.40, 3.00, 505.0, 1.00, 0.55, "whip"),   # silhouettes vs surface
        (3.00, 3.60, 570.0, 1.00, 0.50, "whip"),   # over the reef
        (3.60, 4.20, 575.0, 1.00, 0.50, "whip"),   # diving down
        (4.20, 4.80, 647.0, 1.00, 0.50, "whip"),   # bubbles
        (4.80, 5.40, 621.0, 1.00, 0.50, "whip"),   # fish
        (5.40, 6.00, 507.3, 0.60, 0.55, "zoom"),   # silhouettes, slow (no shark yet)
        (6.00, 7.19, 512.0, 1.00, 0.55, "flash"),  # SHARK on the drop
        (7.19, 7.80, 515.5, 1.00, 0.50, "whip"),
        (7.80, 8.99, 542.0, 1.00, 0.48, "flash"),  # turtle
        (8.99, 9.59, 626.0, 1.00, 0.55, "whip"),   # big fish
        (9.59, 10.79, 490.5, 0.80, 0.50, "zoom"),  # sunbeams
        (10.79, 11.38, 675.8, 1.00, 0.50, "zoom"),  # surface split
        (11.38, 11.99, 678.5, 1.00, 0.45, "whip"),  # surfacing
        (11.99, 13.10, 688.6, 1.00, 0.55, "flash"),  # cutscene
    ]
    HOOK = [("WAIT", 0.10, 0), ("FOR IT...", 0.60, 1)]
    HOOK_UNTIL = 2.40
    LABELS = [("GTA 6 HAS", 2.40, 4.20), ("A WHOLE OCEAN", 3.00, 4.20), ("SHARKS.", 6.00, 7.80), ("TURTLES.", 7.80, 8.99),
              ("GOD RAYS.", 9.59, 10.79)]
    END_TEXT = [("GTA 6 IS", 11.99), ("DIFFERENT.", 12.30)]

POST_KICKS = [DROP + 0.6 * k for k in range(0, 30) if DROP + 0.6 * k < DUR]
HATS = [DROP + 0.3 * k for k in range(1, 60, 2) if DROP + 0.3 * k < DUR]
CUTS = [s[0] for s in SHOTS[1:]]


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def recent(t, times, window):
    past = [x for x in times if x <= t and t - x < window]
    return t - past[-1] if past else None


# ------------------------------------------------------------------ source
def load_shot(src_start, span, x):
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-ss", f"{src_start:.3f}", "-i", str(SRC), "-t", f"{span + 0.1:.3f}",
                          "-vf", f"crop={CW}:{CH}:{x}:{CY}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True).stdout
    n = len(raw) // (CW * CH * 3)
    return [np.frombuffer(raw, np.uint8, CW * CH * 3, i * CW * CH * 3).reshape(CH, CW, 3) for i in range(n)]


FRAMES = [load_shot(s, (b - a) * sp, X(cx)) for (a, b, s, sp, cx, _) in SHOTS]
print(f"{NAME}: loaded {sum(len(f) for f in FRAMES)} source frames", flush=True)

# ------------------------------------------------------------------ look
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
VIGNETTE = np.clip(1.15 - 1.1 * rr ** 1.7, 0.35, 1.0)[..., None]
GRAIN = [rng.normal(0, 3.5, (H, W, 1)).astype(np.float32) for _ in range(5)]


def grade(f):
    lum = f.mean(axis=2, keepdims=True)
    f = lum + (f - lum) * 1.18                               # richer colour
    f = (f - 128) * 1.12 + 126                               # contrast
    l = lum / 255
    f = f + (1 - l) * np.array([-4, 3, 7], np.float32) + l * np.array([6, 3, -3], np.float32)
    return f


# ------------------------------------------------------------------ text
_cache = {}


def text_img(txt, fpath, size, fill=(255, 255, 255), stroke=0, shadow=True):
    key = (txt, fpath, size, fill, stroke)
    if key in _cache:
        return _cache[key]
    f = ImageFont.truetype(fpath, size)
    while f.getlength(txt) > 980 and size > 30:
        size = int(size * 0.94)
        f = ImageFont.truetype(fpath, size)
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    pad = 40
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - t + 8), txt, font=f, fill=(0, 0, 0, 200), stroke_width=stroke)
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    ImageDraw.Draw(im).text((pad - l, pad - t), txt, font=f, fill=fill + (255,),
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    arr = np.asarray(im, np.float32)
    _cache[key] = arr
    return arr


def paste(frame, arr, cx, cy, alpha=1.0, scale=1.0):
    if scale != 1.0:
        im = Image.fromarray(arr.astype(np.uint8)).resize((max(1, int(arr.shape[1] * scale)), max(1, int(arr.shape[0] * scale))), Image.BICUBIC)
        arr = np.asarray(im, np.float32)
    h, w = arr.shape[:2]
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya:
        return
    sub = arr[ya - y0:yb - y0, xa - x0:xb - x0]
    a = sub[..., 3:4] / 255 * alpha
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - a) + sub[..., :3] * a


ACCENT = (255, 214, 64)


def draw_text(frame, t):
    # hook: stacked words that slam in
    if t < HOOK_UNTIL:
        fade = 1.0 if t < HOOK_UNTIL - 0.25 else (HOOK_UNTIL - t) / 0.25
        for txt, at, line in HOOK:
            if t >= at:
                p = ease_out((t - at) / 0.14)
                col = ACCENT if at == DROP or txt.endswith("...") else (255, 255, 255)
                arr = text_img(txt, BLACK, 150 if line < 2 else 170, col)
                paste(frame, arr, W / 2, H * 0.20 + line * 165, alpha=fade * min(1, p * 2), scale=1.35 - 0.35 * p)
    # labels: slide in from left with an accent bar
    for txt, a, b in LABELS:
        if a <= t < b:
            p = ease_out((t - a) / 0.18)
            out = 1.0 if b - t > 0.12 else (b - t) / 0.12
            arr = text_img(txt, BLACK, 110, (255, 255, 255))
            stacked = sum(1 for l in LABELS if l[1] < t < l[2] and l[1] < a)
            cy = H * 0.66 + stacked * 120
            cx = W / 2 - (1 - p) * 300
            bar_w = int(arr.shape[1] * 0.6 * p)
            frame[int(cy + arr.shape[0] / 2 - 30):int(cy + arr.shape[0] / 2 - 18), int(W / 2 - bar_w / 2):int(W / 2 + bar_w / 2)] = ACCENT
            paste(frame, arr, cx, cy, alpha=p * out)
    # end text
    for i, (txt, at) in enumerate(END_TEXT):
        if t >= at:
            p = ease_out((t - at) / 0.16)
            col = ACCENT if i == len(END_TEXT) - 1 else (255, 255, 255)
            paste(frame, text_img(txt, BLACK, 150, col), W / 2, H * 0.22 + i * 170, alpha=min(1, p * 2), scale=1.3 - 0.3 * p)


# ------------------------------------------------------------------ frame
def shot_frame(si, t):
    a, b, s, sp, cx, tin = SHOTS[si]
    frames = FRAMES[si]
    lt = t - a
    fi = min(len(frames) - 1, int(lt * sp * SRC_FPS))
    return frames[fi], lt


def render_frame(i):
    t = i / FPS
    si = max(j for j, sh in enumerate(SHOTS) if sh[0] <= t)
    a, b, s, sp, cx, tin = SHOTS[si]
    src, lt = shot_frame(si, t)

    # zoom: cut punch, kick punch, hat micro-punch, slow push
    z = 1.0 + 0.04 * lt / max(0.6, b - a)
    if t >= DROP:
        z += 0.14 * (1 - ease_out(lt / 0.2))
        dk = recent(t, POST_KICKS, 0.3)
        if dk is not None and t - dk > a:
            z += 0.05 * np.exp(-dk / 0.07)
        dh = recent(t, HATS, 0.2)
        if dh is not None:
            z += 0.018 * np.exp(-dh / 0.05)
    else:
        z += 0.06 * (1 - ease_out(lt / 0.2)) if si > 0 else 0
    shake = 0.0
    if 0 <= t - DROP < 0.35:
        shake = 22 * np.exp(-(t - DROP) / 0.09)
    cw, ch = CW / z, CH / z
    ox = rng.uniform(-1, 1) * shake / 2.0
    oy = rng.uniform(-1, 1) * shake / 2.0
    # whip-pan in: incoming frame slides from the right with motion blur
    whip = tin == "whip" and lt < 0.1
    box = (CW / 2 - cw / 2 + ox, CH / 2 - ch / 2 + oy, CW / 2 + cw / 2 + ox, CH / 2 + ch / 2 + oy)
    img = Image.fromarray(src).resize((W, H), Image.BICUBIC, box=box)
    img = img.filter(ImageFilter.UnsharpMask(radius=2, percent=60, threshold=2))
    frame = np.asarray(img, np.float32).copy()
    if whip:
        k = 1 - lt / 0.1
        shift = int(260 * k)
        acc = np.zeros_like(frame)
        for j in range(6):
            acc += np.roll(frame, shift - j * shift // 6, axis=1)
        frame = acc / 6
    # zoom-blur in
    if tin == "zoom" and lt < 0.1:
        k = 1 - lt / 0.1
        im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
        acc = frame.copy()
        for j in range(1, 5):
            s2 = 1 + 0.05 * j * k
            acc += np.asarray(im.resize((W, H), Image.BILINEAR, box=(W / 2 - W / s2 / 2, H / 2 - H / s2 / 2, W / 2 + W / s2 / 2, H / 2 + H / s2 / 2)), np.float32)
        frame = acc / 5

    frame = grade(frame)
    # RGB split on cuts after the drop
    if t >= DROP and lt < 0.08:
        px = int(14 * (1 - lt / 0.08)) + (10 if abs(t - DROP) < 0.1 else 0)
        frame[..., 0] = np.roll(frame[..., 0], -px, axis=1)
        frame[..., 2] = np.roll(frame[..., 2], px, axis=1)
    frame = frame * VIGNETTE + GRAIN[i % len(GRAIN)]

    # pre-drop: pulse on the build hits, darken into the drop
    for h in PRE_HITS:
        if 0 <= t - h < 0.15:
            frame *= 1 + 0.25 * np.exp(-(t - h) / 0.04)
    if DROP - 0.25 <= t < DROP:
        frame *= 1 - 0.55 * (t - (DROP - 0.25)) / 0.25
    # flashes
    if tin == "flash" and lt < 0.2:
        amp = (0.9 if abs(a - DROP) < 1e-6 else 0.55) * np.exp(-lt / 0.05)
        frame = frame * (1 - amp) + 255 * amp

    draw_text(frame, t)
    if t < 0.1:
        frame *= ease_out(t / 0.1)
    if t > DUR - 0.35:
        frame *= max(0.0, (DUR - t) / 0.35)
    return np.clip(frame, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio + encode
def build_audio():
    pre, out = HERE / f"{NAME}_prenorm.wav", HERE / f"{NAME}.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{SONG_T0}", "-t", f"{DUR}", "-i", SONG,
                    "-af", f"afade=t=in:st=0:d=0.02,afade=t=out:st={DUR - 0.45}:d=0.45", "-ac", "2", "-ar", "48000", str(pre)], check=True)
    f = "loudnorm=I=-14:TP=-2:LRA=11:print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af", f, "-f", "null", "-"], capture_output=True, text=True)
    m = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    f2 = (f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", f2, "-ar", "48000", str(out)], check=True)
    return out


def main():
    audio = build_audio()
    out = HERE / f"{NAME}.mp4"
    n = int(DUR * FPS)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                             "-i", str(audio), "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
                             "-maxrate", "14M", "-bufsize", "28M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                             "-shortest", "-movflags", "+faststart", str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(render_frame(i).tobytes())
    proc.stdin.close()
    assert proc.wait() == 0
    print(f"done: {out}")


if __name__ == "__main__":
    main()
