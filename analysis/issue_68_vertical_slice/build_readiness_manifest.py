#!/usr/bin/env python3
"""Build the fail-closed Issue #68 real-project readiness manifest.

This tool inventories existing Canonical Evidence and applied human Topic
review.  It never authors Topics, Concepts, or review decisions and never
writes into the inspected project.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_source_id(registry_id: str) -> str:
    return f"source_{registry_id}"


def sample_word(word: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": word["id"],
        "sequence": word["sequence"],
        "alignment_status": word["alignment_status"],
        "start_seconds": word.get("start_seconds"),
        "end_seconds": word.get("end_seconds"),
    }


def build_manifest(project: Path, review_result_path: Path) -> dict[str, Any]:
    bundle_path = project / "evidence" / "canonical_bundle.json"
    evidence_manifest_path = project / "evidence" / "manifest.json"
    source_registry_path = project / "sources.json"

    bundle = read_json(bundle_path)
    evidence_manifest = read_json(evidence_manifest_path)
    source_registry = read_json(source_registry_path)
    review_result = read_json(review_result_path)

    errors: list[str] = []
    bundle_hash = sha256(bundle_path)
    if evidence_manifest.get("bundle_sha256") != bundle_hash:
        errors.append("evidence manifest bundle_sha256 does not match canonical bundle")
    if review_result.get("application_status") != "APPLIED":
        errors.append("human Topic review result is not APPLIED")
    review_evidence = review_result.get("canonical_evidence", {})
    if review_evidence.get("artifact_id") != bundle.get("artifact_id"):
        errors.append("review result is bound to a different Canonical Evidence artifact")
    if review_evidence.get("sha256") != bundle_hash:
        errors.append("review result Canonical Evidence hash does not match the project bundle")

    sources = {item["id"]: item for item in bundle.get("sources", [])}
    revisions = {item["id"]: item for item in bundle.get("transcript_revisions", [])}
    alignments_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in bundle.get("alignment_runs", []):
        alignments_by_source[item["source_id"]].append(item)

    words_by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    word_by_id: dict[str, dict[str, Any]] = {}
    for word in bundle.get("words", []):
        words_by_source[word["source_id"]].append(word)
        word_by_id[word["id"]] = word
    for source_words in words_by_source.values():
        source_words.sort(key=lambda item: item["sequence"])

    reviewed_units = list(review_result.get("semantic_knowledge", [])) + list(
        review_result.get("seminar_structure", [])
    )
    reviewed_by_source = Counter(item["source_id"] for item in reviewed_units)
    for unit in reviewed_units:
        start = word_by_id.get(unit["word_start_id"])
        end = word_by_id.get(unit["word_end_id"])
        if start is None or end is None:
            errors.append(f"reviewed unit {unit['id']} has an unresolved Word range")
            continue
        if start["source_id"] != unit["source_id"] or end["source_id"] != unit["source_id"]:
            errors.append(f"reviewed unit {unit['id']} crosses its declared source")
        if start["sequence"] != unit["word_start_sequence"] or end["sequence"] != unit["word_end_sequence"]:
            errors.append(f"reviewed unit {unit['id']} Word sequence does not match its IDs")

    evidence_coverage = {
        item["canonical_source_id"]: item["evidence_status"]
        for item in evidence_manifest.get("registry_coverage", [])
    }
    registry_items: list[tuple[str, str, str]] = []
    for item in source_registry.get("videos", []):
        registry_items.append((item["source_id"], "video", item["title"]))
    for item in source_registry.get("documents", []):
        registry_items.append((item["source_id"], item["type"], item["title"]))

    coverage: list[dict[str, Any]] = []
    video_ids: list[str] = []
    missing_semantic_sources: list[str] = []
    for registry_id, kind, title in registry_items:
        source_id = canonical_source_id(registry_id)
        source_words = words_by_source.get(source_id, [])
        alignment_counts = Counter(word.get("alignment_status") for word in source_words)
        if kind == "video":
            video_ids.append(source_id)
        semantic_count = reviewed_by_source[source_id]
        if kind == "video" and semantic_count == 0:
            missing_semantic_sources.append(source_id)

        samples: dict[str, Any] = {}
        if source_words:
            samples = {
                "beginning": sample_word(source_words[0]),
                "middle": sample_word(source_words[len(source_words) // 2]),
                "end": sample_word(source_words[-1]),
            }
        coverage.append(
            {
                "registry_id": registry_id,
                "canonical_source_id": source_id,
                "kind": kind,
                "title": title,
                "evidence_status": evidence_coverage.get(source_id, "UNREGISTERED"),
                "canonical_source_present": source_id in sources,
                "transcript_revision_count": sum(
                    1 for revision in revisions.values() if revision["source_id"] == source_id
                ),
                "alignment_run_count": len(alignments_by_source[source_id]),
                "word_count": len(source_words),
                "aligned_word_count": alignment_counts["aligned"],
                "unaligned_word_count": alignment_counts["unaligned"],
                "reviewed_topic_unit_count": semantic_count,
                "semantic_coverage": (
                    "DOMAIN_REVIEW_APPLIED" if semantic_count else "SEMANTIC_INPUT_UNAVAILABLE"
                ),
                "trace_samples": samples,
            }
        )

    video_evidence_ready = all(
        sources.get(source_id)
        and words_by_source.get(source_id)
        and alignments_by_source.get(source_id)
        and evidence_coverage.get(source_id) == "COMPOSED"
        for source_id in video_ids
    )
    transcript_assurance = Counter(
        revision.get("transcript_provenance", {}).get("verification_state", "UNDECLARED")
        for revision in revisions.values()
    )
    locator_types = sorted(
        {
            "time_interval"
            for word in word_by_id.values()
            if word.get("start_seconds") is not None and word.get("end_seconds") is not None
        }
    )

    concept_count = 0
    blockers = [
        {
            "id": "MISSING_SOURCE_TOPIC_SEMANTICS",
            "gate": "DOMAIN_AUTHORING",
            "sources": missing_semantic_sources,
            "reason": "No eligible human-authored/reviewed Topic input exists for these sources.",
        },
        {
            "id": "MISSING_CANONICAL_CONCEPT_SEMANTICS",
            "gate": "DOMAIN_AUTHORING",
            "sources": video_ids,
            "reason": "The applied Topic review contains no authoritative Canonical Concepts; the required Topic -> Concept -> Evidence path cannot be asserted.",
        },
        {
            "id": "DOCUMENT_EVIDENCE_CONTRACT_UNAVAILABLE",
            "gate": "FUTURE_ENGINEERING_SCOPE",
            "sources": [
                canonical_source_id(registry_id)
                for registry_id, kind, _ in registry_items
                if kind != "video"
            ],
            "reason": "Registered presentation/handouts have no Canonical Evidence or page/slide locator contract in the current bridge.",
        },
    ]

    status = "INVALID" if errors else "BLOCKED_AT_DOMAIN_AUTHORING"
    gates = {
        "canonical_evidence": "FAIL" if errors else "PASS",
        "all_video_sources_traced": "PASS" if video_evidence_ready and not errors else "FAIL",
        "day_1_topic_domain_review": (
            "PASS" if reviewed_by_source["source_video_001"] > 0 and not errors else "FAIL"
        ),
        "all_video_topic_semantics": "BLOCKED_DOMAIN_AUTHORING",
        "canonical_concept_path": "BLOCKED_DOMAIN_AUTHORING",
        "obsidian_export": "NOT_RUN_BLOCKED_SEMANTIC_INPUT",
    }

    return {
        "schema_version": "1.0.0",
        "artifact_type": "seminartext.issue_68_readiness_manifest",
        "artifact_id": "issue_68_stress_code_readiness_v1",
        "status": status,
        "project": {
            "id": bundle["project"]["id"],
            "title": bundle["project"]["title"],
            "canonical_evidence_artifact_id": bundle["artifact_id"],
            "canonical_evidence_sha256": bundle_hash,
            "evidence_manifest_sha256": sha256(evidence_manifest_path),
            "source_registry_sha256": sha256(source_registry_path),
            "topic_review_result_artifact_id": review_result["artifact_id"],
            "topic_review_result_sha256": sha256(review_result_path),
            "topic_decision_artifact": review_result.get("decision_artifact"),
        },
        "inventory": {
            "registered_source_count": len(registry_items),
            "registered_video_count": len(video_ids),
            "registered_document_count": len(registry_items) - len(video_ids),
            "composed_source_count": len(sources),
            "transcript_revision_count": len(revisions),
            "word_count": len(word_by_id),
            "reviewed_source_topic_snapshot_count": len(
                review_result.get("source_topic_snapshots", [])
            ),
            "reviewed_semantic_topic_unit_count": len(review_result.get("semantic_knowledge", [])),
            "reviewed_structure_unit_count": len(review_result.get("seminar_structure", [])),
            "canonical_concept_count": concept_count,
            "transcript_assurance": dict(sorted(transcript_assurance.items())),
            "locator_types": locator_types,
        },
        "coverage": coverage,
        "gates": gates,
        "blockers": blockers,
        "claims": {
            "full_registered_source_evidence_coverage": evidence_manifest.get(
                "all_registered_sources_composed", False
            ),
            "full_video_evidence_coverage": video_evidence_ready,
            "full_video_semantic_coverage": not missing_semantic_sources,
            "full_seminar_knowledge_coverage": False,
            "multi_source_vertical_slice": "PARTIAL",
            "cross_seminar_ready_next": False,
        },
        "human_gate": {
            "classification": "DOMAIN_AUTHORING",
            "required_inputs": [
                "Authoritative eligible Topic inputs for source_video_002, source_video_003, and source_video_004.",
                "Authoritative minimal Canonical Concept identities/content and explicit Topic-to-Concept links needed to exercise Seminar -> Source/Topic -> Concept -> Evidence.",
            ],
            "domain_review_after_authoring": "REQUIRED",
        },
        "safety": {
            "machine_transcript_assurance_preserved": True,
            "semantic_acceptance_inferred": False,
            "topics_or_concepts_authored": False,
            "project_files_modified": False,
            "obsidian_export_attempted": False,
            "dataset_d_or_e_accessed": False,
            "gold_modified": False,
        },
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--review-result", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    manifest = build_manifest(args.project.resolve(), args.review_result.resolve())
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")
    return 1 if manifest["status"] == "INVALID" else 0


if __name__ == "__main__":
    raise SystemExit(main())
