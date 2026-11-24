#!/bin/sh
# Fallback master for ffmpeg 6: two-pass loudnorm (-14 LUFS, TP -1.5) on the WAV, then mux with the picture.
set -e
HERE=$(cd "$(dirname "$0")" && pwd); cd "$HERE/out"
J=$(ffmpeg -hide_banner -nostats -i mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
v() { echo "$J" | grep "\"$1\"" | sed 's/.*: "\(.*\)".*/\1/'; }
ffmpeg -y -hide_banner -loglevel error -i mix.wav -af "loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=$(v input_i):measured_TP=$(v input_tp):measured_LRA=$(v input_lra):measured_thresh=$(v input_thresh):offset=$(v target_offset):linear=true,aresample=48000" -ar 48000 mix_norm.wav
ffmpeg -y -hide_banner -loglevel error -i video.mp4 -i mix_norm.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$HERE/keep-digging-reel.mp4"
ffmpeg -hide_banner -nostats -i "$HERE/keep-digging-reel.mp4" -af ebur128=peak=true -f null - 2>&1 | grep -A8 Summary | grep -E "I:|Peak:"
