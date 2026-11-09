#!/usr/bin/env bash
# Rebuild the "Monstrous" edit from the source clip.
#   ./build.sh <source.mp4> [workdir]
# Needs: ffmpeg, python3 with numpy, scipy, opencv-python-headless, pillow.
set -euo pipefail
SRC="$1"
WORK="${2:-$(mktemp -d)}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

python3 prep.py "$SRC" "$WORK"          # decode frames + optical flow
python3 make_audio.py "$WORK"           # BGM + sound design -> mix.wav
JOBS="${JOBS:-4}" python3 render.py "$WORK" video   # picture -> video.mp4

ffmpeg -v error -y -i "$WORK/video.mp4" -i "$WORK/mix.wav" \
  -map 0:v -map 1:a -c:v copy -c:a aac -b:a 320k -ar 48000 \
  -shortest -movflags +faststart "$HERE/monstrous_edit.mp4"
echo "done -> $HERE/monstrous_edit.mp4"
