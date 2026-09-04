#!/usr/bin/env python3
"""Build the complete Issue #113 governed V2 decision artifact without applying it."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from seminartext_modules.human_review_workflow import (  # noqa: E402
    canonical_bytes,
    load_package,
    validate_decisions_v2,
    validate_schema_v2,
)


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_word_id(revision_id: str, sequence: int) -> str:
    return f"{revision_id}:word:{sequence:06d}"


def build_artifact(project: Path, plan_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    plan = read_json(plan_path)
    package_spec = plan["review_package"]
    package_path = project / package_spec["path"]
    if sha256(package_path) != package_spec["sha256"]:
        raise ValueError("source Human Review package SHA-256 mismatch")
    package, bundle = load_package(project, package_path)
    topics = sorted(package["topics"], key=lambda item: item["sequence"])
    topic_by_id = {item["id"]: item for item in topics}

    semantic_records = []
    semantic_by_number: dict[int, dict[str, Any]] = {}
    for item in plan["semantic_decisions"]:
        number = item["review_item_number"]
        if number in semantic_by_number:
            raise ValueError(f"duplicate semantic decision number {number}")
        record = {
            "id": f"issue_113_semantic_decision_{number:02d}",
            "review_item_number": number,
            "source_topic_id": item["source_topic_id"],
            "authoritative_outcome": item["authoritative_outcome"],
        }
        semantic_by_number[number] = record
        semantic_records.append(record)
    expected_semantic_count = plan["expected_semantic_decision_count"]
    if sorted(semantic_by_number) != list(range(1, expected_semantic_count + 1)):
        raise ValueError("authoritative semantic decision inventory is incomplete")
    if {item["source_topic_id"] for item in semantic_records} != set(topic_by_id):
        raise ValueError("authoritative semantic decision Topic inventory is incomplete")

    boundary_sources = []
    resolved_boundaries = []
    boundary_by_id: dict[str, dict[str, Any]] = {}
    for source_spec in plan["boundary_decision_sources"]:
        source_path = project / source_spec["path"]
        source_sha = sha256(source_path)
        if source_sha != source_spec["sha256"]:
            raise ValueError(f"boundary decision SHA-256 mismatch: {source_path}")
        source = read_json(source_path)
        validate_schema_v2(source)
        if source.get("artifact_type") != "seminartext.boundary_review_decisions":
            raise ValueError(f"boundary decision contract mismatch: {source_path}")
        if source.get("authority") != "PRODUCT_OWNER_DOMAIN_REVIEW":
            raise ValueError(f"boundary authority mismatch: {source_path}")
        if source.get("unresolved_review_required") != []:
            raise ValueError(f"unresolved exact boundaries remain: {source_path}")
        if source.get("review_package", {}).get("sha256") != package_spec["sha256"]:
            raise ValueError(f"boundary source refers to another review package: {source_path}")
        boundary_sources.append(
            {
                "artifact_id": source["artifact_id"],
                "sha256": source_sha,
                "authority": source["authority"],
                "decision_count": len(source["decisions"]),
            }
        )
        for decision in source["decisions"]:
            boundary_id = decision["boundary_proposal_id"]
            if boundary_id in boundary_by_id:
                raise ValueError(f"duplicate exact boundary {boundary_id}")
            record = {
                "boundary_proposal_id": boundary_id,
                "canonical_word_id": decision["canonical_word_id"],
                "timestamp": decision["timestamp"],
                "source_artifact_id": source["artifact_id"],
                "source_artifact_sha256": source_sha,
                "authority": source["authority"],
                "status": decision["status"],
            }
            boundary_by_id[boundary_id] = record
            resolved_boundaries.append(record)
    if len(boundary_by_id) != plan["expected_boundary_decision_count"]:
        raise ValueError("authoritative exact-boundary inventory is incomplete")
    resolved_boundaries.sort(key=lambda item: int(item["canonical_word_id"].rsplit(":", 1)[1]))

    transformations = []
    normalized_for_audit = []
    used_semantic_numbers: set[int] = set()
    used_boundary_refs: set[str] = set()
    fragment_counter = 0
    result_sequence = 0
    for spec in plan["transformations"]:
        semantic_numbers = spec["semantic_decision_numbers"]
        if used_semantic_numbers.intersection(semantic_numbers):
            raise ValueError(f"semantic decision reused by {spec['id']}")
        used_semantic_numbers.update(semantic_numbers)
        semantic_refs = [semantic_by_number[number]["id"] for number in semantic_numbers]
        target_ids = [semantic_by_number[number]["source_topic_id"] for number in semantic_numbers]
        target_topics = sorted((topic_by_id[item] for item in target_ids), key=lambda item: item["sequence"])
        target_ids = [item["id"] for item in target_topics]
        for previous, current in zip(target_topics, target_topics[1:]):
            if current["word_start_sequence"] != previous["word_end_sequence"] + 1:
                raise ValueError(f"non-contiguous transformation targets in {spec['id']}")
        minimum = target_topics[0]["word_start_sequence"]
        maximum = target_topics[-1]["word_end_sequence"]

        result_specs = sorted(spec["results"], key=lambda item: item["word_start_sequence"])
        expected = minimum
        for result_spec in result_specs:
            if result_spec["word_start_sequence"] != expected:
                raise ValueError(f"result gap or overlap in {spec['id']}")
            expected = result_spec["word_end_sequence"] + 1
        if expected != maximum + 1:
            raise ValueError(f"transformation does not cover complete source span: {spec['id']}")

        fragments = []
        results = []
        for result_spec in result_specs:
            refs = []
            evidence_refs = []
            for topic in target_topics:
                start = max(result_spec["word_start_sequence"], topic["word_start_sequence"])
                end = min(result_spec["word_end_sequence"], topic["word_end_sequence"])
                if start > end:
                    continue
                fragment_counter += 1
                fragment_id = f"issue_113_fragment_{fragment_counter:03d}"
                fragment = {
                    "id": fragment_id,
                    "source_topic_id": topic["id"],
                    "source_id": topic["source_id"],
                    "transcript_revision_id": topic["transcript_revision_id"],
                    "word_start_id": canonical_word_id(topic["transcript_revision_id"], start),
                    "word_end_id": canonical_word_id(topic["transcript_revision_id"], end),
                    "evidence_refs": topic["evidence_refs"],
                }
                fragments.append(fragment)
                refs.append(fragment_id)
                evidence_refs.extend(topic["evidence_refs"])
            results.append(
                {
                    "id": result_spec["id"],
                    "disposition": result_spec["disposition"],
                    "title": result_spec["title"],
                    "summary": "",
                    "sequence": result_sequence,
                    "fragment_refs": refs,
                    "evidence_refs": sorted(set(evidence_refs)),
                }
            )
            result_sequence += 1

        boundary_refs = spec["boundary_decision_refs"]
        if used_boundary_refs.intersection(boundary_refs):
            raise ValueError(f"exact boundary reused by {spec['id']}")
        if any(item not in boundary_by_id for item in boundary_refs):
            raise ValueError(f"unknown exact boundary in {spec['id']}")
        used_boundary_refs.update(boundary_refs)
        transformation = {
            "id": spec["id"],
            "operations": spec["operations"],
            "target_ids": target_ids,
            "expected_topics": [
                {"topic_id": topic["id"], "topic_sha256": topic["topic_sha256"]}
                for topic in target_topics
            ],
            "source_fragments": fragments,
            "results": results,
            "reason": " | ".join(semantic_by_number[number]["authoritative_outcome"] for number in semantic_numbers),
            "timestamp": plan["decision_timestamp"],
            "semantic_decision_refs": semantic_refs,
            "boundary_decision_refs": boundary_refs,
        }
        transformations.append(transformation)
        normalized_for_audit.append(
            {
                "spec": spec,
                "transformation": transformation,
                "semantic_numbers": semantic_numbers,
                "result_specs": result_specs,
            }
        )

    if used_semantic_numbers != set(semantic_by_number):
        raise ValueError("not all authoritative semantic decisions are mapped")
    if used_boundary_refs != set(boundary_by_id):
        raise ValueError("not all authoritative exact boundaries are mapped")

    artifact = {
        "schema_version": "2.0.0",
        "artifact_type": "seminartext.topic_review_decisions",
        "artifact_id": plan["artifact_id"],
        "review_package_id": package["artifact_id"],
        "review_package_sha256": package_spec["sha256"],
        "reviewer": plan["reviewer"],
        "boundary_authority": "PRODUCT_OWNER_DOMAIN_REVIEW",
        "authoritative_semantic_decisions": semantic_records,
        "exact_boundary_provenance": {
            "authority": "PRODUCT_OWNER_DOMAIN_REVIEW",
            "sources": boundary_sources,
            "resolved_boundaries": resolved_boundaries,
        },
        "decisions": transformations,
        "limitations": plan["limitations"],
    }
    validate_schema_v2(artifact)
    validate_decisions_v2(
        package_path,
        package,
        bundle,
        artifact,
        require_complete=True,
        require_approved_boundaries=True,
    )
    return artifact, normalized_for_audit


def render_audit(artifact: dict[str, Any], audit_data: list[dict[str, Any]]) -> str:
    transformations = {item["transformation"]["id"]: item for item in audit_data}
    by_semantic_ref = {
        semantic_ref: item
        for item in audit_data
        for semantic_ref in item["transformation"]["semantic_decision_refs"]
    }
    lines = [
        "# Issue #113 complete V2 semantic-decision audit mapping",
        "",
        "This document is deterministic derived audit output. The governed JSON artifact is authoritative.",
        "No semantic decisions are applied by this report.",
        "",
        f"- Authoritative semantic decisions: `{len(artifact['authoritative_semantic_decisions'])}`",
        f"- Authoritative exact boundaries: `{len(artifact['exact_boundary_provenance']['resolved_boundaries'])}`",
        f"- Governed transformation records: `{len(artifact['decisions'])}`",
        f"- Result units: `{sum(len(item['results']) for item in artifact['decisions'])}`",
        "",
        "## Original review item mapping",
        "",
        "| Item | Source Topic | Transformation | Operations | Source fragments | Result units / dispositions | Boundary decisions |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]
    for semantic in artifact["authoritative_semantic_decisions"]:
        item = by_semantic_ref[semantic["id"]]
        transformation = item["transformation"]
        source_fragments = [
            fragment
            for fragment in transformation["source_fragments"]
            if fragment["source_topic_id"] == semantic["source_topic_id"]
        ]
        fragment_text = "<br>".join(
            f"`{fragment['word_start_id'].rsplit(':', 1)[1]}–{fragment['word_end_id'].rsplit(':', 1)[1]}`"
            for fragment in source_fragments
        )
        fragment_ids = {fragment["id"] for fragment in source_fragments}
        result_text = "<br>".join(
            f"`{result['id']}` — {result['title']} (`{result['disposition']}`)"
            for result in transformation["results"]
            if fragment_ids.intersection(result["fragment_refs"])
        )
        boundary_text = "<br>".join(f"`{item}`" for item in transformation["boundary_decision_refs"]) or "unchanged"
        lines.append(
            f"| {semantic['review_item_number']} | `{semantic['source_topic_id']}` | `{transformation['id']}` | "
            f"{', '.join(transformation['operations'])} | {fragment_text} | {result_text} | {boundary_text} |"
        )
    lines.extend(["", "## Governed transformation details", ""])
    for transformation_id in sorted(transformations):
        item = transformations[transformation_id]
        transformation = item["transformation"]
        lines.extend(
            [
                f"### {transformation_id}",
                "",
                f"- Semantic authority: {', '.join(f'`{ref}`' for ref in transformation['semantic_decision_refs'])}",
                f"- Exact-boundary authority: {', '.join(f'`{ref}`' for ref in transformation['boundary_decision_refs']) or 'unchanged original boundaries'}",
                "- Results:",
                "",
            ]
        )
        fragment_by_id = {item["id"]: item for item in transformation["source_fragments"]}
        for result in transformation["results"]:
            selected = [fragment_by_id[ref] for ref in result["fragment_refs"]]
            start = selected[0]["word_start_id"]
            end = selected[-1]["word_end_id"]
            lines.append(
                f"  - `{result['id']}` — **{result['title']}** — `{result['disposition']}` — `{start}`…`{end}`"
            )
        lines.append("")
    lines.extend(["## Preserved limitations", ""])
    lines.extend(f"- {item}" for item in artifact["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists() or args.audit.exists():
        raise ValueError("output already exists")
    artifact, audit_data = build_artifact(args.project.resolve(), args.plan.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(canonical_bytes(artifact))
    args.audit.write_text(render_audit(artifact, audit_data), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "PASS",
                "semantic_decisions": len(artifact["authoritative_semantic_decisions"]),
                "boundary_decisions": len(artifact["exact_boundary_provenance"]["resolved_boundaries"]),
                "transformations": len(artifact["decisions"]),
                "fragments": sum(len(item["source_fragments"]) for item in artifact["decisions"]),
                "results": sum(len(item["results"]) for item in artifact["decisions"]),
                "output_sha256": sha256(args.output),
                "audit_sha256": sha256(args.audit),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
