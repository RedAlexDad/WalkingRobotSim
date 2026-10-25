#!/bin/bash
# batch_transcribe.sh - транскрибация всех видео в каталоге чанками (large-v3, ru).
# Пропускает видео, для которых уже есть .ru.srt рядом.
#
# Использование:
#   ./batch_transcribe.sh <dir_with_videos> [out_base_dir] [chunk_sec]
set -euo pipefail

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIR="${1:?usage: batch_transcribe.sh <dir_with_videos> [out_base_dir] [chunk_sec]}"
OUT_BASE="${2:-/tmp/opencode/whisper/batch}"
CHUNK="${3:-120}"

shopt -s nullglob
for video in "$DIR"/*.mp4; do
    base="${video%.mp4}"
    if [ -f "$base.ru.srt" ]; then
        echo "SKIP (already done): $(basename "$video")"
        continue
    fi
    echo "=== START: $(basename "$video") ==="
    out="$OUT_BASE/$(basename "$video" .mp4)"
    mkdir -p "$out/chunks"
    "$SCRIPTS_DIR/chunk_transcribe.sh" "$video" "$out/chunks" "$CHUNK" 5 ru
    python3 "$SCRIPTS_DIR/merge.py" "$out/chunks" "$out/full" "$CHUNK" 5
    rm -rf "$out/chunks"
    cp "$out/full.srt" "$base.ru.srt"
    cp "$out/full.txt" "$base.ru.txt"
    echo "=== DONE: $(basename "$video") -> $(basename "$base.ru.srt") ==="
done
echo "ALL LECTURES TRANSCRIBED"