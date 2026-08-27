#!/usr/bin/env python3
"""Build and validate the bounded Issue #44 Golden Knowledge Slice."""

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


ID_RE = re.compile(r"^[a-z][a-z0-9._:-]{2,127}$")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_bytes(document: dict[str, Any]) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def repository_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if ROOT not in path.parents:
        raise ValueError(f"input path escapes repository: {relative}")
    return path


def aligned_envelope(
    words: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[str], str]:
    aligned = [word for word in words if word["alignment_status"] == "aligned"]
    if not aligned:
        raise ValueError("knowledge evidence range has no aligned timing anchor")
    unaligned_ids = [
        word["id"] for word in words if word["alignment_status"] == "unaligned"
    ]
    timing_status = (
        "aligned_word_range"
        if not unaligned_ids
        else "aligned_envelope_with_explicit_unaligned_words"
    )
    locator = {
        "end_seconds": aligned[-1]["end_seconds"],
        "start_seconds": aligned[0]["start_seconds"],
        "type": "time_interval",
    }
    return locator, unaligned_ids, timing_status


def range_words(
    words: list[dict[str, Any]], start: int, end: int
) -> list[dict[str, Any]]:
    if not isinstance(start, int) or not isinstance(end, int):
        raise ValueError("word range endpoints must be integer sequences")
    if start < 0 or end < start or end >= len(words):
        raise ValueError(f"invalid canonical Word range [{start}, {end}]")
    selected = words[start : end + 1]
    if [word["sequence"] for word in selected] != list(range(start, end + 1)):
        raise ValueError("canonical Word sequence is not contiguous")
    return selected


def build_evidence(
    specs: list[dict[str, Any]],
    words: list[dict[str, Any]],
    transcript_text: str,
    source_id: str,
    transcript_id: str,
) -> list[dict[str, Any]]:
    records = []
    for spec in specs:
        selected = range_words(
            words, spec["word_start_sequence"], spec["word_end_sequence"]
        )
        locator, unaligned_ids, timing_status = aligned_envelope(selected)
        char_start = selected[0]["char_start"]
        char_end = selected[-1]["char_end"]
        records.append(
            {
                "canonical_source_id": source_id,
                "canonical_transcript_revision_id": transcript_id,
                "canonical_word_end_id": selected[-1]["id"],
                "canonical_word_start_id": selected[0]["id"],
                "claim": spec["claim"],
                "id": spec["id"],
                "locator": locator,
                "quote": transcript_text[char_start:char_end],
                "sequence": spec["sequence"],
                "timing_status": timing_status,
                "unaligned_word_ids": unaligned_ids,
            }
        )
    return records


def build_topics(
    specs: list[dict[str, Any]],
    words: list[dict[str, Any]],
    source_id: str,
    transcript_id: str,
) -> list[dict[str, Any]]:
    records = []
    for spec in specs:
        selected = range_words(
            words, spec["word_start_sequence"], spec["word_end_sequence"]
        )
        locator, unaligned_ids, timing_status = aligned_envelope(selected)
        records.append(
            {
                "canonical_source_id": source_id,
                "canonical_transcript_revision_id": transcript_id,
                "canonical_word_end_id": selected[-1]["id"],
                "canonical_word_start_id": selected[0]["id"],
                "concept_ids": spec["concept_ids"],
                "coverage": spec["coverage"],
                "evidence_ids": spec["evidence_ids"],
                "id": spec["id"],
                "locator": locator,
                "sequence": spec["sequence"],
                "structure_origin": spec["structure_origin"],
                "structure_provenance": spec["structure_provenance"],
                "summary": spec["summary"],
                "timing_status": timing_status,
                "title": spec["title"],
                "unaligned_word_ids": unaligned_ids,
            }
        )
    return records


