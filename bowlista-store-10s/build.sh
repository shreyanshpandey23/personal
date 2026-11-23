#!/bin/sh
# One command: voice check, picture, sound, mix, master.
set -e
LIB=${LIB:-/root/lemo-opuscar}
export LIB
HERE=$(cd "$(dirname "$0")" && pwd)
[ -f "$LIB/core/render/video.mjs" ] || { echo "set LIB to the Lemo-Opuscar library folder"; exit 1; }
cd "$LIB"
[ -f "$HERE/voices/l1.wav" ] || "$LIB/.venv/bin/python" core/tts/tts.py "$HERE/lines.json" "$HERE/voices"
"$LIB/.venv/bin/python" core/tts/asr_check.py "$HERE/lines.json" "$HERE/voices" --lang en
node core/render/events.mjs "$HERE" --size 1080x1920
node core/render/video.mjs "$HERE" --size 1080x1920 --fps 30 --workers 3 --out "$HERE/out/video.mp4"
"$LIB/.venv/bin/python" "$HERE/mix.py"
"$LIB/.venv/bin/python" "$HERE/subs.py"
sh core/render/mux.sh "$HERE/out/video.mp4" "$HERE/out/mix.wav" "$HERE/bowlista-10s.mp4" 30 0 || sh "$HERE/master.sh"   # ffmpeg 6 fallback
