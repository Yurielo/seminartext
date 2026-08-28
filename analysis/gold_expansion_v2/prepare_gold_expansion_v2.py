#!/usr/bin/env python3
"""Build prediction-independent Gold Expansion v2 evidence and packets."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from schemas.validate_canonical_evidence_v1 import validate_bundle  # noqa: E402


WINDOW_SECONDS = 720
MIN_WINDOW_SECONDS = 600
WINDOW_COUNT = 6


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def parse_time(value: str) -> float:
    hours, minutes, rest = value.replace(",", ".").split(":")
    return int(hours) * 3600 + int(minutes) * 60 + float(rest)


def format_time(value: float) -> str:
    milliseconds = round(value * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


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
        if not text:
            continue
        start, end = parse_time(left), parse_time(right)
        if end <= start:
            raise ValueError(f"invalid SRT cue interval: {left} --> {right}")
        records.append(
            {
                "id": len(records) + 1,
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
            }
        )
    if not records:
        raise ValueError("SRT contains no timed text cues")
    return records


def media_duration(path: Path) -> float:
    output = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        text=True,
    )
    return float(output.strip())


def source_quality(cues: list[dict[str, Any]], duration: float) -> dict[str, Any]:
    durations = [item["end"] - item["start"] for item in cues]
    word_counts = [len(re.findall(r"\w+(?:[-']\w+)*", item["text"])) for item in cues]
    normalized = [re.sub(r"\W+", " ", item["text"].lower()).strip() for item in cues]
    overlaps = [
        round(cues[index - 1]["end"] - cues[index]["start"], 3)
        for index in range(1, len(cues))
        if cues[index]["start"] < cues[index - 1]["end"]
    ]
    gaps = [
        round(cues[index]["start"] - cues[index - 1]["end"], 3)
        for index in range(1, len(cues))
        if cues[index]["start"] > cues[index - 1]["end"]
    ]
    return {
        "cue_count": len(cues),
        "cue_duration_seconds": {
            "median": round(statistics.median(durations), 3),
            "p90": round(percentile(durations, 0.90), 3),
            "p95": round(percentile(durations, 0.95), 3),
            "max": round(max(durations), 3),
        },
        "cue_words": {
            "median": round(statistics.median(word_counts), 3),
            "p90": round(percentile([float(x) for x in word_counts], 0.90), 3),
            "max": max(word_counts),
        },
        "unique_normalized_cues": len(set(normalized)),
        "unique_normalized_cue_ratio": round(len(set(normalized)) / len(cues), 6),
        "overlap_count": len(overlaps),
        "max_overlap_seconds": round(max(overlaps, default=0), 3),
        "gap_count": len(gaps),
        "gaps_over_30_seconds": sum(value > 30 for value in gaps),
        "max_gap_seconds": round(max(gaps, default=0), 3),
        "transcript_end_seconds": cues[-1]["end"],
        "source_duration_seconds": round(duration, 3),
        "end_coverage_ratio": round(cues[-1]["end"] / duration, 6),
    }


def cue_records(
    cues: list[dict[str, Any]], transcript_id: str
) -> tuple[str, list[dict[str, Any]], list[tuple[int, int, str]]]:
    canonical_text = "\n".join(item["text"] for item in cues) + "\n"
    records = []
    spans = []
    cursor = 0
    for sequence, cue in enumerate(cues):
        start, end = cursor, cursor + len(cue["text"])
        cue_id = f"{transcript_id}:cue:{sequence:06d}"
        records.append(
            {
                "char_end": end,
                "char_start": start,
                "id": cue_id,
                "lifecycle_status": "draft",
                "sequence": sequence,
                "source_locator": {
                    "end_seconds": cue["end"],
                    "start_seconds": cue["start"],
                    "type": "time_interval",
                },
                "text": cue["text"],
                "transcript_revision_id": transcript_id,
            }
        )
        spans.append((start, end, cue_id))
        cursor = end + 1
    return canonical_text, records, spans


def map_alignment(
    tokens: list[re.Match[str]], aligned_words: list[dict[str, Any]]
) -> list[dict[str, Any] | None]:
    mapped = []
    aligned_index = 0
    for token in tokens:
        if (
            aligned_index < len(aligned_words)
            and aligned_words[aligned_index].get("word") == token.group(0)
        ):
            mapped.append(aligned_words[aligned_index])
            aligned_index += 1
        else:
            mapped.append(None)
    if aligned_index != len(aligned_words):
        word = aligned_words[aligned_index].get("word")
        raise ValueError(f"alignment contains unmatched semantic token: {word!r}")
    return mapped


def source_cue_for_word(
    start: int, end: int, spans: list[tuple[int, int, str]], hint: int
) -> tuple[str, int]:
    while hint < len(spans) and start >= spans[hint][1]:
        hint += 1
    if hint >= len(spans) or start < spans[hint][0] or end > spans[hint][1]:
        raise ValueError(f"word span [{start}, {end}) has no single source cue")
    return spans[hint][2], hint


def build_words(
    canonical_text: str,
    transcript_id: str,
    source_id: str,
    cue_spans: list[tuple[int, int, str]],
    alignment_run_id: str,
    aligned_words: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    tokens = list(re.finditer(r"\S+", canonical_text))
    mapped = map_alignment(tokens, aligned_words)
    records = []
    cue_hint = 0
    for sequence, (token, aligned) in enumerate(zip(tokens, mapped)):
        cue_id, cue_hint = source_cue_for_word(
            token.start(), token.end(), cue_spans, cue_hint
        )
        if aligned is None:
            status, start, end, confidence = "unaligned", None, None, None
            provenance = {"alignment_run_id": None, "kind": "unavailable", "method": None}
            flags = ["unaligned_review_required"]
        else:
            status = "aligned"
            start, end, confidence = aligned["start"], aligned["end"], aligned.get("score")
            provenance = {
                "alignment_run_id": alignment_run_id,
                "kind": "forced_alignment",
                "method": None,
            }
            flags = []
            if confidence is not None and confidence < 0.1:
                flags.append("low_alignment_confidence")
            if end - start > 5:
                flags.append("unusually_long_interval")
        records.append(
            {
                "alignment_status": status,
                "char_end": token.end(),
                "char_start": token.start(),
                "confidence": confidence,
                "end_seconds": end,
                "id": f"{transcript_id}:word:{sequence:06d}",
                "lifecycle_status": "draft",
                "normalized_text": None,
                "qa_flags": flags,
                "sequence": sequence,
                "source_cue_ids": [cue_id],
                "source_id": source_id,
                "speaker_id": None,
                "start_seconds": start,
                "text": token.group(0),
                "timing_provenance": provenance,
                "transcript_revision_id": transcript_id,
            }
        )
    return records


def build_segments(
    cue_records_: list[dict[str, Any]], words: list[dict[str, Any]], transcript_id: str, slug: str
) -> list[dict[str, Any]]:
    words_by_cue: dict[str, list[dict[str, Any]]] = {}
    for word in words:
        words_by_cue.setdefault(word["source_cue_ids"][0], []).append(word)
    records = []
    for cue in cue_records_:
        group = words_by_cue.get(cue["id"], [])
        if not group:
            raise ValueError(f"cue has no canonical words: {cue['id']}")
        records.append(
            {
                "id": f"segment_{slug}_video_001_r1_{cue['sequence']:06d}",
                "lifecycle_status": "draft",
                "sequence": cue["sequence"],
                "transcript_revision_id": transcript_id,
                "word_count": len(group),
                "word_end_id": group[-1]["id"],
                "word_start_id": group[0]["id"],
            }
        )
    return records


def build_bundle(candidate: dict[str, Any], cues: list[dict[str, Any]], alignment: dict[str, Any]) -> dict[str, Any]:
    slug = candidate["slug"]
    project_id = f"project_{slug}"
    source_id = f"source_{slug}_video_001"
    transcript_id = f"transcript_{slug}_video_001_r1"
    run_id = f"alignment_{slug}_video_001_r1_whisperx_3.8.6"
    canonical_text, canonical_cues, cue_spans = cue_records(cues, transcript_id)
    text_sha = hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()
    if text_sha != alignment["transcript"]["text_sha256"]:
        raise ValueError(f"{slug}: alignment transcript hash mismatch")
    run_hashes = alignment["alignment"]["run_result_sha256"]
    if not run_hashes or len(set(run_hashes)) != 1:
        raise ValueError(f"{slug}: alignment is not deterministic")
    words = build_words(
        canonical_text,
        transcript_id,
        source_id,
        cue_spans,
        run_id,
        alignment["words"],
    )
    segments = build_segments(canonical_cues, words, transcript_id, slug)
    navigation = []
    aligned = [word for word in words if word["alignment_status"] == "aligned"]
    for sequence, offset in enumerate([0, len(aligned) // 4, len(aligned) // 2, 3 * len(aligned) // 4, len(aligned) - 1]):
        word = aligned[offset]
        navigation.append(
            {
                "id": f"evidence_{slug}_video_001_word_{word['sequence']:06d}",
                "lifecycle_status": "draft",
                "locator": {
                    "end_seconds": word["end_seconds"],
                    "start_seconds": word["start_seconds"],
                    "type": "time_interval",
                },
                "project_id": project_id,
                "source_id": source_id,
                "target": {"entity_id": word["id"], "entity_type": "word"},
                "transcript_revision_id": transcript_id,
            }
        )
    bundle = {
        "alignment_runs": [
            {
                "aligner": alignment["alignment"]["aligner"],
                "aligner_version": alignment["alignment"]["aligner_version"],
                "config_sha256": alignment["alignment"]["config_sha256"],
                "id": run_id,
                "model": alignment["alignment"]["model"],
                "model_revision": alignment["alignment"]["model_revision"],
                "model_sha256": alignment["alignment"]["model_sha256"],
                "source_content_sha256": candidate["source_sha256"],
                "source_id": source_id,
                "status": "valid",
                "transcript_revision_id": transcript_id,
                "transcript_text_sha256": text_sha,
            }
        ],
        "artifact_id": f"canonical_{slug}_video_001_asr_r1",
        "artifact_type": "seminartext.canonical_evidence",
        "benchmark_segments": segments,
        "cues": canonical_cues,
        "evidence_refs": sorted(navigation, key=lambda item: item["id"]),
        "project": {"id": project_id, "lifecycle_status": "active", "title": candidate["project_title"]},
        "schema_version": "1.0.0",
        "sources": [
            {
                "content_sha256": candidate["source_sha256"],
                "duration_seconds": candidate["duration_seconds"],
                "id": source_id,
                "kind": "video",
                "lifecycle_status": "active",
                "project_id": project_id,
                "sequence": 0,
                "title": candidate["source_title"],
            }
        ],
        "topics": [],
        "transcript_revisions": [
            {
                "authority": "candidate",
                "canonical_text": canonical_text,
                "id": transcript_id,
                "lifecycle_status": "draft",
                "parent_revision_id": None,
                "revision_kind": "asr",
                "revision_number": 1,
                "source_id": source_id,
                "text_sha256": text_sha,
            }
        ],
        "words": words,
    }
    errors = validate_bundle(bundle)
    if errors:
        raise ValueError("canonical validation failed:\n" + "\n".join(errors))
    return bundle


def make_windows(cues: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    windows, current = [], []
    start = cues[0]["start"]
    for cue in cues:
        if current and cue["start"] >= start + WINDOW_SECONDS:
            windows.append(current)
            current = []
            start = cue["start"]
        current.append(cue)
    if current:
        windows.append(current)
    return windows


def evenly_spaced(total: int, wanted: int) -> list[int]:
    if total < wanted:
        raise ValueError(f"need {wanted} eligible windows, found {total}")
    selected = sorted({round(index * (total - 1) / (wanted - 1)) for index in range(wanted)})
    cursor = 0
    while len(selected) < wanted:
        if cursor not in selected:
            selected.append(cursor)
        cursor += 1
    return sorted(selected)


def build_packets(candidate: dict[str, Any], cues: list[dict[str, Any]], bundle: dict[str, Any]) -> dict[str, Any]:
    windows = make_windows(cues)
    eligible = [
        index
        for index, window in enumerate(windows)
        if window[-1]["end"] - window[0]["start"] >= MIN_WINDOW_SECONDS
    ]
    selected = [eligible[offset] for offset in evenly_spaced(len(eligible), WINDOW_COUNT)]
    words = bundle["words"]
    words_by_cue = {cue["id"]: [] for cue in bundle["cues"]}
    for word in words:
        words_by_cue[word["source_cue_ids"][0]].append(word)
    packets = []
    for selection_order, window_index in enumerate(selected, 1):
        window = windows[window_index]
        first_cue = bundle["cues"][window[0]["id"] - 1]
        last_cue = bundle["cues"][window[-1]["id"] - 1]
        first_word = words_by_cue[first_cue["id"]][0]
        last_word = words_by_cue[last_cue["id"]][-1]
        packets.append(
            {
                "annotation": {
                    "boundaries": [],
                    "notes": "",
                    "summaries": [],
                    "titles": [],
                },
                "annotation_status": "GOLD_ANNOTATION_REQUIRED",
                "candidate_id": candidate["candidate_id"],
                "cue_range": [window[0]["id"], window[-1]["id"]],
                "packet_id": f"{candidate['candidate_id'].lower()}_video_001_window_{window_index + 1:02d}",
                "selection_order": selection_order,
                "source_id": "video_001",
                "timestamp_range": [format_time(window[0]["start"]), format_time(window[-1]["end"])],
                "transcript": [
                    {
                        "cue_id": cue["id"],
                        "end": format_time(cue["end"]),
                        "start": format_time(cue["start"]),
                        "text": cue["text"],
                    }
                    for cue in window
                ],
                "word_id_range": [first_word["id"], last_word["id"]],
            }
        )
    return {
        "artifact_type": "gold_expansion_v2_annotation_packets",
        "candidate_id": candidate["candidate_id"],
        "contamination_policy": "prediction_independent_no_topic_engine_outputs_read",
        "packet_count": len(packets),
        "packets": packets,
        "schema_version": 1,
        "selection_policy": {
            "available_window_count": len(windows),
            "candidate_count": WINDOW_COUNT,
            "eligible_window_count": len(eligible),
            "min_candidate_seconds": MIN_WINDOW_SECONDS,
            "name": "evenly_spaced_transcript_windows",
            "rule": "Split completed ASR cues into sequential 12-minute windows, retain windows at least 10 minutes long, then select six evenly spaced positions. No predictions or semantic difficulty judgments are read.",
            "selected_window_numbers": [index + 1 for index in selected],
            "window_seconds": WINDOW_SECONDS,
        },
    }


def build_candidate(candidate: dict[str, Any], output_root: Path) -> dict[str, Any]:
    source = Path(candidate["source_path"])
    project = Path(candidate["project_path"])
    srt = project / "transcript" / "video_001" / "transcript.srt"
    completion = project / "transcript" / "video_001" / ".seminartext_complete"
    alignment_path = Path(candidate["alignment_path"])
    if not alignment_path.is_absolute():
        alignment_path = ROOT / alignment_path
    for path in (source, srt, completion, alignment_path):
        if not path.exists():
            raise FileNotFoundError(path)
    if sha256_file(source) != candidate["source_sha256"]:
        raise ValueError(f"{candidate['candidate_id']}: source SHA-256 mismatch")
    duration = media_duration(source)
    if abs(duration - candidate["duration_seconds"]) > 0.1:
        raise ValueError(f"{candidate['candidate_id']}: source duration changed")
    cues = parse_srt(srt)
    alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
    if alignment.get("invocation_role") != "alignment_only_no_asr":
        raise ValueError("alignment evidence used an invalid role")
    if alignment["source"]["content_sha256"] != candidate["source_sha256"]:
        raise ValueError("alignment evidence references another source")
    if alignment["transcript"]["srt_sha256"] != sha256_file(srt):
        raise ValueError("alignment evidence references another SRT")

    bundle = build_bundle(candidate, cues, alignment)
    packets = build_packets(candidate, cues, bundle)
    quality = source_quality(cues, duration)
    candidate_dir = output_root / candidate["slug"]
    candidate_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "canonical_evidence": candidate_dir / "canonical_evidence_bundle.json",
        "annotation_packets": candidate_dir / "gold_annotation_packets.json",
        "source_quality": candidate_dir / "source_quality.json",
    }
    artifacts["canonical_evidence"].write_bytes(canonical_bytes(bundle))
    artifacts["annotation_packets"].write_bytes(canonical_bytes(packets))
    artifacts["source_quality"].write_bytes(canonical_bytes(quality))
    repeated = canonical_bytes(build_bundle(candidate, cues, alignment))
    if repeated != artifacts["canonical_evidence"].read_bytes():
        raise ValueError(f"{candidate['candidate_id']}: population is not byte-identical")
    return {
        "aligned_words": sum(word["alignment_status"] == "aligned" for word in bundle["words"]),
        "annotation_packets": str(artifacts["annotation_packets"].relative_to(ROOT)),
        "candidate_id": candidate["candidate_id"],
        "canonical_bundle": str(artifacts["canonical_evidence"].relative_to(ROOT)),
        "canonical_sha256": sha256_file(artifacts["canonical_evidence"]),
        "cue_count": len(cues),
        "deterministic_population": True,
        "source_quality": quality,
        "transcript_lifecycle": "ASR / provisional / human review required",
        "unaligned_words": sum(word["alignment_status"] == "unaligned" for word in bundle["words"]),
        "word_count": len(bundle["words"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()
    config_path = args.config if args.config.is_absolute() else ROOT / args.config
    output_root = (
        args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    )
    summary_path = args.summary if args.summary.is_absolute() else ROOT / args.summary
    config = json.loads(config_path.read_text(encoding="utf-8"))
    results = [build_candidate(candidate, output_root) for candidate in config["candidates"]]
    summary = {
        "artifact_type": "gold_expansion_v2_preparation_summary",
        "candidates": results,
        "guardrails": {
            "dataset_c_d_e_unchanged": True,
            "final_gold_boundaries_created": False,
            "gold_a_b_c_unchanged": True,
            "topic_engine_candidates_run": False,
        },
        "schema_version": 1,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_bytes(canonical_bytes(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
