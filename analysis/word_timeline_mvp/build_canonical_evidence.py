#!/usr/bin/env python3
"""Populate Canonical Evidence v1 from the frozen Issue #38 alignment evidence.

This runner is deliberately narrow: it consumes one immutable verified
transcript, its cue provenance, and alignment-only output. It never invokes ASR
or WhisperX and never edits semantic text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from schemas.validate_canonical_evidence_v1 import validate_bundle  # noqa: E402


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_bytes(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_bytes(payload)


def repository_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents:
        raise ValueError(f"input path escapes repository: {relative}")
    return path


def load_hashed_json(spec: dict[str, Any], label: str) -> dict[str, Any]:
    path = repository_path(spec["path"])
    actual = sha256_file(path)
    if actual != spec["sha256"]:
        raise ValueError(f"{label} SHA-256 mismatch: {actual}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_verified_text(spec: dict[str, Any]) -> str:
    path = repository_path(spec["path"])
    payload = path.read_bytes()
    actual = sha256_bytes(payload)
    if actual != spec["text_sha256"]:
        raise ValueError(f"verified transcript SHA-256 mismatch: {actual}")
    return payload.decode("utf-8")


def build_cues(
    transcript_id: str,
    canonical_text: str,
    frozen: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[tuple[int, int, str]]]:
    records: list[dict[str, Any]] = []
    spans: list[tuple[int, int, str]] = []
    cursor = 0
    segments = frozen.get("segments")
    if not isinstance(segments, list) or not segments:
        raise ValueError("frozen cues must contain a non-empty segments array")

    for sequence, segment in enumerate(segments):
        text = segment["text"]
        start = cursor
        end = start + len(text)
        if canonical_text[start:end] != text:
            raise ValueError(f"cue {sequence} does not match verified transcript")
        cue_id = f"{transcript_id}:cue:{sequence:06d}"
        records.append(
            {
                "char_end": end,
                "char_start": start,
                "id": cue_id,
                "lifecycle_status": "verified",
                "sequence": sequence,
                "source_locator": {
                    "end_seconds": segment["source_end"],
                    "start_seconds": segment["source_start"],
                    "type": "time_interval",
                },
                "text": text,
                "transcript_revision_id": transcript_id,
            }
        )
        spans.append((start, end, cue_id))
        cursor = end
        if sequence < len(segments) - 1:
            if canonical_text[cursor : cursor + 1] != "\n":
                raise ValueError(f"cue {sequence} is not followed by canonical LF")
            cursor += 1

    if canonical_text[cursor:] == "\n":
        cursor += 1
    if cursor != len(canonical_text):
        raise ValueError("frozen cues do not cover the complete verified transcript")
    return records, spans


def map_alignment(
    canonical_tokens: list[re.Match[str]],
    aligned_words: list[dict[str, Any]],
    expected_unaligned: list[dict[str, Any]],
) -> list[dict[str, Any] | None]:
    """Map an exact aligned-token subsequence without semantic normalization."""
    mapped: list[dict[str, Any] | None] = []
    aligned_index = 0
    for token in canonical_tokens:
        semantic_text = token.group(0)
        if (
            aligned_index < len(aligned_words)
            and aligned_words[aligned_index].get("word") == semantic_text
        ):
            mapped.append(aligned_words[aligned_index])
            aligned_index += 1
        else:
            mapped.append(None)

    if aligned_index != len(aligned_words):
        unexpected = aligned_words[aligned_index].get("word")
        raise ValueError(
            "alignment output is not an exact subsequence of verified text; "
            f"first unmatched aligned token: {unexpected!r}"
        )

    actual_unaligned = [
        {"sequence": sequence, "text": canonical_tokens[sequence].group(0)}
        for sequence, item in enumerate(mapped)
        if item is None
    ]
    if actual_unaligned != expected_unaligned:
        raise ValueError(
            "unaligned token set changed: "
            f"expected {expected_unaligned!r}, got {actual_unaligned!r}"
        )
    return mapped


def cue_for_span(
    start: int,
    end: int,
    cue_spans: list[tuple[int, int, str]],
    hint: int,
) -> tuple[str, int]:
    while hint < len(cue_spans) and start >= cue_spans[hint][1]:
        hint += 1
    if hint >= len(cue_spans):
        raise ValueError(f"word span [{start}, {end}) has no cue")
    cue_start, cue_end, cue_id = cue_spans[hint]
    if start < cue_start or end > cue_end:
        raise ValueError(f"word span [{start}, {end}) crosses cue boundary")
    return cue_id, hint


def build_words(
    manifest: dict[str, Any],
    evidence: dict[str, Any],
    transcript_id: str,
    source_id: str,
    canonical_text: str,
    cue_spans: list[tuple[int, int, str]],
    alignment_run_id: str,
) -> list[dict[str, Any]]:
    tokens = list(re.finditer(r"\S+", canonical_text))
    if len(tokens) != manifest["expected"]["word_count"]:
        raise ValueError("verified transcript word count changed")

    aligned_words = evidence.get("words")
    if not isinstance(aligned_words, list):
        raise ValueError("alignment evidence has no words array")
    mapped = map_alignment(tokens, aligned_words, manifest["expected"]["unaligned"])
    fragment = evidence["source_fragment"]
    offset = fragment["start_seconds"]
    fragment_duration = fragment["duration_seconds"]

    records: list[dict[str, Any]] = []
    cue_hint = 0
    previous_end: float | None = None
    for sequence, (token, aligned) in enumerate(zip(tokens, mapped)):
        cue_id, cue_hint = cue_for_span(
            token.start(), token.end(), cue_spans, cue_hint
        )
        qa_flags: list[str] = []
        if aligned is None:
            status = "unaligned"
            start_seconds = None
            end_seconds = None
            confidence = None
            timing_provenance = {
                "alignment_run_id": None,
                "kind": "unavailable",
                "method": None,
            }
            qa_flags.append("unaligned_review_required")
        else:
            relative_start = aligned.get("start")
            relative_end = aligned.get("end")
            if not isinstance(relative_start, (int, float)) or not isinstance(
                relative_end, (int, float)
            ):
                raise ValueError(f"aligned word {sequence} has incomplete timing")
            if relative_start < 0 or relative_end <= relative_start:
                raise ValueError(f"aligned word {sequence} has invalid interval")
            if relative_end > fragment_duration:
                raise ValueError(f"aligned word {sequence} exceeds fragment bounds")
            if previous_end is not None and relative_start < previous_end:
                raise ValueError(f"aligned word {sequence} overlaps prior timed word")
            previous_end = relative_end
            start_seconds = round(offset + relative_start, 6)
            end_seconds = round(offset + relative_end, 6)
            confidence = aligned.get("score")
            if confidence is not None and not 0 <= confidence <= 1:
                raise ValueError(f"aligned word {sequence} has invalid confidence")
            if confidence is not None and confidence < 0.1:
                qa_flags.append("low_alignment_confidence")
            if relative_end - relative_start > 5:
                qa_flags.append("unusually_long_interval")
            status = "aligned"
            timing_provenance = {
                "alignment_run_id": alignment_run_id,
                "kind": "forced_alignment",
                "method": None,
            }

        records.append(
            {
                "alignment_status": status,
                "char_end": token.end(),
                "char_start": token.start(),
                "confidence": confidence,
                "end_seconds": end_seconds,
                "id": f"{transcript_id}:word:{sequence:06d}",
                "lifecycle_status": "verified",
                "normalized_text": None,
                "qa_flags": qa_flags,
                "sequence": sequence,
                "source_cue_ids": [cue_id],
                "source_id": source_id,
                "speaker_id": None,
                "start_seconds": start_seconds,
                "text": token.group(0),
                "timing_provenance": timing_provenance,
                "transcript_revision_id": transcript_id,
            }
        )

    aligned_count = sum(item["alignment_status"] == "aligned" for item in records)
    if aligned_count != manifest["expected"]["aligned_words"]:
        raise ValueError(f"aligned word count changed: {aligned_count}")
    return records


def build_segments(
    transcript_id: str,
    words: list[dict[str, Any]],
    chunk_size: int,
) -> list[dict[str, Any]]:
    if not isinstance(chunk_size, int) or chunk_size < 1:
        raise ValueError("benchmark_word_chunk_size must be positive")
    records = []
    for sequence, start in enumerate(range(0, len(words), chunk_size)):
        group = words[start : start + chunk_size]
        records.append(
            {
                "id": f"segment_stress_code_video_001_fragment_r1_{sequence:06d}",
                "lifecycle_status": "verified",
                "sequence": sequence,
                "transcript_revision_id": transcript_id,
                "word_count": len(group),
                "word_end_id": group[-1]["id"],
                "word_start_id": group[0]["id"],
            }
        )
    return records


def build_evidence_refs(
    manifest: dict[str, Any],
    words: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    records = []
    for sequence in manifest["navigation_word_sequences"]:
        word = words[sequence]
        if word["alignment_status"] != "aligned":
            raise ValueError(f"navigation word {sequence} is not aligned")
        records.append(
            {
                "id": f"evidence_stress_code_video_001_word_{sequence:06d}",
                "lifecycle_status": "verified",
                "locator": {
                    "end_seconds": word["end_seconds"],
                    "start_seconds": word["start_seconds"],
                    "type": "time_interval",
                },
                "project_id": manifest["project"]["id"],
                "source_id": manifest["source"]["id"],
                "target": {"entity_id": word["id"], "entity_type": "word"},
                "transcript_revision_id": word["transcript_revision_id"],
            }
        )
    return sorted(records, key=lambda item: item["id"])


def build_bundle(manifest_path: Path) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("artifact_type") != "issue_42_word_timeline_population_manifest":
        raise ValueError("unexpected population manifest type")

    transcript_spec = manifest["transcript"]
    source_spec = manifest["source"]
    transcript_id = transcript_spec["id"]
    source_id = source_spec["id"]
    canonical_text = load_verified_text(transcript_spec)
    frozen_cues = load_hashed_json(manifest["cues"], "frozen cues")
    evidence = load_hashed_json(
        manifest["alignment_evidence"], "alignment evidence"
    )

    if evidence.get("invocation_role") != "alignment_only_no_asr":
        raise ValueError("alignment evidence is not alignment-only")
    if evidence["transcript"]["text_sha256"] != transcript_spec["text_sha256"]:
        raise ValueError("alignment evidence references another transcript")
    if evidence["transcript"]["segments_sha256"] != manifest["cues"]["sha256"]:
        raise ValueError("alignment evidence references another cue set")
    if evidence["source_fragment"]["parent_source_sha256"] != source_spec["content_sha256"]:
        raise ValueError("alignment evidence references another source")
    if evidence["source_fragment"]["parent_source_id"] != source_spec["legacy_source_id"]:
        raise ValueError("alignment evidence source identity mismatch")

    alignment = evidence["alignment"]
    if canonical_hash(alignment["config"]) != alignment["config_sha256"]:
        raise ValueError("alignment configuration hash mismatch")
    run_hashes = alignment.get("run_result_sha256")
    if not isinstance(run_hashes, list) or len(run_hashes) < 2 or len(set(run_hashes)) != 1:
        raise ValueError("frozen alignment repeat runs are not deterministic")

    cues, cue_spans = build_cues(transcript_id, canonical_text, frozen_cues)
    if len(cues) != manifest["expected"]["cue_count"]:
        raise ValueError("frozen cue count changed")
    alignment_run_id = "alignment_stress_code_video_001_fragment_r1_whisperx_3.8.6"
    words = build_words(
        manifest,
        evidence,
        transcript_id,
        source_id,
        canonical_text,
        cue_spans,
        alignment_run_id,
    )
    segments = build_segments(
        transcript_id, words, manifest["benchmark_word_chunk_size"]
    )

    bundle = {
        "alignment_runs": [
            {
                "aligner": alignment["aligner"],
                "aligner_version": alignment["aligner_version"],
                "config_sha256": alignment["config_sha256"],
                "id": alignment_run_id,
                "model": alignment["model"],
                "model_revision": alignment["model_revision"],
                "model_sha256": alignment["model_sha256"],
                "source_content_sha256": source_spec["content_sha256"],
                "source_id": source_id,
                "status": "valid",
                "transcript_revision_id": transcript_id,
                "transcript_text_sha256": transcript_spec["text_sha256"],
            }
        ],
        "artifact_id": manifest["artifact_id"],
        "artifact_type": "seminartext.canonical_evidence",
        "benchmark_segments": segments,
        "cues": cues,
        "evidence_refs": build_evidence_refs(manifest, words),
        "project": {
            "id": manifest["project"]["id"],
            "lifecycle_status": "active",
            "title": manifest["project"]["title"],
        },
        "schema_version": "1.0.0",
        "sources": [
            {
                "content_sha256": source_spec["content_sha256"],
                "duration_seconds": source_spec["duration_seconds"],
                "id": source_id,
                "kind": source_spec["kind"],
                "lifecycle_status": "active",
                "project_id": manifest["project"]["id"],
                "sequence": 0,
                "title": source_spec["title"],
            }
        ],
        "topics": [],
        "transcript_revisions": [
            {
                "authority": "authoritative",
                "canonical_text": canonical_text,
                "id": transcript_id,
                "lifecycle_status": "verified",
                "parent_revision_id": None,
                "revision_kind": transcript_spec["revision_kind"],
                "revision_number": transcript_spec["revision_number"],
                "source_id": source_id,
                "text_sha256": transcript_spec["text_sha256"],
            }
        ],
        "words": words,
    }
    errors = validate_bundle(bundle)
    if errors:
        raise ValueError("canonical cross-record validation failed:\n" + "\n".join(errors))
    return bundle


def validate_json_schema(bundle: dict[str, Any], schema_path: Path) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(
            "JSON Schema validation requested; install jsonschema in an isolated "
            "test environment"
        ) from exc
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(bundle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--schema", type=Path)
    args = parser.parse_args()

    bundle = build_bundle(args.manifest.resolve())
    if args.schema is not None:
        validate_json_schema(bundle, args.schema.resolve())
    payload = canonical_bytes(bundle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "sha256": sha256_bytes(payload),
                "words": len(bundle["words"]),
                "aligned": sum(
                    word["alignment_status"] == "aligned"
                    for word in bundle["words"]
                ),
                "unaligned": sum(
                    word["alignment_status"] == "unaligned"
                    for word in bundle["words"]
                ),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
