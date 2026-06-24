#!/usr/bin/env python3
"""Transcribe an audio file locally with faster-whisper (no API key needed).

Usage:
  uv run --with faster-whisper transcribe.py /path/to/voice.m4a
  WHISPER_MODEL=small uv run --with faster-whisper transcribe.py clip.wav

Prints the transcript text to stdout. Model defaults to base.en (good
accuracy/speed for short English voice memos); override with WHISPER_MODEL
(tiny.en / base.en / small.en / medium.en, or multilingual variants).
Decodes m4a/mp3/wav/ogg via bundled PyAV — no system ffmpeg required.
"""
import os, sys
from faster_whisper import WhisperModel

def main():
    if len(sys.argv) < 2:
        print("usage: transcribe.py <audiofile>", file=sys.stderr)
        raise SystemExit(2)
    path = sys.argv[1]
    if not os.path.exists(path):
        print(f"file not found: {path}", file=sys.stderr)
        raise SystemExit(1)
    model_name = os.environ.get("WHISPER_MODEL", "base.en")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(path, vad_filter=True)
    text = "".join(s.text for s in segments).strip()
    print(text)

if __name__ == "__main__":
    main()
