"""DROP version. 9:16 beat-synced edit of the BTS "2.0" MV to "Vintage Vuitton" (earfzilla),
with lyric words placed BEHIND the members (MODNet person matte).

Song window 21.82s-36.82s (15s). Drop at 1.89s output; 8th-note grid 0.4725s.
Run with /root/tools-venv/bin/python (needs onnxruntime for seg.py).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from seg import matte  # noqa: E402

SRC = HERE.parent / "source" / "bts_2.0_mv.mp4"
SONG = "/root/.claude/uploads/3f3291ed-96fb-5d54-963a-e6516cb0d4a7/f2b08d75-Vintage_Vuitton_-_earfzilla.m4a"
SONG_T0 = 21.82
W, H, FPS, DUR = 1080, 1920, 30, 15.0
N = int(DUR * FPS)
CW, CH, CY = 450, 800, 140          # 9:16 crop from the letterboxed 1920x800 picture
SRC_FPS = 24000 / 1001
DROP = 1.89
G = 0.4725
g = lambda k: DROP + k * G
KICKS = [g(k) for k in range(0, 30, 2)]          # kick every 2 grid steps after the drop

FONT = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
assert Path(FONT).exists()
rng = np.random.default_rng(1)

# (out_start, out_end, src_start, speed, crop_x, lyric_words)
# lyric_words: list of (text, appear_time, line) shown BEHIND the person
SHOTS = [
    (0.00, DROP, 5.25, 1.00, 543, [], 0),                                     # elevator floor counter (tease)
    (DROP, g(1), 146.30, 1.00, 40, [], 0),                                    # RM lunge + "2.0 LOADING" - freeze on drop
    (g(1), g(4), 135.10, 1.00, 831, [("LATE", g(1), 0), ("NIGHTS", 2.74, 1)], 0.12),     # bathroom group
    (g(4), g(6), 203.90, 1.00, 735, [("DELAYED", 3.96, 0), ("FLIGHTS", 4.56, 1)], 0.24),  # window trio
    (g(6), g(7), 9.00, 1.00, 831, [], 0),                                    # elevator crowd
    (g(7), g(8), 138.00, 1.00, 351, [], 0),                                  # J-Hope bathroom
    (g(8), g(12), 161.00, 0.90, 889, [("RANDOM", 5.98, 0), ("COUNTRY", 6.42, 1)], 0.33),  # hall dance wide
    (g(12), g(15), 195.60, 1.00, 735, [("UNDER", 7.56, 0), ("STAGE", 7.88, 1), ("LIGHTS", 8.34, 2)], 0.30),  # window group
    (g(15), g(16), 194.60, 1.00, 831, [], 0),                                # red jacket
    (g(16), g(17), 138.60, 1.00, 1157, [], 0),                               # Jungkook bathroom
    (g(17), g(19), 132.35, 1.00, 735, [("STAGE", g(17), 0), ("FRIGHT", 10.26, 1)], 0.20),  # bathroom group
    (g(19), g(20), 33.15, 1.00, 658, [], 0),                                 # Jin close
    (g(20), g(21), 23.80, 1.00, 831, [], 0),                                 # Jimin close
    (g(21), g(22), 35.20, 1.00, 581, [], 0),                                 # V close
    (g(22), g(26), 200.50, 1.00, 735, [("I DON'T HAVE", 12.48, 0), ("A CLUE", 13.42, 1)], 0.30),  # window group
    (g(26), DUR + 0.1, 205.00, 1.00, 831, [("WHAT'S IN", 14.12, 0), ("STORE", 14.54, 1)], 0.22),  # window trio ending
]
# lyric shown in FRONT (small) over the fast cuts
FRONT_LYRICS = [("NO TIME FOR", 9.14, g(17))]
ZOOM_BLUR_OUT = {3, 7, 14}       # shots whose last frames get a zoom-blur transition


def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


# ------------------------------------------------------------------ source frames
def load_shot(src_start: float, span: float, x: int) -> list[np.ndarray]:
    """x is a crop offset, or (x_start, x_end) for a pan that follows the subject."""
    pan = isinstance(x, tuple)
    cw = 1920 if pan else CW
    raw = subprocess.run([
        "ffmpeg", "-v", "quiet", "-err_detect", "ignore_err", "-ss", f"{src_start:.3f}", "-i", str(SRC),
        "-t", f"{span + 0.2:.3f}", "-vf", f"crop={cw}:{CH}:{0 if pan else x}:{CY}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    n = len(raw) // (cw * CH * 3)
    frames = [np.frombuffer(raw, np.uint8, cw * CH * 3, i * cw * CH * 3).reshape(CH, cw, 3) for i in range(n)]
    if pan:
        nf = max(1, min(n, int(span * SRC_FPS) + 1) - 1)
        frames = [f[:, int(x[0] + (x[1] - x[0]) * ease(min(1, i / nf))):][:, :CW].copy() for i, f in enumerate(frames)]
    return frames


def ease(t):
    return t * t * (3 - 2 * t)


FRAMES = []
for (a, b, s, sp, x, _, _) in SHOTS:
    FRAMES.append(load_shot(s, (b - a) * sp, x))
    print(f"loaded shot @{s:7.2f}s: {len(FRAMES[-1])} frames", flush=True)
MATTES: dict[tuple[int, int], np.ndarray] = {}


# ------------------------------------------------------------------ look
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2)
VIGNETTE = np.clip(1.18 - 1.2 * rr ** 1.6, 0.3, 1.0)[..., None]
GRAIN = [rng.normal(0, 4.5, (H, W, 1)).astype(np.float32) for _ in range(5)]


def grade(f: np.ndarray, sat: float) -> np.ndarray:
    lum = f.mean(axis=2, keepdims=True)
    f = lum + (f - lum) * sat
    f = (f - 128) * 1.10 + 124                       # contrast
    l = lum / 255
    f = f + (1 - l) * np.array([-6, 2, 8], np.float32) + l * np.array([8, 2, -6], np.float32)  # teal/orange split
    return f


def word_img(text: str, size: int, stroke: int = 0) -> Image.Image:
    f = ImageFont.truetype(FONT, size)
    l, t, r, b = f.getbbox(text, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 20, b - t + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10 - l, 10 - t), text, font=f, fill=(255, 255, 255, 255),
                            stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
    return im


def fit_size(text: str, want: int, max_w: int = 1040) -> int:
    s = want
    while ImageFont.truetype(FONT, s).getlength(text) > max_w and s > 40:
        s = int(s * 0.95)
    return s


# ------------------------------------------------------------------ frame
def render_frame(i: int) -> np.ndarray:
    t = i / FPS
    for si, (a, b, s, sp, x, words, ty) in enumerate(SHOTS):
        if a <= t < b:
            break
    lt = t - a
    frames = FRAMES[si]
    lt_src = max(0.0, lt - 0.16) if si == 1 else lt          # freeze-frame on the drop
    fi = min(len(frames) - 1, int(lt_src * sp * SRC_FPS))
    src = frames[fi]

    # zoom: cut punch + kick punch + slow push (pre-drop shots push slowly, no punch)
    if t < DROP:
        z = 1.0 + 0.10 * lt / (b - a)
    else:
        z = 1.0 + 0.16 * (1 - ease_out(lt / 0.22)) + 0.03 * lt / max(0.4, b - a)
        past = [k for k in KICKS if k <= t]
        if past and t - past[-1] < 0.3 and past[-1] > a + 0.05:
            z += 0.045 * np.exp(-(t - past[-1]) / 0.08)
    if si == len(SHOTS) - 1:
        z = 1.0 + 0.12 * (1 - ease_out(lt / 0.22)) + 0.08 * lt / (DUR - a)
    shake = 0.0
    if 0 <= t - DROP < 0.4:
        shake = 16 * np.exp(-(t - DROP) / 0.1)
    elif t > DROP and lt < 0.12:
        shake = 5.0
    cw, ch = CW / z, CH / z
    cx = CW / 2 + rng.uniform(-1, 1) * shake / 2.4
    cy = CH / 2 + rng.uniform(-1, 1) * shake / 2.4
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    img = Image.fromarray(src).resize((W, H), Image.LANCZOS, box=box)
    img = img.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    frame = np.asarray(img, np.float32)

    # lyrics behind the person
    if words:
        key = (si, fi)
        if key not in MATTES:
            MATTES[key] = matte(src)
        m = Image.fromarray((MATTES[key] * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR, box=box)
        m = np.asarray(m, np.float32)[..., None] / 255
        layer = np.zeros((H, W, 4), np.float32)
        n_lines = max(w[2] for w in words) + 1
        size = 290 if n_lines == 2 else 240
        line_h = size * 0.98
        top = H * ty - line_h * n_lines / 2
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for text, at, line in words:
            if t < at:
                continue
            p = ease_out((t - at) / 0.14)
            sz = fit_size(text, size)
            wi = word_img(text, sz)
            sc = 1.35 - 0.35 * p
            wi = wi.resize((max(1, int(wi.width * sc)), max(1, int(wi.height * sc))), Image.BICUBIC)
            if p < 1:
                wi.putalpha(wi.getchannel("A").point(lambda v, p=p: int(v * min(1, p * 1.5))))
            y = int(top + line * line_h + line_h / 2 - wi.height / 2)
            L.alpha_composite(wi, (W // 2 - wi.width // 2, max(0, y)))
        layer = np.asarray(L, np.float32)
        ta = layer[..., 3:4] / 255 * 0.96
        behind = frame * (1 - ta) + layer[..., :3] * ta
        frame = behind * (1 - m) + frame * m

    # zoom-blur transition on the last 3 frames of selected shots
    if si in ZOOM_BLUR_OUT and b - t < 3 / FPS:
        k = 1 - (b - t) / (3 / FPS)
        acc = frame.copy()
        im = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
        for j in range(1, 5):
            s2 = 1 + 0.04 * j * (0.5 + k)
            c2 = im.resize((W, H), Image.BILINEAR, box=(W / 2 - W / s2 / 2, H / 2 - H / s2 / 2, W / 2 + W / s2 / 2, H / 2 + H / s2 / 2))
            acc += np.asarray(c2, np.float32)
        frame = acc / 5

    sat = 0.45 if t < DROP else 1.08
    frame = grade(frame, sat)

    # RGB split on cuts after the drop
    if t >= DROP and lt < 0.1:
        sp_px = int(12 * (1 - lt / 0.1)) + (10 if abs(t - DROP) < 0.15 else 0)
        frame[..., 0] = np.roll(frame[..., 0], -sp_px, axis=1)
        frame[..., 2] = np.roll(frame[..., 2], sp_px, axis=1)

    # front lyric (small, with stroke) over the fast cuts
    for text, at, until in FRONT_LYRICS:
        if at <= t < until:
            wi = word_img(text, 96, stroke=6)
            p = ease_out((t - at) / 0.12)
            arr = np.asarray(wi, np.float32)
            y0 = int(H * 0.70 + (1 - p) * 30)
            x0 = W // 2 - wi.width // 2
            al = arr[..., 3:4] / 255 * p
            frame[y0:y0 + wi.height, x0:x0 + wi.width] = frame[y0:y0 + wi.height, x0:x0 + wi.width] * (1 - al) + arr[..., :3] * al

    frame = frame * VIGNETTE + GRAIN[i % len(GRAIN)]
    # pre-drop: darken into the hit, then white flash on the drop
    if DROP - 0.3 <= t < DROP:
        frame *= 1 - 0.6 * (t - (DROP - 0.3)) / 0.3
    if 0 <= t - DROP < 0.3:
        a_ = 0.85 * np.exp(-(t - DROP) / 0.06)
        frame = frame * (1 - a_) + 255 * a_
    for k in range(1, 8):
        if 0 <= t - g(k) < 0.12:
            a_ = 0.28 * np.exp(-(t - g(k)) / 0.035)
            frame = frame * (1 - a_) + 255 * a_
    if t < 0.15:
        frame *= ease_out(t / 0.15)
    if t > DUR - 0.4:
        frame *= max(0.0, (DUR - t) / 0.4)
    return np.clip(frame, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ audio + encode
def build_audio() -> Path:
    pre, out = HERE / "mix_drop_prenorm.wav", HERE / "mix_drop.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{SONG_T0}", "-t", f"{DUR}", "-i", SONG,
                    "-af", f"afade=t=in:st=0:d=0.15,afade=t=out:st={DUR - 0.5}:d=0.5",
                    "-ac", "2", "-ar", "48000", str(pre)], check=True)
    f = "loudnorm=I=-14:TP=-2:LRA=11:print_format=json"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(pre), "-af", f, "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(p.stderr[p.stderr.rfind("{"): p.stderr.rfind("}") + 1])
    f2 = (f"loudnorm=I=-14:TP=-2:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
          f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(pre), "-af", f2, "-ar", "48000", str(out)], check=True)
    return out


def main() -> None:
    audio = build_audio()
    out = HERE / "final_drop.mp4"
    proc = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", str(audio), "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-maxrate", "14M", "-bufsize", "28M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ], stdin=subprocess.PIPE)
    for i in range(N):
        proc.stdin.write(render_frame(i).tobytes())
        if i % 90 == 0:
            print(f"  frame {i}/{N}", flush=True)
    proc.stdin.close()
    assert proc.wait() == 0
    print(f"done: {out}")


if __name__ == "__main__":
    main()
