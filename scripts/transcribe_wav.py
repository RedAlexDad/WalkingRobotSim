#!/usr/bin/env python3
"""Chunked transcription of a long WAV with whisper.cpp (CPU-safe).

Splits the audio into fixed-length chunks, transcribes each chunk with a
per-chunk timeout (so a single chunk cannot hang the whole job), and merges
the results into one .txt and one .srt.

Usage:
    python3 scripts/transcribe_wav.py IN.wav --out-dir DIR \
        [--chunk-seconds 120] [--threads 16] [--model PATH]
"""

from __future__ import annotations

import argparse
import pathlib
import re
import shlex
import subprocess
import sys

WHISPER = pathlib.Path.home() / "GitHub/whisper.cpp/build/bin/whisper-cli"
MODEL = pathlib.Path.home() / "GitHub/whisper.cpp/models/ggml-large-v3.bin"
TS = re.compile(
    r"(\d\d):(\d\d):(\d\d)[,.](\d\d\d)\s*-->\s*(\d\d):(\d\d):(\d\d)[,.](\d\d\d)"
)


def run(cmd: list[str], timeout: float, log) -> int:
    log(f"$ {' '.join(str(c) for c in cmd)}")
    try:
        p = subprocess.run(cmd, timeout=timeout, stdout=subprocess.DEVNULL,
                           stderr=subprocess.PIPE)
        return p.returncode
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT after {timeout:.0f}s: {cmd[0]}")
        return 124


def split(wav: pathlib.Path, out: pathlib.Path, chunk: int) -> list[pathlib.Path]:
    for old in out.glob("chunk_*.wav"):
        old.unlink()
    rc = run([
        "ffmpeg", "-y", "-v", "error", "-i", str(wav),
        "-f", "segment", "-segment_time", str(chunk), "-reset_timestamps", "1",
        "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le",
        str(out / "chunk_%03d.wav"),
    ], timeout=600, log=print)
    if rc != 0:
        sys.exit(f"ffmpeg split failed rc={rc}")
    return sorted(out.glob("chunk_*.wav"))


def shift_srt(text: str, offset: float, counter: list[int]) -> str:
    def repl(m: re.Match) -> str:
        g = [int(x) for x in m.groups()]

        def t(s: int, ms: int) -> float:
            return s + ms / 1000.0

        a = t(g[0] * 3600 + g[1] * 60 + g[2], g[3]) + offset
        b = t(g[4] * 3600 + g[5] * 60 + g[6], g[7]) + offset

        def fmt(v: float) -> str:
            h = int(v // 3600)
            m = int((v % 3600) // 60)
            s = int(v % 60)
            ms = int(round((v - int(v)) * 1000))
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        return f"{fmt(a)} --> {fmt(b)}"

    body = TS.sub(repl, text)
    out = []
    for block in body.strip().split("\n\n"):
        lines = block.strip().splitlines()
        if not lines:
            continue
        counter[0] += 1
        out.append(str(counter[0]))
        out.extend(lines[1:])
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", type=pathlib.Path)
    ap.add_argument("--out-dir", type=pathlib.Path, required=True)
    ap.add_argument("--chunk-seconds", type=int, default=120)
    ap.add_argument("--threads", type=int, default=16)
    ap.add_argument("--model", type=pathlib.Path, default=MODEL)
    ap.add_argument("--chunk-timeout", type=float, default=600.0)
    ap.add_argument("--whisper-bin", type=pathlib.Path, default=WHISPER)
    ap.add_argument("--lang", default="ru")
    ap.add_argument("--beam", type=int, default=0)
    ap.add_argument("--prompt", default=None)
    ap.add_argument("--extra", default="",
                    help="доп. аргументы whisper-cli (строка)")
    a = ap.parse_args()

    a.out_dir.mkdir(parents=True, exist_ok=True)

    def log(msg: str) -> None:
        print(msg, flush=True)

    chunks = split(a.wav, a.out_dir, a.chunk_seconds)
    log(f"chunks: {len(chunks)} (по {a.chunk_seconds}s)")

    txt_parts: list[str] = []
    srt_parts: list[str] = []
    counter = [0]
    for i, ch in enumerate(chunks):
        offset = i * a.chunk_seconds
        base = a.out_dir / f"out_{i:03d}"
        log(f"[{i + 1}/{len(chunks)}] offset={offset}s -> {ch.name}")
        cmd = [str(a.whisper_bin), "-m", str(a.model), "-l", a.lang,
               "-f", str(ch), "-otxt", "-osrt", "-of", str(base)]
        if a.threads:
            cmd += ["-t", str(a.threads)]
        if a.beam:
            cmd += ["-bs", str(a.beam)]
        if a.prompt:
            cmd += ["--prompt", a.prompt]
        if a.extra:
            cmd += shlex.split(a.extra)
        rc = run(cmd, timeout=a.chunk_timeout, log=log)
        if rc != 0:
            log(f"  chunk {i} rc={rc} (пропуск)")
            continue
        t = pathlib.Path(str(base) + ".txt")
        s = pathlib.Path(str(base) + ".srt")
        if t.exists():
            txt_parts.append(f"=== чанк {i + 1} (с {offset // 60}:{offset % 60:02d}) ===")
            txt_parts.append(t.read_text(encoding="utf-8").strip())
        if s.exists():
            srt_parts.append(shift_srt(s.read_text(encoding="utf-8"), offset,
                                       counter))
        log(f"  ok ({t.stat().st_size if t.exists() else 0} b)")

    (a.out_dir / "full.txt").write_text("\n\n".join(txt_parts),
                                        encoding="utf-8")
    (a.out_dir / "full.srt").write_text("\n".join(srt_parts),
                                        encoding="utf-8")
    log(f"DONE: {a.out_dir / 'full.txt'} , {a.out_dir / 'full.srt'}")


if __name__ == "__main__":
    main()
