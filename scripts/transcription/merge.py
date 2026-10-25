#!/usr/bin/env python3
# merge.py - склейка чанков из chunk_transcribe.sh в единый SRT/TXT.
#
# Использование:
#   ./merge.py <chunks_dir> [out_prefix] [chunk_sec] [overlap_sec]
import json
import glob
import sys
import os

CHUNK = 120
OVERLAP = 5

if len(sys.argv) > 1:
    chunks_dir = sys.argv[1]
else:
    chunks_dir = "/tmp/opencode/whisper/chunks"
prefix = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(chunks_dir), "full")
if len(sys.argv) > 3:
    CHUNK = int(sys.argv[3])
if len(sys.argv) > 4:
    OVERLAP = int(sys.argv[4])

DURATION = 0.0
segs = []
for fp in sorted(glob.glob(os.path.join(chunks_dir, "c_*.json"))):
    base = os.path.basename(fp).replace("c_", "").replace(".json", "")
    id_ = int(base)
    offset = (id_ - 1) * CHUNK
    with open(fp) as f:
        data = json.load(f)
    for sg in data.get("transcription", []):
        st = offset + sg["offsets"]["from"] / 1000.0
        en = offset + sg["offsets"]["to"] / 1000.0
        txt = sg.get("text", "").strip()
        if txt:
            segs.append((st, en, txt))
    # ожидаемая длительность аудио (последний чанк может выходить за конец)
    wav = fp.replace(".json", ".wav")
    try:
        import subprocess
        d = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", wav],
            capture_output=True, text=True).stdout
        DURATION = max(DURATION, offset + float(d))
    except Exception:
        pass

segs.sort(key=lambda x: x[0])

DEDUP = 2.5  # дедупликация одинаковых соседних сегментов в зоне перекрытия
clean = []
for st, en, txt in segs:
    if st >= DURATION:
        continue
    en = min(en, DURATION)
    if clean and clean[-1][2] == txt and st - clean[-1][0] < DEDUP + 1:
        continue
    clean.append((st, en, txt))


def fmt(t):
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    ms = int((t - int(t)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


with open(prefix + ".srt", "w") as f:
    for i, (st, en, txt) in enumerate(clean, 1):
        f.write(f"{i}\n{fmt(st)} --> {fmt(en)}\n{txt.strip()}\n\n")

with open(prefix + ".txt", "w") as f:
    for _, _, txt in clean:
        f.write(txt.strip() + "\n")

print(f"SRT segments: {len(clean)}")
print(f"done: {prefix}.srt, {prefix}.txt")