def build_slice(curation_path: Path) -> dict[str, Any]:
    curation = json.loads(curation_path.read_text(encoding="utf-8"))
    if curation.get("artifact_type") != "issue_44_golden_knowledge_slice_curation":
        raise ValueError("unexpected curation artifact type")
    canonical_spec = curation["canonical_bundle"]
    canonical_path = repository_path(canonical_spec["path"])
    canonical_payload = canonical_path.read_bytes()
    actual_hash = sha256_bytes(canonical_payload)
    if actual_hash != canonical_spec["sha256"]:
        raise ValueError(f"canonical bundle SHA-256 mismatch: {actual_hash}")
    canonical = json.loads(canonical_payload)
    canonical_errors = validate_bundle(canonical)
    if canonical_errors:
        raise ValueError(
            "source Canonical Evidence bundle is invalid:\n"
            + "\n".join(canonical_errors)
        )

    project = canonical["project"]
    if project["id"] != curation["project_id"]:
        raise ValueError("curation project does not match canonical project")
    sources = {source["id"]: source for source in canonical["sources"]}
    source = sources.get(curation["source_id"])
    if source is None:
        raise ValueError("curation source does not resolve in canonical bundle")
    transcripts = [
        item
        for item in canonical["transcript_revisions"]
        if item["source_id"] == source["id"] and item["authority"] == "authoritative"
    ]
    if len(transcripts) != 1:
        raise ValueError("expected exactly one authoritative canonical transcript")
    transcript = transcripts[0]
    words = [
        word
        for word in canonical["words"]
        if word["transcript_revision_id"] == transcript["id"]
    ]

    evidence = build_evidence(
        curation["evidence"],
        words,
        transcript["canonical_text"],
        source["id"],
        transcript["id"],
    )
    topics = build_topics(
        curation["topics"], words, source["id"], transcript["id"]
    )
    concepts = [
        {
            "aliases": spec["aliases"],
            "derivation_status": "provisional_manual_curation",
            "description": spec["description"],
            "evidence_ids": spec["evidence_ids"],
            "id": spec["id"],
            "identity_rationale": spec["identity_rationale"],
            "preferred_label": spec["preferred_label"],
            "review_status": spec["review_status"],
            "sequence": spec["sequence"],
            "topic_ids": spec["topic_ids"],
        }
        for spec in curation["concepts"]
    ]

    document = {
        "artifact_id": curation["artifact_id"],
        "artifact_type": "seminartext.golden_knowledge_slice",
        "canonical_evidence": {
            "artifact_id": canonical["artifact_id"],
            "path": canonical_spec["path"],
            "schema_version": canonical["schema_version"],
            "sha256": canonical_spec["sha256"],
        },
        "concepts": concepts,
        "evidence": evidence,
        "product_review": {
            "required": True,
            "status": "pending",
        },
        "schema_version": "1.0.0",
        "seminar": {
            "canonical_project_id": project["id"],
            "id": curation["seminar"]["id"],
            "source_ids": [source["id"]],
            "title": curation["seminar"]["title"],
            "topic_ids": [topic["id"] for topic in topics],
        },
        "sources": [
            {
                "canonical_source_id": source["id"],
                "content_sha256": source["content_sha256"],
                "duration_seconds": source["duration_seconds"],
                "id": source["id"],
                "kind": source["kind"],
                "title": source["title"],
            }
        ],
        "topics": topics,
    }
    errors = validate_slice(document, canonical)
    if errors:
        raise ValueError("Golden Slice validation failed:\n" + "\n".join(errors))
    return document


