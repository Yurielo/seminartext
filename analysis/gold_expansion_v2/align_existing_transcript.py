#!/usr/bin/env python3
"""Run WhisperX alignment-only on an existing SeminarText SRT.

This runner never invokes WhisperX ASR and never changes transcript text.  It
stores a compact projection of two deterministic alignment runs for later
Canonical Evidence population.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import resource
import time
from pathlib import Path
from typing import Any

import whisperx


MODEL = "jonatasgrosman/wav2vec2-large-xlsr-53-russian"
MODEL_REVISION = "2329100508896c6d9b157019803ab5601e6f3406"
MODEL_SHA256 = "d1cdb1a7921de7d363f967a9b0101a713602e109dba62b6f3f9ae2e0b2df0c1c"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_time(value: str) -> float:
    hours, minutes, rest = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def parse_srt(path: Path) -> list[dict[str, Any]]:
    records = []
    raw = path.read_text(encoding="utf-8", errors="strict").strip()
    for block in re.split(r"\n\s*\n", raw):
        lines = block.splitlines()
        time_index = next(
            (index for index, line in enumerate(lines) if "-->" in line), None
        )
        if time_index is None:
            continue
        left, right = [part.strip() for part in lines[time_index].split("-->", 1)]
        text = " ".join(line.strip() for line in lines[time_index + 1 :] if line.strip())
        if text:
            records.append(
                {"start": parse_time(left), "end": parse_time(right), "text": text}
            )
    if not records:
        raise ValueError("SRT contains no timed text cues")
    return records


def compact_words(result: dict[str, Any]) -> list[dict[str, Any]]:
    words = []
    for item in result.get("word_segments", []):
        start, end = item.get("start"), item.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            continue
        if end <= start:
            continue
        words.append(
            {
                "word": item["word"],
                "start": round(float(start), 6),
                "end": round(float(end), 6),
                "score": (
                    round(float(item["score"]), 6)
                    if isinstance(item.get("score"), (int, float))
                    else None
                ),
            }
        )
    return words


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--srt", required=True, type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--source-sha256", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=2)
    args = parser.parse_args()

    if args.runs < 1:
        raise ValueError("at least one alignment run is required")
    actual_source_hash = sha256_file(args.audio)
    if actual_source_hash != args.source_sha256:
        raise ValueError(f"source SHA-256 mismatch: {actual_source_hash}")

    segments = parse_srt(args.srt)
    transcript_text = "\n".join(item["text"] for item in segments) + "\n"
    transcript_hash = hashlib.sha256(transcript_text.encode("utf-8")).hexdigest()
    config = {
        "device": "cpu",
        "language": "ru",
        "model": MODEL,
        "model_revision": MODEL_REVISION,
        "return_char_alignments": True,
        "role": "alignment_only_no_asr",
    }

    started = time.perf_counter()
    audio = whisperx.load_audio(str(args.audio))
    model_started = time.perf_counter()
    model, metadata = whisperx.load_align_model(language_code="ru", device="cpu")
    model_seconds = time.perf_counter() - model_started

    run_hashes = []
    run_seconds = []
    words = None
    for _ in range(args.runs):
        run_started = time.perf_counter()
        result = whisperx.align(
            segments,
            model,
            metadata,
            audio,
            "cpu",
            return_char_alignments=True,
        )
        run_seconds.append(round(time.perf_counter() - run_started, 6))
        run_hashes.append(canonical_hash(result))
        projected = compact_words(result)
        if words is None:
            words = projected
        elif canonical_hash(projected) != canonical_hash(words):
            raise ValueError("compact alignment projection changed between runs")

    payload = {
        "artifact_type": "gold_expansion_v2_whisperx_alignment_evidence",
        "schema_version": 1,
        "invocation_role": "alignment_only_no_asr",
        "source": {
            "source_id": args.source_id,
            "content_sha256": actual_source_hash,
        },
        "transcript": {
            "srt_sha256": sha256_file(args.srt),
            "text_sha256": transcript_hash,
            "segment_count": len(segments),
        },
        "alignment": {
            "aligner": "whisperx",
            "aligner_version": importlib.metadata.version("whisperx"),
            "model": MODEL,
            "model_revision": MODEL_REVISION,
            "model_sha256": MODEL_SHA256,
            "config": config,
            "config_sha256": canonical_hash(config),
            "run_result_sha256": run_hashes,
            "run_seconds": run_seconds,
            "model_load_seconds": round(model_seconds, 6),
            "total_seconds": round(time.perf_counter() - started, 6),
            "max_resident_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        },
        "words": words or [],
    }
    if len(run_hashes) > 1 and len(set(run_hashes)) != 1:
        raise ValueError("WhisperX result changed between deterministic runs")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
