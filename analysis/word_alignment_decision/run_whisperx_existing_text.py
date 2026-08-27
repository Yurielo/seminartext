#!/usr/bin/env python3
"""Run WhisperX alignment against a frozen existing transcript.

This is an experiment-only runner. It never invokes WhisperX ASR and therefore
does not replace the supplied semantic text with a fresh transcription.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import resource
import sys
import time
from pathlib import Path

import whisperx


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_result_hash(result: dict) -> str:
    payload = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--segments", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=2)
    args = parser.parse_args()

    frozen = json.loads(args.segments.read_text(encoding="utf-8"))
    segments = [
        {"start": row["start"], "end": row["end"], "text": row["text"]}
        for row in frozen["segments"]
    ]

    device = "cpu"
    started = time.perf_counter()
    audio = whisperx.load_audio(str(args.audio))
    model_started = time.perf_counter()
    model, metadata = whisperx.load_align_model(language_code="ru", device=device)
    model_seconds = time.perf_counter() - model_started

    runs = []
    for run_number in range(1, args.runs + 1):
        run_started = time.perf_counter()
        result = whisperx.align(
            segments,
            model,
            metadata,
            audio,
            device,
            return_char_alignments=True,
        )
        elapsed = time.perf_counter() - run_started
        runs.append(
            {
                "run": run_number,
                "seconds": elapsed,
                "canonical_result_sha256": canonical_result_hash(result),
                "result": result,
            }
        )

    payload = {
        "artifact_type": "issue_38_whisperx_existing_transcript_alignment",
        "schema_version": 1,
        "invocation_role": "alignment_only_no_asr",
        "language": "ru",
        "device": device,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "whisperx": importlib.metadata.version("whisperx"),
            "torch": importlib.metadata.version("torch"),
            "torchaudio": importlib.metadata.version("torchaudio"),
            "transformers": importlib.metadata.version("transformers"),
        },
        "input": {
            "audio_path": str(args.audio),
            "audio_sha256": sha256(args.audio),
            "segments_path": str(args.segments),
            "segments_sha256": sha256(args.segments),
            "segment_count": len(segments),
        },
        "model_load_seconds": model_seconds,
        "total_seconds": time.perf_counter() - started,
        "max_resident_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
