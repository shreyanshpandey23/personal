# Keep Digging reel: how it's built

- **Song:** the same uploaded track, segment 0:32.53–0:42.97 (10.44 s = 18 beats at 0.58 s). The drop lands on beat 7, at 4.06 s into the video.
- **Beat map:**
  - Strikes on beats 0–5.
  - Big wind-up held through the song's quiet gap (beat 6).
  - Breakthrough strike and white flash on the drop.
  - Walk to the diamond on beat 8; lift it overhead on beat 9.
  - Camera steps back on beats 10, 11 and 12; "KEEP DIGGING." lands on beat 12.
- **Render:** with the Lemo-Opuscar library at `$LIB`:
  - `node $LIB/core/render/video.mjs . --size 1080x1920 --fps 30 --out out/video.mp4`
  - `ffmpeg -ss 32.526 -t 10.44 -i <song> -af "afade=t=in:d=0.06,afade=t=out:st=9.9:d=0.54" -ar 48000 -ac 2 out/mix.wav`
  - `sh master.sh` (normalise to −14 LUFS, then mux)
- **Sync check:** the drop kick is detected at 4.08 s (strike at 4.06 s). 13 of 18 kicks are within 40 ms of the beat grid; the rest are off-beat hits.
- **The quitter (added):** an upper tunnel on a rock ledge. He strikes in sync on beats 0–3, slumps and drops the pick on beat 4, and walks out along the ledge (gone by about 5 s). His tunnel stops about 140 px short of his own diamond; both diamonds are labelled "SUCCESS:".
