#!/bin/bash
# chunk_transcribe.sh - транскрибация длинного аудио независимыми чанками.
# Используется для подавления галлюцинаций whisper (зацикливание) на длинных файлах.
#
# Использование:
#   ./chunk_transcribe.sh <video_or_audio> [out_dir] [chunk_sec] [overlap_sec] [lang] [model]
set -euo pipefail

CLI="${WHISPER_CLI:-/home/redalexdad/GitHub/whisper.cpp/build_cuda/bin/whisper-cli}"
MODEL="${WHISPER_MODEL:-/home/redalexdad/GitHub/whisper.cpp/models/ggml-large-v3.bin}"

SRC="${1:?usage: chunk_transcribe.sh <media> [out_dir] [chunk_sec] [overlap_sec] [lang] [model]}"
OUT="${2:-/tmp/opencode/whisper/chunks}"
CHUNK="${3:-120}"
OVERLAP="${4:-5}"
LANG="${5:-ru}"
if [ "$#" -ge 6 ]; then MODEL="$6"; fi

WORK="${OUT}/audio_work"
mkdir -p "$WORK"
WAV="$WORK/input.wav"

ffmpeg -v error -i "$SRC" -ac 1 -ar 16000 "$WAV" -y

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$WAV" | cut -d. -f1)
mkdir -p "$OUT"
rm -f "$OUT"/c_*.json

start=0
id=0
while [ "$start" -lt "$DUR" ]; do
    id=$((id + 1))
    e=$((start + CHUNK + OVERLAP))
    printf "%s %s -> %s (chunk %s)\n" "$id" "$start" "$e" "$start"
    ffmpeg -v error -ss "$start" -to "$e" -i "$WAV" -ac 1 -ar 16000 "$OUT/c_${id}.wav" -y
    "$CLI" -m "$MODEL" -l "$LANG" -f "$OUT/c_${id}.wav" -oj -of "$OUT/c_${id}" -nt >/dev/null 2>&1
    start=$((start + CHUNK))
done
echo "done ${id} chunks"