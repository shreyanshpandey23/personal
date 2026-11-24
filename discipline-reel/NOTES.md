# Discipline reel: how it's built

- **Song:** the uploaded track, segment 0:31.37–0:45.87 (14.5 s), chosen so the drop (0:36.6) lands on beat 9, at 5.22 s into the video. Tempo is about 103 BPM: one beat every 0.58 s, and beat 0 is the first frame.
- **Picture:** `index.html` draws every frame on a canvas as a function of time. Push-up reps, the drop flash, the punch-zooms and the text all key off the same 0.58 s grid.
- **Render:** with the Lemo-Opuscar library at `$LIB`:
  - `node $LIB/core/render/video.mjs . --size 1080x1920 --fps 30 --out out/video.mp4`
  - `ffmpeg -ss 31.366 -t 14.5 -i <song> -af "afade=t=in:d=0.08,afade=t=out:st=13.9:d=0.6" -ar 48000 -ac 2 out/mix.wav`
  - `sh master.sh` (two-pass loudness normalisation to −14 LUFS, then mux)
- **Sync check:** 19 of 27 detected kicks in the final file sit within 40 ms of the beat grid (median 13 ms). The rest are the song's off-beat hits.
