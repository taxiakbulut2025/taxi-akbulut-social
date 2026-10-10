#!/usr/bin/env bash
# Baut ein Reel: animiertes Motiv + eigene Musik -> MP4 (1080x1920, H.264/AAC)
# Aufruf: bash generator/make_reel.sh motive/<slug>-reel.html reels/<datum>-<slug>.mp4 [music.py-Optionen]
set -euo pipefail
SRC=$1; OUT=$2; shift 2
TMP=$(mktemp -d)
node generator/reel.js "$SRC" "$TMP/frames" 9 30
python3 generator/music.py "$TMP/music.wav" "$@"
mkdir -p "$(dirname "$OUT")"
ffmpeg -y -loglevel error -framerate 30 -i "$TMP/frames/f%04d.jpg" -i "$TMP/music.wav" \
  -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 -r 30 -c:a aac -b:a 192k -ar 44100 \
  -shortest -movflags +faststart "$OUT"
cp "$TMP/frames/f0240.jpg" "${OUT%.mp4}-vorschau.jpg"
rm -rf "$TMP"
echo "ok $OUT"