def validate_slice(
    document: dict[str, Any], canonical: dict[str, Any]
) -> list[str]:
    errors: list[str] = []
    if document.get("schema_version") != "1.0.0":
        errors.append("schema_version must be 1.0.0")
    if document.get("artifact_type") != "seminartext.golden_knowledge_slice":
        errors.append("unexpected artifact_type")

    collections = {
        "source": document.get("sources", []),
        "topic": document.get("topics", []),
        "concept": document.get("concepts", []),
        "evidence": document.get("evidence", []),
    }
    all_ids = [document.get("seminar", {}).get("id")]
    for records in collections.values():
        all_ids.extend(record.get("id") for record in records)
    if any(not isinstance(item, str) or ID_RE.fullmatch(item) is None for item in all_ids):
        errors.append("all entity IDs must be stable lowercase namespaced IDs")
    duplicates = sorted({item for item in all_ids if all_ids.count(item) > 1})
    if duplicates:
        errors.append(f"entity IDs are not unique: {duplicates}")

    for name in ("topics", "concepts", "evidence"):
        records = document.get(name, [])
        sequences = [record.get("sequence") for record in records]
        if sequences != list(range(len(records))):
            errors.append(f"{name} sequence/order is not deterministic")
        if records != sorted(records, key=lambda item: (item["sequence"], item["id"])):
            errors.append(f"{name} records are not deterministically ordered")

    canonical_words = {word["id"]: word for word in canonical["words"]}
    canonical_sources = {source["id"]: source for source in canonical["sources"]}
    canonical_transcripts = {
        item["id"]: item for item in canonical["transcript_revisions"]
    }
    evidence = {item["id"]: item for item in document.get("evidence", [])}
    topics = {item["id"]: item for item in document.get("topics", [])}
    concepts = {item["id"]: item for item in document.get("concepts", [])}

    for item in evidence.values():
        first = canonical_words.get(item.get("canonical_word_start_id"))
        last = canonical_words.get(item.get("canonical_word_end_id"))
        source = canonical_sources.get(item.get("canonical_source_id"))
        transcript = canonical_transcripts.get(
            item.get("canonical_transcript_revision_id")
        )
        if first is None or last is None or source is None or transcript is None:
            errors.append(f"{item['id']}: orphan canonical reference")
            continue
        if first["source_id"] != source["id"] or last["source_id"] != source["id"]:
            errors.append(f"{item['id']}: cross-source Word range")
        if (
            first["transcript_revision_id"] != transcript["id"]
            or last["transcript_revision_id"] != transcript["id"]
        ):
            errors.append(f"{item['id']}: cross-revision Word range")
        start, end = first["sequence"], last["sequence"]
        if end < start:
            errors.append(f"{item['id']}: inverted Word range")
            continue
        selected = canonical["words"][start : end + 1]
        char_start, char_end = first["char_start"], last["char_end"]
        if item.get("quote") != transcript["canonical_text"][char_start:char_end]:
            errors.append(f"{item['id']}: quote does not match canonical text")
        aligned = [word for word in selected if word["alignment_status"] == "aligned"]
        expected_locator = {
            "end_seconds": aligned[-1]["end_seconds"],
            "start_seconds": aligned[0]["start_seconds"],
            "type": "time_interval",
        }
        if item.get("locator") != expected_locator:
            errors.append(f"{item['id']}: locator is not the canonical aligned envelope")
        expected_unaligned = [
            word["id"]
            for word in selected
            if word["alignment_status"] == "unaligned"
        ]
        if item.get("unaligned_word_ids") != expected_unaligned:
            errors.append(f"{item['id']}: unaligned limitations are incomplete")
        expected_status = (
            "aligned_word_range"
            if not expected_unaligned
            else "aligned_envelope_with_explicit_unaligned_words"
        )
        if item.get("timing_status") != expected_status:
            errors.append(f"{item['id']}: timing status is inaccurate")

    for topic in topics.values():
        if topic.get("structure_origin") not in {"gold_dataset_a", "manual_issue_44"}:
            errors.append(f"{topic['id']}: prohibited automatic Topic origin")
        missing_evidence = [item for item in topic["evidence_ids"] if item not in evidence]
        missing_concepts = [item for item in topic["concept_ids"] if item not in concepts]
        if missing_evidence or missing_concepts:
            errors.append(f"{topic['id']}: orphan knowledge references")
        first = canonical_words.get(topic.get("canonical_word_start_id"))
        last = canonical_words.get(topic.get("canonical_word_end_id"))
        if first is None or last is None:
            errors.append(f"{topic['id']}: orphan Topic Word range")
            continue
        for evidence_id in topic["evidence_ids"]:
            if evidence_id not in evidence:
                continue
            item = evidence[evidence_id]
            ev_first = canonical_words[item["canonical_word_start_id"]]["sequence"]
            ev_last = canonical_words[item["canonical_word_end_id"]]["sequence"]
            if ev_first < first["sequence"] or ev_last > last["sequence"]:
                errors.append(f"{topic['id']}: evidence {evidence_id} is outside Topic")

    for concept in concepts.values():
        if concept.get("derivation_status") != "provisional_manual_curation":
            errors.append(f"{concept['id']}: Concept must remain provisional")
        if concept.get("review_status") != "product_review_required":
            errors.append(f"{concept['id']}: Product Review must remain explicit")
        if not concept.get("topic_ids") or not concept.get("evidence_ids"):
            errors.append(f"{concept['id']}: Concept has no Topic or Evidence")
        if concept.get("preferred_label") in concept.get("aliases", []):
            errors.append(f"{concept['id']}: preferred label duplicated as alias")
        if len(concept.get("aliases", [])) != len(set(concept.get("aliases", []))):
            errors.append(f"{concept['id']}: duplicate aliases")
        for topic_id in concept.get("topic_ids", []):
            topic = topics.get(topic_id)
            if topic is None or concept["id"] not in topic["concept_ids"]:
                errors.append(f"{concept['id']}: non-reciprocal Topic link {topic_id}")
        for evidence_id in concept.get("evidence_ids", []):
            item = evidence.get(evidence_id)
            if item is None:
                errors.append(f"{concept['id']}: orphan Evidence {evidence_id}")
                continue
            if not any(
                evidence_id in topics[topic_id]["evidence_ids"]
                for topic_id in concept.get("topic_ids", [])
                if topic_id in topics
            ):
                errors.append(
                    f"{concept['id']}: Evidence {evidence_id} is outside linked Topics"
                )

    seminar = document.get("seminar", {})
    if seminar.get("source_ids") != [item["id"] for item in document.get("sources", [])]:
        errors.append("Seminar Source links are incomplete")
    if seminar.get("topic_ids") != [item["id"] for item in document.get("topics", [])]:
        errors.append("Seminar Topic links are incomplete")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curation", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    document = build_slice(args.curation.resolve())
    payload = canonical_bytes(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(
        json.dumps(
            {
                "concepts": len(document["concepts"]),
                "evidence": len(document["evidence"]),
                "output": str(args.output),
                "sha256": sha256_bytes(payload),
                "topics": len(document["topics"]),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
